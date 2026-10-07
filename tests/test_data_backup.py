import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
import zipfile
from engineering.local_app.store import Store
from engineering.local_app.files import preserve_file
from engineering.local_app.lock import DataLock


class DataBackupTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.base=Path(self.tmp.name);self.root=self.base/'original'
        self.store=Store(self.root);self.sid=self.store.create_session('Тестовый проект')['id']
        self.file=preserve_file(self.store,self.sid,'source.txt',b'original engineering source')
        self.archive=self.base/'backup.zip'

    def test_restore_relocates_original_and_preserves_history_and_key(self):
        from engineering.local_app.backup import create_backup,restore_backup
        (self.root/'engineering-verification.key').write_bytes(b'x'*32)
        (self.root/'derived').mkdir();(self.root/'derived'/'converted.docx').write_bytes(b'derived')
        create_backup(self.root,self.archive)
        target=self.base/'restored';restore_backup(self.archive,target)
        restored=Store(target)
        self.assertEqual(restored.snapshot(self.sid)['session']['title'],'Тестовый проект')
        self.assertEqual(restored.get_file(self.file['id'])['sha256'],self.file['sha256'])
        self.assertEqual(Path(restored.get_file(self.file['id'])['path']).read_bytes(),b'original engineering source')
        self.assertTrue(Path(restored.get_file(self.file['id'])['path']).is_relative_to(target))
        self.assertEqual(restored.verification_key(),b'x'*32)
        self.assertEqual((target/'derived'/'converted.docx').read_bytes(),b'derived')

    def test_running_app_and_existing_destination_are_not_overwritten(self):
        from engineering.local_app.backup import create_backup,restore_backup
        with DataLock(self.root):
            with self.assertRaises(RuntimeError):create_backup(self.root,self.archive)
        create_backup(self.root,self.archive)
        with self.assertRaises(ValueError):create_backup(self.root,self.archive)
        with self.assertRaises(ValueError):restore_backup(self.archive,self.root)
        self.assertEqual(Path(self.store.get_file(self.file['id'])['path']).read_bytes(),b'original engineering source')

    def test_failed_copy_does_not_publish_partial_archive(self):
        from engineering.local_app.backup import create_backup
        from unittest.mock import patch
        with patch('engineering.local_app.backup.zipfile.ZipFile.write',side_effect=OSError('Disk full')):
            with self.assertRaises(OSError):create_backup(self.root,self.archive)
        self.assertFalse(self.archive.exists())

    def test_legacy_migration_has_recovery_copy_and_preserves_data(self):
        with sqlite3.connect(self.store.path) as db:db.execute('PRAGMA user_version=0')
        Store(self.root)
        with sqlite3.connect(self.root/'history.pre-migration-v0.sqlite3') as db:
            self.assertEqual(db.execute('PRAGMA user_version').fetchone()[0],0)
            self.assertEqual(db.execute('SELECT title FROM sessions').fetchone()[0],'Тестовый проект')

    def test_invalid_existing_migration_copy_blocks_upgrade(self):
        with sqlite3.connect(self.store.path) as db:db.execute('PRAGMA user_version=0')
        (self.root/'history.pre-migration-v0.sqlite3').write_bytes(b'incomplete copy')
        with self.assertRaises((ValueError,sqlite3.DatabaseError)):Store(self.root)
        with sqlite3.connect(self.store.path) as db:self.assertEqual(db.execute('PRAGMA user_version').fetchone()[0],0)

    def test_failed_migration_backup_can_retry_without_partial_copy(self):
        from unittest.mock import patch
        with sqlite3.connect(self.store.path) as db:db.execute('PRAGMA user_version=0')
        connect=sqlite3.connect
        class FailingBackup(sqlite3.Connection):
            def backup(self,target,*args,**kwargs):
                target.execute('CREATE TABLE partial(id INTEGER)');target.commit()
                raise OSError('Simulated disk full')
        with patch('engineering.local_app.store.sqlite3.connect',side_effect=lambda *a,**kw:connect(*a,**dict(kw,factory=FailingBackup))):
            with self.assertRaises(OSError):Store(self.root)
        self.assertFalse((self.root/'history.pre-migration-v0.sqlite3').exists())
        self.assertEqual(list(self.root.glob('migration-*.sqlite3')),[])
        Store(self.root)
        with connect(self.root/'history.pre-migration-v0.sqlite3') as db:self.assertEqual(db.execute('PRAGMA integrity_check').fetchone()[0],'ok')

    def test_racing_empty_target_is_not_replaced(self):
        from engineering.local_app.backup import create_backup,restore_backup,_publish_directory
        from unittest.mock import patch
        import os
        create_backup(self.root,self.archive);target=self.base/'racing'
        inode=[]
        def racing(source,destination):
            destination.mkdir();inode.append(destination.stat().st_ino)
            _publish_directory(source,destination)
        with patch('engineering.local_app.backup._publish_directory',side_effect=racing):
            with self.assertRaises(OSError):restore_backup(self.archive,target)
        self.assertEqual(target.stat().st_ino,inode[0]);self.assertEqual(list(target.iterdir()),[])

    def test_migration_failure_rolls_back_schema_changes(self):
        bad=self.base/'broken';bad.mkdir();path=bad/'history.sqlite3'
        with sqlite3.connect(path) as db:db.execute('CREATE TABLE jobs(id TEXT PRIMARY KEY)')
        with self.assertRaises(sqlite3.OperationalError):Store(bad)
        with sqlite3.connect(path) as db:
            self.assertEqual(db.execute('PRAGMA user_version').fetchone()[0],0)
            self.assertIsNone(db.execute("SELECT name FROM sqlite_master WHERE name='sessions'").fetchone())

    def test_corrupt_archive_leaves_target_absent(self):
        from engineering.local_app.backup import create_backup,restore_backup
        create_backup(self.root,self.archive)
        bad=self.base/'bad.zip'
        with zipfile.ZipFile(self.archive) as source,zipfile.ZipFile(bad,'w') as dest:
            for entry in source.infolist():
                data=source.read(entry)
                dest.writestr(entry,b'corrupt' if entry.filename.startswith('files/') else data)
        target=self.base/'target'
        with self.assertRaises(ValueError):restore_backup(bad,target)
        self.assertFalse(target.exists())

    def test_traversal_is_rejected(self):
        from engineering.local_app.backup import restore_backup
        with zipfile.ZipFile(self.archive,'w') as z:z.writestr('../escape',b'unsafe')
        with self.assertRaises(ValueError):restore_backup(self.archive,self.base/'target')
        self.assertFalse((self.base/'escape').exists())

    def test_future_schema_is_not_changed(self):
        with sqlite3.connect(self.store.path) as db:db.execute('PRAGMA user_version=999')
        with self.assertRaises(RuntimeError):Store(self.root)
        with sqlite3.connect(self.store.path) as db:self.assertEqual(db.execute('PRAGMA user_version').fetchone()[0],999)

    def test_launcher_reports_corrupt_database_without_traceback(self):
        from scripts.run_local_app import main
        from contextlib import redirect_stderr
        import io
        broken=self.base/'corrupt';broken.mkdir();(broken/'history.sqlite3').write_bytes(b'not sqlite')
        output=io.StringIO()
        with redirect_stderr(output):self.assertEqual(main(['--data-dir',str(broken),'--no-browser']),2)
        self.assertIn('Cannot start',output.getvalue());self.assertNotIn('Traceback',output.getvalue())

    def test_only_nonsecret_settings_are_restored(self):
        from engineering.local_app.backup import create_backup,restore_backup
        from unittest.mock import patch
        with patch.dict('os.environ',{'ENGINEER_OS_LOCAL_MODEL':'test-model','ENGINEER_OS_LOCAL_MODEL_KEY':'secret-never-copy'}):
            create_backup(self.root,self.archive)
        target=self.base/'restored';restore_backup(self.archive,target)
        settings=json.loads((target/'settings.json').read_text())
        self.assertEqual(settings['ENGINEER_OS_LOCAL_MODEL'],'test-model')
        self.assertNotIn('ENGINEER_OS_LOCAL_MODEL_KEY',settings)
        with zipfile.ZipFile(self.archive) as z:self.assertNotIn(b'secret-never-copy',z.read('manifest.json'))


if __name__=='__main__':unittest.main()

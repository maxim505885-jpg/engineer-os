import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
import zipfile

from engineering.local_app.backup import restore_backup, verify_backup
from engineering.local_app.files import preserve_file
from engineering.local_app.store import Store


class BackupStreamCompatibilityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.store = Store(self.base/'source')
        self.sid = self.store.create_session('Legacy project')['id']
        self.file = preserve_file(self.store, self.sid, 'source.txt', b'original')

    def legacy_archive(self, *, bad_counts=False, traversal=False):
        snapshot = self.base/'snapshot.sqlite3'
        with sqlite3.connect(self.store.path) as src, sqlite3.connect(snapshot) as dst:
            src.backup(dst)
            names = [r[0] for r in dst.execute("SELECT name FROM sqlite_master WHERE type='table'")]
            counts = {name: dst.execute('SELECT count(*) FROM "'+name+'"').fetchone()[0] for name in names}
        if bad_counts:
            counts['sessions'] += 1
        data = snapshot.read_bytes()
        name = '../outside' if traversal else 'files/'+self.file['id']+'.txt'
        manifest = dict(schema='ENGINEER_OS_DATA_BACKUP_V1', database=dict(archive_path='history.sqlite3', size=len(data), sha256=hashlib.sha256(data).hexdigest(), table_counts=counts), files=[dict(id=self.file['id'], archive_path=name, size=8, sha256=self.file['sha256'])], non_secret_config={})
        archive = self.base/'legacy.zip'
        with zipfile.ZipFile(archive, 'w') as z:
            z.writestr('manifest.json', json.dumps(manifest))
            z.writestr('history.sqlite3', data)
            z.writestr(name, b'original')
        return archive

    def test_legacy_archive_restores_sources_without_minting_authority(self):
        archive = self.legacy_archive()
        self.assertEqual(verify_backup(archive)['status'], 'PASS')
        target = self.base/'restored'
        result = restore_backup(archive, target)
        self.assertEqual(result['status'], 'PASS')
        restored = Store(target)
        self.assertEqual(Path(restored.get_file(self.file['id'])['path']).read_bytes(), b'original')
        self.assertIsNone(restored.verification_key())
        self.assertFalse(result['authority_key_preserved'])

    def test_legacy_bad_counts_block_before_publication(self):
        archive = self.legacy_archive(bad_counts=True)
        target = self.base/'never'
        with self.assertRaises(ValueError):
            restore_backup(archive, target)
        self.assertFalse(target.exists())

    def test_legacy_unsafe_member_blocks_before_publication(self):
        archive = self.legacy_archive(traversal=True)
        target = self.base/'never'
        with self.assertRaises(ValueError):
            restore_backup(archive, target)
        self.assertFalse(target.exists())

"""Owner-selected roots must not redirect managed leaves outside that root."""
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest

from engineering.local_app.backup import create_backup, restore_backup
from engineering.local_app.lock import DataLock
from engineering.local_app.settings import activate, active_directory, load
from engineering.local_app.store import Store


class RecoveryPathSecurityTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.base=Path(self.tmp.name);self.root=self.base/'selected';self.root.mkdir()

    def link(self,source,target,kind):
        try:
            if kind=='hard':os.link(source,target)
            else:target.symlink_to(source)
        except (OSError,NotImplementedError):self.skipTest('Links unavailable on this platform')

    def test_linked_database_is_rejected_without_modifying_external_database(self):
        for kind in ('symbolic','hard'):
            with self.subTest(kind=kind):
                external=self.base/(kind+'.sqlite3')
                with sqlite3.connect(external) as db:db.execute('PRAGMA user_version=1')
                before=external.read_bytes();path=self.root/'history.sqlite3'
                self.link(external,path,kind)
                try:
                    with self.assertRaises(ValueError):Store(self.root)
                    self.assertEqual(external.read_bytes(),before)
                finally:path.unlink()

    def test_broken_database_link_is_rejected_without_creating_external_file(self):
        external=self.base/'missing.sqlite3';self.link(external,self.root/'history.sqlite3','symbolic')
        with self.assertRaises(ValueError):Store(self.root)
        self.assertFalse(external.exists())

    def test_linked_lock_is_rejected_without_writing_external_file(self):
        for kind in ('symbolic','hard'):
            with self.subTest(kind=kind):
                external=self.base/(kind+'-empty');external.touch();path=self.root/'app.lock'
                self.link(external,path,kind)
                try:
                    with self.assertRaises(ValueError):
                        with DataLock(self.root):pass
                    self.assertEqual(external.read_bytes(),b'')
                finally:path.unlink()

    def test_broken_lock_is_rejected_without_creating_external_file(self):
        external=self.base/'missing-lock';self.link(external,self.root/'app.lock','symbolic')
        with self.assertRaises(ValueError):
            with DataLock(self.root):pass
        self.assertFalse(external.exists())

    def test_hardlinked_settings_are_rejected(self):
        Store(self.root)
        settings=self.base/'external-settings';settings.write_text('{}')
        self.link(settings,self.root/'settings.json','hard')
        with self.assertRaises(ValueError):load(self.root)

    def test_hardlinked_issuer_key_is_rejected_and_never_archived(self):
        store=Store(self.root)
        key=self.base/'external-key';key.write_bytes(b'x'*32)
        self.link(key,self.root/'engineering-verification.key','hard')
        self.assertIsNone(store.verification_key())
        with self.assertRaises(ValueError):create_backup(self.root,self.base/'copy.zip')

    def test_database_sidecar_link_is_rejected_before_sqlite_open(self):
        store=Store(self.root)
        external=self.base/'external-sidecar';external.write_bytes(b'keep')
        self.link(external,self.root/'history.sqlite3-wal','symbolic')
        with self.assertRaises(ValueError):
            with store.connection():pass
        self.assertEqual(external.read_bytes(),b'keep')

    def test_backup_parent_alias_cannot_put_archive_inside_managed_data(self):
        Store(self.root);alias=self.base/'alias'
        try:alias.symlink_to(self.root,target_is_directory=True)
        except (OSError,NotImplementedError):self.skipTest('Directory links unavailable')
        with self.assertRaises(ValueError):create_backup(self.root,alias/'copy.zip')
        self.assertFalse((self.root/'copy.zip').exists())

    def test_activation_rejects_linked_database_and_keeps_selection(self):
        Store(self.base/'external')
        external=self.base/'external'/'history.sqlite3'
        self.link(external,self.root/'history.sqlite3','symbolic')
        selection=self.base/'selection';selection.write_text('keep')
        with self.assertRaises(ValueError):activate(self.root,selection)
        self.assertEqual(selection.read_text(),'keep')

    def test_broken_active_selection_fails_closed(self):
        selection=self.base/'selection';self.link(self.base/'missing-selection',selection,'symbolic')
        with self.assertRaises(ValueError):active_directory(selection,self.root)

    def test_owner_directory_aliases_still_allow_backup_restore_and_selection(self):
        alias=self.base/'owner alias'
        try:alias.symlink_to(self.root,target_is_directory=True)
        except (OSError,NotImplementedError):self.skipTest('Directory links unavailable')
        store=Store(alias);sid=store.create_session('Owner project')['id']
        key=self.root/'engineering-verification.key';key.write_bytes(b'x'*32)
        archive=self.base/'copy.zip';create_backup(alias,archive)
        restored=self.base/'restored';restore_backup(archive,restored)
        self.assertEqual(Store(restored).snapshot(sid)['session']['title'],'Owner project')
        self.assertEqual(Store(restored).verification_key(),b'x'*32)
        selection=self.base/'selection'
        self.assertEqual(activate(alias,selection),self.root.resolve())
        self.assertEqual(active_directory(selection,self.base/'fallback'),self.root.resolve())

    def test_broken_migration_copy_link_blocks_before_creating_external_file(self):
        store=Store(self.root)
        with store.connection() as db:db.execute('PRAGMA user_version=0')
        external=self.base/'missing-copy'
        self.link(external,self.root/'history.pre-migration-v0.sqlite3','symbolic')
        with self.assertRaises(ValueError):Store(self.root)
        self.assertFalse(external.exists())
        with store.connection() as db:self.assertEqual(db.execute('PRAGMA user_version').fetchone()[0],0)


if __name__=='__main__':unittest.main()

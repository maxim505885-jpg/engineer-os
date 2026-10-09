"""Windows metadata fallback must retain the managed-leaf trust boundary."""
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from engineering.local_app.lock import _windows_shared_stat,managed_file


@unittest.skipUnless(os.name=='nt','Native Windows handle semantics')
class WindowsSharedStatTests(unittest.TestCase):
    def test_live_sqlite_shm_has_authoritative_single_link_metadata(self):
        with tempfile.TemporaryDirectory() as folder:
            db=sqlite3.connect(Path(folder)/'data.sqlite3')
            try:
                db.execute('PRAGMA journal_mode=WAL');db.execute('CREATE TABLE sample(value)');db.commit()
                path=Path(str(Path(folder)/'data.sqlite3')+'-shm')
                self.assertTrue(path.exists())
                self.assertEqual(_windows_shared_stat(path).st_nlink,1)
                unknown=os.stat_result((path.stat().st_mode,0,0,0,0,0,0,0,0,0))
                with patch.object(Path,'lstat',return_value=unknown):self.assertEqual(managed_file(path).st_nlink,1)
            finally:db.close()

    def test_unknown_path_metadata_cannot_admit_hardlinked_leaf(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'internal';path.write_bytes(b'original');os.link(path,Path(folder)/'alias')
            unknown=os.stat_result((path.stat().st_mode,0,0,0,0,0,0,0,0,0))
            with patch.object(Path,'lstat',return_value=unknown):
                with self.assertRaises(ValueError):managed_file(path)

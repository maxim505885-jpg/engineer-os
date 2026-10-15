import contextlib
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from engineering.local_app.files import preserve_file
from engineering.local_app.store import Store
from scripts import backup_engineer_os_data as launcher


class BackupLauncherSelectionTests(unittest.TestCase):
    def test_backup_uses_selected_data_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'app';root.mkdir()
            data=Path(tmp)/'selected';store=Store(data)
            sid=store.create_session('Selected project')['id']
            preserve_file(store,sid,'source.txt',b'selected original')
            config=root/'.engineer-os';config.mkdir()
            (config/'active-data-dir.txt').write_text(str(data)+'\n')
            with patch.object(launcher,'ROOT',root),patch.object(Path,'home',return_value=Path(tmp)),contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(launcher.main(),0)
            self.assertEqual(len(list((Path(tmp)/'Documents'/'ENGINEER_OS_DATA_BACKUPS').glob('*.zip'))),1)

    def test_invalid_selection_does_not_backup_a_different_project(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'app';root.mkdir()
            config=root/'.engineer-os';config.mkdir()
            Store(config/'local-app')
            (config/'active-data-dir.txt').write_text(str(Path(tmp)/'missing')+'\n')
            with patch.object(launcher,'ROOT',root),patch.object(Path,'home',return_value=Path(tmp)),contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(launcher.main(),2)
            self.assertEqual(list((Path(tmp)/'Documents'/'ENGINEER_OS_DATA_BACKUPS').glob('*.zip')),[])

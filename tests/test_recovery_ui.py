"""Actual loopback recovery API preserves offline locks and new-target restore."""
import json
import tempfile
import threading
import unittest
from pathlib import Path
from http.client import HTTPConnection
from types import SimpleNamespace
from engineering.local_app.server import make_server
from engineering.local_app.store import Store
from engineering.local_app.files import preserve_file
from engineering.local_app.lock import DataLock


class RecoveryUITests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.base=Path(self.tmp.name).resolve();self.root=self.base/'data';self.store=Store(self.root)
        self.sid=self.store.create_session('Restore project')['id']
        self.file=preserve_file(self.store,self.sid,'Original.md','Original height 4m'.encode())
        self.store.enqueue(self.sid,'Saved history',[])
        self.selection=self.base/'active-data-dir.txt'
        self.server=make_server(SimpleNamespace(root=self.root),None,recovery_only=True,drive_client=None,selection_path=self.selection)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start();self.addCleanup(self.close)
        self.origin=self.server.origin

    def close(self):
        self.server.shutdown();self.server.server_close();self.thread.join()

    def request(self,path,body=None,*,token=True,origin=None):
        conn=HTTPConnection('127.0.0.1',self.server.server_port,timeout=10)
        headers={'Origin':origin or self.origin}
        if token:headers['X-Engineer-Token']=self.server.token
        raw=json.dumps(body).encode() if body is not None else None
        if raw is not None:headers['Content-Type']='application/json'
        try:
            conn.request('POST' if body is not None else 'GET',path,raw,headers)
            r=conn.getresponse();return r.status,r.read()
        finally:conn.close()

    def test_browser_backup_verify_restore_preserves_original_history_and_queue(self):
        archive=self.base/'copy.zip';target=self.base/'new-project'
        self.assertEqual(self.request('/api/data/backup',{'archive':str(archive)})[0],200)
        self.assertEqual(self.request('/api/data/verify',{'archive':str(archive)})[0],200)
        status,raw=self.request('/api/data/restore',{'archive':str(archive),'target':str(target)})
        self.assertEqual(status,200,raw)
        restored=Store(target).snapshot(self.sid)
        self.assertEqual(restored['files'][0]['sha256'],self.file['sha256'])
        self.assertEqual(restored['messages'][0]['content'],'Saved history')
        self.assertEqual(restored['jobs'][0]['state'],'QUEUED')
        self.assertEqual(self.request('/api/data/restore',{'archive':str(archive),'target':str(target)})[0],400)

    def test_active_owner_and_untrusted_requests_cannot_backup(self):
        archive=self.base/'copy.zip'
        self.assertEqual(self.request('/api/data/backup',{'archive':str(archive)},token=False)[0],403)
        self.assertEqual(self.request('/api/data/backup',{'archive':str(archive)},origin='https://example.com')[0],403)
        with DataLock(self.root):
            self.assertEqual(self.request('/api/data/backup',{'archive':str(archive)})[0],409)
        self.assertFalse(archive.exists())

    def test_recovery_mode_has_no_chat_or_model_and_rejects_relative_paths(self):
        self.assertEqual(self.request('/api/sessions',{'title':'Forbidden'})[0],409)
        self.assertEqual(self.request('/api/data/backup',{'archive':'relative.zip'})[0],400)
        self.assertEqual(self.request('/api/data/restore',{'archive':str(self.base/'missing.zip'),'target':'relative'})[0],400)
        status,raw=self.request('/api/data/status');self.assertEqual(status,200)
        self.assertTrue(json.loads(raw)['recovery_only'])
        self.assertIn('Резервные копии'.encode(),self.request('/')[1])

    def test_activation_requires_an_existing_idle_project_and_preserves_original_root(self):
        from engineering.local_app.settings import activate,active_directory
        selection=self.base/'active-data-dir.txt'
        with self.assertRaises(ValueError):activate(self.base/'missing',selection)
        with DataLock(self.root):
            with self.assertRaises(RuntimeError):activate(self.root,selection)
        activate(self.root,selection)
        self.assertEqual(active_directory(selection,self.base/'fallback'),self.root)
        self.assertEqual(self.store.snapshot(self.sid)['messages'][0]['content'],'Saved history')

    def test_activation_http_selects_only_valid_idle_data(self):
        self.assertEqual(self.request('/api/data/activate',{'target':str(self.base/'absent')})[0],400)
        self.assertFalse(self.selection.exists())
        with DataLock(self.root):self.assertEqual(self.request('/api/data/activate',{'target':str(self.root)})[0],409)
        self.assertFalse(self.selection.exists())
        self.assertEqual(self.request('/api/data/activate',{'target':str(self.root)})[0],200)
        self.assertEqual(self.selection.read_text().strip(),str(self.root))
        self.assertEqual(self.request('/api/data/activate',{'target':str(self.base/'absent')})[0],400)
        self.assertEqual(self.selection.read_text().strip(),str(self.root))

    def test_concurrent_operation_does_not_start_a_second_copy(self):
        self.server.data_slots.acquire()
        try:self.assertEqual(self.request('/api/data/backup',{'archive':str(self.base/'copy.zip')})[0],409)
        finally:self.server.data_slots.release()
        self.assertFalse((self.base/'copy.zip').exists())

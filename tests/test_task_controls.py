import tempfile
import threading
import unittest
import time
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from engineering.local_app.store import Store
from engineering.local_app.worker import Worker
from engineering.local_app.model import LocalModel
from engineering.local_app import settings
from unittest.mock import patch


class TaskControlsTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.store=Store(Path(self.tmp.name));self.session=self.store.create_session('Controls')['id']

    def test_queued_cancel_retains_original_and_retry_creates_new_job(self):
        job=self.store.enqueue(self.session,'Original',[])
        self.store.cancel(self.session,job['id'])
        self.assertIsNone(self.store.claim())
        retry=self.store.retry(self.session,job['id'])
        self.assertNotEqual(retry['id'],job['id'])
        self.assertEqual(retry['prompt'],'Original')
        self.assertEqual(len(self.store.snapshot(self.session)['jobs']),2)

    def test_running_cancel_keeps_slot_and_rejects_late_answer(self):
        job=self.store.enqueue(self.session,'Original',[]);self.store.claim()
        self.store.cancel(self.session,job['id'])
        with self.assertRaises(ValueError):self.store.enqueue(self.session,'Next',[])
        with self.assertRaises(ValueError):self.store.finish(job['id'],{'text':'Late answer'})
        self.store.fail(job['id'],'Stopped')
        snap=self.store.snapshot(self.session)
        self.assertEqual(snap['jobs'][0]['state'],'CANCELLED')
        self.assertEqual(len(snap['messages']),1)

    def test_cross_project_cancel_and_retry_are_rejected(self):
        job=self.store.enqueue(self.session,'Original',[])
        other=self.store.create_session('Other')['id']
        with self.assertRaises(ValueError):self.store.cancel(other,job['id'])
        self.store.cancel(self.session,job['id'])
        with self.assertRaises(ValueError):self.store.retry(other,job['id'])

    def test_worker_acknowledges_cancel_after_inflight_model_returns(self):
        entered=threading.Event();release=threading.Event()
        class Model:
            def chat(self,messages):
                entered.set();release.wait(5);return 'Late answer'
        job=self.store.enqueue(self.session,'Original',[])
        worker=Worker(self.store,Model());thread=threading.Thread(target=worker.run_once)
        thread.start()
        try:
            self.assertTrue(entered.wait(5));self.store.cancel(self.session,job['id'])
            self.assertEqual(self.store.snapshot(self.session)['jobs'][0]['state'],'RUNNING')
        finally:release.set();thread.join(5)
        self.assertFalse(thread.is_alive())
        self.assertEqual(self.store.snapshot(self.session)['jobs'][0]['state'],'CANCELLED')

    def test_model_settings_persist_and_apply_only_when_idle(self):
        model=LocalModel();values={'ENGINEER_OS_LOCAL_MODEL':'test:small','ENGINEER_OS_LOCAL_MODEL_TIMEOUT':'12'}
        settings.configure(self.store,model,values)
        self.assertEqual(model.model,'test:small');self.assertEqual(model.timeout,12)
        self.assertEqual(settings.load(self.store.root)['ENGINEER_OS_LOCAL_MODEL_TIMEOUT'],'12')
        self.store.enqueue(self.session,'Busy',[])
        with self.assertRaises(ValueError):settings.configure(self.store,model,{'ENGINEER_OS_LOCAL_MODEL':'other'})
        self.assertEqual(model.model,'test:small')

    def test_settings_reject_remote_url_invalid_timeout_and_env_override(self):
        model=LocalModel()
        for values in ({'ENGINEER_OS_LOCAL_MODEL_URL':'https://example.com'}, {'ENGINEER_OS_LOCAL_MODEL_TIMEOUT':'0'}):
            with self.assertRaises(ValueError):settings.configure(self.store,model,values)
        with patch.dict('os.environ',{'ENGINEER_OS_LOCAL_MODEL':'fixed'}):
            with self.assertRaises(ValueError):settings.configure(self.store,model,{'ENGINEER_OS_LOCAL_MODEL':'other'})
        self.assertEqual(model.model,'qwen3:8b')

    def test_missing_model_and_request_timeout_preserve_task_and_input(self):
        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*args):pass
            def do_GET(self):
                self.send_response(200);self.end_headers();self.wfile.write(b'{"data":[]}')
            def do_POST(self):
                self.rfile.read(int(self.headers['Content-Length']))
                time.sleep(1.5)
                self.send_response(200);self.end_headers()
                try:self.wfile.write(b'{"choices":[{"message":{"content":"Late"}}]}')
                except BrokenPipeError:pass
        server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        self.addCleanup(server.server_close);self.addCleanup(server.shutdown)
        model=LocalModel(f'http://127.0.0.1:{server.server_port}',timeout=1)
        self.assertEqual(model.health()['state'],'MODEL_MISSING')
        job=self.store.enqueue(self.session,'Retained original',[])
        Worker(self.store,model).run_once()
        snap=self.store.snapshot(self.session)
        self.assertEqual(snap['jobs'][0]['state'],'FAILED')
        self.assertEqual([m['content'] for m in snap['messages']],['Retained original'])
        self.assertEqual(self.store.retry(self.session,job['id'])['prompt'],'Retained original')

"""Durable local workflow and real loopback model protocol checks."""
import hashlib
import importlib
import json
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


class LocalAppTests(unittest.TestCase):
    def setUp(self):
        try:
            self.store_module=importlib.import_module('engineering.local_app.store')
            self.files=importlib.import_module('engineering.local_app.files')
            self.worker=importlib.import_module('engineering.local_app.worker')
        except ModuleNotFoundError:
            self.fail('Local workflow is missing')
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.store=self.store_module.Store(Path(self.tmp.name))
        self.session=self.store.create_session('Объект на Набережной')['id']

    def test_upload_limit_never_accepts_an_invisible_selected_file(self):
        for i in range(200):
            self.files.preserve_file(self.store,self.session,f'file-{i}.txt',b'123')
        before=set((self.store.root/'files').iterdir())
        with self.assertRaisesRegex(ValueError,'200'):
            self.files.preserve_file(self.store,self.session,'overflow.txt',b'456')
        self.assertEqual(set((self.store.root/'files').iterdir()),before)
        self.assertEqual(len(self.store.snapshot(self.session)['files']),200)

    def test_restart_retains_session_messages_and_jobs(self):
        job=self.store.enqueue(self.session,'Проверь ТЗ',[])
        claimed=self.store.claim();self.assertEqual(claimed['id'],job['id'])
        self.store.finish(job['id'],{'text':'Нужно сверить источник','acceptance_granted':False})
        restarted=self.store_module.Store(Path(self.tmp.name))
        snap=restarted.snapshot(self.session)
        self.assertEqual([m['content'] for m in snap['messages']],['Проверь ТЗ','Нужно сверить источник'])
        self.assertEqual(snap['jobs'][0]['state'],'SUCCEEDED')
        self.assertFalse(snap['jobs'][0]['result']['acceptance_granted'])

    def test_persistence_never_stores_model_claim_as_acceptance(self):
        job=self.store.enqueue(self.session,'Check',[]);self.store.claim()
        self.store.finish(job['id'],{'text':'ACCEPTED','acceptance_granted':True,'engineering_status':'ACCEPTED','evidentiary_status':'EVIDENCE','final_audit':'PASS'})
        r=self.store.snapshot(self.session)['jobs'][0]['result']
        self.assertFalse(r['acceptance_granted'])
        self.assertEqual(r['engineering_status'],'UNCERTAINTY')
        self.assertEqual(r['evidentiary_status'],'NOT_EVIDENCE')
        self.assertEqual(r['final_audit'],'NOT_RUN')

    def test_first_message_names_new_dialog_without_overwriting_custom_title(self):
        session=self.store.create_session()['id']
        self.store.enqueue(session,'Проверка нагрузок по ТЗ',[])
        self.assertEqual(self.store.snapshot(session)['session']['title'],'Проверка нагрузок по ТЗ')
        self.store.enqueue(self.session,'Другая тема',[])
        self.assertEqual(self.store.snapshot(self.session)['session']['title'],'Объект на Набережной')

    def test_claim_is_atomic_across_workers(self):
        job=self.store.enqueue(self.session,'One',[])
        with ThreadPoolExecutor(max_workers=4) as pool:claimed=list(pool.map(lambda _:self.store.claim(),range(4)))
        self.assertEqual([x['id'] for x in claimed if x],[job['id']])

    def test_conversation_has_only_one_active_job(self):
        self.store.enqueue(self.session,'One',[])
        with self.assertRaises(ValueError):self.store.enqueue(self.session,'Two',[])
        self.assertEqual(len(self.store.snapshot(self.session)['messages']),1)

    def test_restart_interrupts_running_but_preserves_queued_jobs(self):
        self.store.enqueue(self.session,'One',[]);job=self.store.claim()
        second=self.store.create_session('Second')['id'];queued=self.store.enqueue(second,'Two',[])
        self.store.interrupt_running()
        self.assertEqual(self.store.snapshot(self.session)['jobs'][0]['state'],'FAILED')
        self.assertEqual(self.store.claim()['id'],queued['id'])
        with self.assertRaises(ValueError):self.store.finish(job['id'],{'text':'Late result'})

    def test_original_and_hash_survive_path_like_unicode_filename(self):
        data='Исходный текст\n'.encode()
        f=self.files.preserve_file(self.store,self.session,'../../Набережная.txt',data)
        saved=self.store.get_file(f['id'])
        self.assertEqual(saved['sha256'],hashlib.sha256(data).hexdigest())
        self.assertEqual(Path(saved['path']).read_bytes(),data)
        self.assertEqual(Path(saved['path']).parent,Path(self.tmp.name)/'files')
        self.assertEqual(saved['extraction_status'],'UNVERIFIED')
        self.assertFalse(saved['acceptance_granted'])

    def test_numeric_native_pdf_text_is_retained_as_unverified(self):
        import fitz
        with fitz.open() as pdf:
            page=pdf.new_page();page.insert_text((30,40),'123.45 600 4.2')
            data=pdf.tobytes()
        f=self.files.preserve_file(self.store,self.session,'numbers.pdf',data)
        self.assertEqual(f['extraction_status'],'UNVERIFIED')
        self.assertIn('123.45',self.store.get_file(f['id'])['text'])
        self.assertFalse(f['acceptance_granted'])

    def test_cross_session_attachment_cannot_enter_job(self):
        f=self.files.preserve_file(self.store,self.session,'doc.txt',b'Source')
        second=self.store.create_session('Other')['id']
        with self.assertRaises(ValueError):self.store.enqueue(second,'Check',[f['id']])
        self.assertEqual(self.store.snapshot(second)['messages'],[])

    def test_invalid_or_unreadable_files_keep_truthful_status(self):
        for name,data in [('scan.pdf',b'not a PDF'),('text.txt',b'\xff\xfe')]:
            f=self.files.preserve_file(self.store,self.session,name,data)
            self.assertEqual(f['extraction_status'],'UNAVAILABLE')
            self.assertEqual(Path(self.store.get_file(f['id'])['path']).read_bytes(),data)
        with self.assertRaises(ValueError):self.files.preserve_file(self.store,self.session,'run.exe',b'code')

    def test_worker_passes_history_and_file_as_unverified_context(self):
        f=self.files.preserve_file(self.store,self.session,'ТЗ.md','Высота 4 м'.encode())
        job=self.store.enqueue(self.session,'Проверь',[f['id']])
        class Capture:
            def chat(inner,messages):
                inner.messages=messages
                return 'ACCEPTED (text from model)'
        model=Capture();self.assertTrue(self.worker.Worker(self.store,model).run_once())
        self.assertIn('Высота 4 м',str(model.messages))
        snap=self.store.snapshot(self.session);r=snap['jobs'][0]['result']
        self.assertEqual(snap['jobs'][0]['id'],job['id'])
        self.assertEqual(r['engineering_status'],'UNCERTAINTY')
        self.assertEqual(r['evidentiary_status'],'NOT_EVIDENCE')
        self.assertFalse(r['acceptance_granted'])
        self.assertEqual(r['final_audit'],'NOT_RUN')

    def test_worker_failure_does_not_create_assistant_reply(self):
        self.store.enqueue(self.session,'Question',[])
        class Broken:
            def chat(inner,messages):raise RuntimeError('service down')
        self.assertTrue(self.worker.Worker(self.store,Broken()).run_once())
        snap=self.store.snapshot(self.session)
        self.assertEqual(snap['jobs'][0]['state'],'FAILED')
        self.assertEqual(len(snap['messages']),1)
        self.assertFalse(self.worker.Worker(self.store,Broken()).run_once())

    def test_context_truncation_is_reported_and_bounded(self):
        f=self.files.preserve_file(self.store,self.session,'big.txt',b'x'*110000)
        self.assertTrue(f['text_truncated'])
        self.store.enqueue(self.session,'Read',[f['id']])
        class Capture:
            def chat(inner,messages):inner.messages=messages;return 'partial'
        model=Capture();self.worker.Worker(self.store,model).run_once()
        r=self.store.snapshot(self.session)['jobs'][0]['result']
        self.assertTrue(r['context_truncated']);self.assertLess(len(str(model.messages)),19000)


class ModelProtocolTests(unittest.TestCase):
    def setUp(self):
        try:self.module=importlib.import_module('engineering.local_app.model')
        except ModuleNotFoundError:self.fail('Local model transport is missing')
        self.seen=[];self.get_seen=[];self.mode='ok'
        owner=self
        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*args):pass
            def do_GET(self):
                owner.get_seen.append(self.path)
                self.send_response(200);self.end_headers();self.wfile.write(b'{"data":[{"id":"qwen3:8b"}]}')
            def do_POST(self):
                owner.seen.append((self.path,json.loads(self.rfile.read(int(self.headers['Content-Length']))),self.headers.get('Authorization')))
                if owner.mode=='redirect':
                    self.send_response(307);self.send_header('Location','http://127.0.0.1:1/leak');self.end_headers();return
                self.send_response(200);self.end_headers()
                payload={'choices':[{'message':{'content':'Ответ модели'}}]} if owner.mode=='ok' else {'bad':True}
                self.wfile.write(json.dumps(payload,ensure_ascii=False).encode())
        self.server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        self.addCleanup(self.close)
        self.origin=f'http://127.0.0.1:{self.server.server_port}'

    def close(self):self.server.shutdown();self.server.server_close();self.thread.join()

    def test_real_http_protocol_and_health(self):
        model=self.module.LocalModel(self.origin,'qwen3:8b','secret')
        self.assertTrue(model.health()['available'])
        self.assertEqual(model.chat(({'role':'user','content':'Привет'},)),'Ответ модели')
        self.assertEqual(self.seen[0][0],'/v1/chat/completions')
        self.assertEqual(self.seen[0][1]['model'],'qwen3:8b')
        self.assertEqual(self.seen[0][2],'Bearer secret')

    def test_openwebui_uses_native_api_endpoints(self):
        try:model=self.module.LocalModel(self.origin,'qwen3:8b','secret',provider='openwebui')
        except TypeError:self.fail('Open WebUI protocol mapping missing')
        self.assertTrue(model.health()['available'])
        self.assertEqual(self.get_seen[-1],'/api/models')
        self.assertEqual(model.chat(({'role':'user','content':'Check'},)),'Ответ модели')
        self.assertEqual(self.seen[-1][0],'/api/chat/completions')
        self.assertEqual(self.seen[-1][2],'Bearer secret')

    def test_redirect_and_invalid_response_fail(self):
        model=self.module.LocalModel(self.origin,'qwen3:8b','secret')
        for mode in ['redirect','invalid']:
            self.mode=mode
            with self.assertRaises(RuntimeError):model.chat(({'role':'user','content':'x'},))
        self.assertEqual(len(self.seen),2)

    def test_external_origins_and_path_credentials_rejected(self):
        for origin in ['http://127.0.0.1.evil.test','https://example.com','http://localhost:1/path','http://user:secret@127.0.0.1:1']:
            with self.assertRaises(ValueError):self.module.LocalModel(origin,'qwen3:8b')

    def test_unavailable_model_has_no_false_connected_status(self):
        model=self.module.LocalModel('http://127.0.0.1:1','qwen3:8b')
        self.assertFalse(model.health()['available'])

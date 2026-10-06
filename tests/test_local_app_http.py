"""Actual HTTP workflow, restart lock and loopback browser boundary."""
import importlib
import json
import tempfile
import threading
import time
import unittest
from http.client import HTTPConnection
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from urllib.parse import quote


class LocalHTTPTests(unittest.TestCase):
    def setUp(self):
        try:self.module=importlib.import_module('engineering.local_app.server')
        except ModuleNotFoundError:self.fail('Local HTTP application is missing')
        from engineering.local_app.store import Store
        from engineering.local_app.model import LocalModel
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.store=Store(Path(self.tmp.name))
        self.requests=[];owner=self
        class ModelHandler(BaseHTTPRequestHandler):
            def log_message(self,*args):pass
            def do_GET(self):
                self.send_response(200);self.end_headers();self.wfile.write(b'{"data":[{"id":"qwen3:8b"}]}')
            def do_POST(self):
                owner.requests.append(json.loads(self.rfile.read(int(self.headers['Content-Length']))))
                self.send_response(200);self.end_headers();self.wfile.write(json.dumps({'choices':[{'message':{'content':'Нужна проверка источника'}}]},ensure_ascii=False).encode())
        self.fake=ThreadingHTTPServer(('127.0.0.1',0),ModelHandler)
        self.fake_thread=threading.Thread(target=self.fake.serve_forever,daemon=True);self.fake_thread.start()
        self.model=LocalModel(f'http://127.0.0.1:{self.fake.server_port}','qwen3:8b')
        self.server=self.module.make_server(self.store,self.model,port=0)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start();self.addCleanup(self.close)
        self.origin=f'http://127.0.0.1:{self.server.server_port}'

    def close(self):
        self.server.shutdown();self.server.server_close();self.thread.join()
        self.fake.shutdown();self.fake.server_close();self.fake_thread.join()

    def request(self,method,path,body=None,headers=None,token=True):
        h={'Origin':self.origin}
        if token:h['X-Engineer-Token']=self.server.token
        if isinstance(body,dict):body=json.dumps(body,ensure_ascii=False).encode();h['Content-Type']='application/json'
        h.update(headers or {})
        c=HTTPConnection('127.0.0.1',self.server.server_port,timeout=3)
        try:
            c.request(method,path,body=body,headers=h);r=c.getresponse();return r.status,dict(r.headers),r.read()
        finally:c.close()

    def create(self):
        status,_,raw=self.request('POST','/api/sessions',{'title':'Объект'})
        self.assertEqual(status,201);return json.loads(raw)['id']

    def test_real_upload_queue_model_and_history(self):
        from engineering.local_app.worker import Worker
        session=self.create();source='ТЗ: высота 4 м'.encode()
        status,_,body=self.request('POST',f'/api/sessions/{session}/files?name='+quote('ТЗ.md'),source,{'Content-Type':'application/octet-stream'})
        self.assertEqual(status,201);f=json.loads(body)
        self.assertEqual(self.request('GET','/api/files/'+f['id'])[2],source)
        status,_,body=self.request('POST',f'/api/sessions/{session}/jobs',{'prompt':'Проверь','file_ids':[f['id']]})
        self.assertEqual(status,202)
        worker=Worker(self.store,self.model);worker.run_once()
        status,_,body=self.request('GET',f'/api/sessions/{session}');snap=json.loads(body)
        self.assertEqual(status,200);self.assertEqual(len(snap['messages']),2)
        self.assertEqual(snap['jobs'][0]['state'],'SUCCEEDED')
        self.assertFalse(snap['jobs'][0]['result']['acceptance_granted'])
        self.assertIn('высота 4 м',str(self.requests[0]))
        restarted=type(self.store)(Path(self.tmp.name))
        self.assertEqual(restarted.snapshot(session)['messages'][-1]['content'],'Нужна проверка источника')

    def test_core_preparation_through_http_queue_and_worker(self):
        from engineering.local_app.worker import Worker
        session=self.create()
        status,_,body=self.request('POST',f'/api/sessions/{session}/files?name=r.txt',b'123',{'Content-Type':'application/octet-stream'})
        f=json.loads(body);self.assertEqual(status,201)
        status,_,_=self.request('POST',f'/api/sessions/{session}/jobs',{'prompt':'ТЗ: проверка отчёта','file_ids':[f['id']],'mode':'CORE_PLAN'})
        self.assertEqual(status,202);Worker(self.store,self.model).run_once()
        j=json.loads(self.request('GET',f'/api/sessions/{session}')[2])['jobs'][0]
        self.assertEqual(j['state'],'SUCCEEDED');self.assertEqual(j['result']['core_plan']['status'],'UNCERTAINTY')
        self.assertEqual(self.requests,[])
        for mode in ([],{},None,3):
            self.assertEqual(self.request('POST',f'/api/sessions/{session}/jobs',{'prompt':'Invalid','file_ids':[f['id']],'mode':mode})[0],400)
        self.assertEqual(self.request('POST',f'/api/sessions/{session}/jobs',{'prompt':'Invalid','file_ids':[f['id']],'mode':'SHELL'})[0],400)

    def test_candidate_api_preserves_source_binding_and_rejects_forgery(self):
        session=self.create()
        _,_,raw=self.request('POST',f'/api/sessions/{session}/files?name=r.txt',b'height 4m',{'Content-Type':'application/octet-stream'})
        f=json.loads(raw);payload=dict(file_id=f['id'],quote='height 4m',statement='According to original',status='ACCEPTED',acceptance_granted=True)
        path=f'/api/sessions/{session}/evidence'
        self.assertEqual(self.request('POST',path,payload,token=False)[0],403)
        status,_,raw=self.request('POST',path,payload);r=json.loads(raw)
        self.assertEqual(status,201);self.assertEqual(r['status'],'UNVERIFIED');self.assertFalse(r['acceptance_granted'])
        self.assertEqual(self.request('POST',path,dict(payload,quote='height 99m'))[0],400)
        self.assertEqual(len(json.loads(self.request('GET',f'/api/sessions/{session}')[2])['evidence']),1)

    def test_html_bootstrap_and_api_require_token(self):
        status,h,body=self.request('GET','/',token=False)
        self.assertEqual(status,200);self.assertIn(self.server.token.encode(),body)
        self.assertIn("default-src 'self'",h['Content-Security-Policy'])
        self.assertEqual(self.request('GET','/api/sessions',token=False)[0],403)
        self.assertEqual(self.request('POST','/api/sessions',{'title':'No'},token=False)[0],403)

    def test_noncanonical_request_target_cannot_bypass_token(self):
        session=self.create()
        for target in [f'api/sessions/{session}/jobs',f'//api/sessions/{session}/jobs']:
            status,_,_=self.request('POST',target,{'prompt':'Unauthorized','file_ids':[]},token=False)
            self.assertIn(status,(400,403))
        self.assertEqual(self.store.snapshot(session)['jobs'],[])

    def test_cross_origin_host_and_fetch_site_rejected(self):
        for headers in [{'Origin':'https://evil.test'},{'Host':'evil.test'},{'Sec-Fetch-Site':'cross-site'},{'Origin':'null'}]:
            self.assertEqual(self.request('POST','/api/sessions',{'title':'No'},headers)[0],403)
        self.assertEqual(self.store.sessions(),[])
        self.assertEqual(self.request('GET','/',headers={'Host':'evil.test'},token=False)[0],403)

    def test_invalid_json_size_and_unknown_session_are_visible(self):
        self.assertEqual(self.request('POST','/api/sessions',b'{bad',{'Content-Type':'application/json'})[0],400)
        self.assertEqual(self.request('POST','/api/sessions',b'',{'Content-Type':'application/json','Content-Length':'999999999'})[0],413)
        self.assertEqual(self.request('GET','/api/sessions/not-an-id')[0],400)
        self.assertEqual(self.request('GET','/missing')[0],404)

    def test_bind_to_lan_is_not_allowed(self):
        with self.assertRaises(ValueError):self.module.make_server(self.store,self.model,host='0.0.0.0',port=0)

    def test_download_of_markup_file_cannot_render_as_html(self):
        session=self.create()
        status,_,body=self.request('POST',f'/api/sessions/{session}/files?name=attack.md',b'<script>alert(1)</script>',{'Content-Type':'application/octet-stream'})
        self.assertEqual(status,201);f=json.loads(body)
        status,h,data=self.request('GET','/api/files/'+f['id'])
        self.assertEqual(status,200);self.assertEqual(h['Content-Type'],'application/octet-stream')
        self.assertTrue(h['Content-Disposition'].startswith('attachment;'))
        self.assertEqual(h['X-Content-Type-Options'],'nosniff')


class DirectoryLockTests(unittest.TestCase):
    def test_second_owner_cannot_recover_an_active_worker(self):
        try:m=importlib.import_module('engineering.local_app.lock')
        except ModuleNotFoundError:self.fail('Exclusive local data lock is missing')
        with tempfile.TemporaryDirectory() as tmp:
            with m.DataLock(Path(tmp)):
                with self.assertRaises(RuntimeError):
                    with m.DataLock(Path(tmp)):pass
            with m.DataLock(Path(tmp)):pass

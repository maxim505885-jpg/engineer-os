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
                content=getattr(owner,'core_reply','Нужна проверка источника')
                self.send_response(200);self.end_headers();self.wfile.write(json.dumps({'choices':[{'message':{'content':content}}]},ensure_ascii=False).encode())
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
        self.assertEqual(f['extraction_coverage']['method'],'UTF8')
        self.assertEqual(f['extraction_coverage']['completeness'],'NOT_CHECKED')
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

    def test_profile_execution_uses_local_protocol_and_durable_results(self):
        from engineering.local_app.worker import Worker
        session=self.create()
        _,_,raw=self.request('POST',f'/api/sessions/{session}/files?name=r.txt',b'height 4m',{'Content-Type':'application/octet-stream'})
        f=json.loads(raw)
        self.core_reply=json.dumps(dict(status='UNCERTAINTY',summary='Unverified specialist draft',observations=[],limitations=['Measurements not checked']))
        payload=dict(prompt='Review only the roof',file_ids=[f['id']],mode='CORE_RUN',requested_checks=['report','normative'])
        path=f'/api/sessions/{session}/jobs'
        self.assertEqual(self.request('POST',path,payload,token=False)[0],403)
        self.assertEqual(self.request('POST',path,payload)[0],202)
        Worker(self.store,self.model).run_once()
        run=json.loads(self.request('GET',f'/api/sessions/{session}')[2])['jobs'][0]['result']
        self.assertEqual(len(self.requests),3)
        self.assertTrue(run['core_run']['analysis_complete'])
        self.assertEqual(run['core_run']['results'][-1]['agent'],'final-audit-agent')
        self.assertTrue(all(r['execution']=='COMPLETED' for r in run['core_run']['results']))
        self.assertFalse(run['acceptance_granted']);self.assertEqual(run['final_audit'],'NOT_RUN')
        self.assertIn('Review only the roof',str(self.requests[-1]))
        self.assertEqual(type(self.store)(Path(self.tmp.name)).snapshot(session)['jobs'][0]['result'],run)

    def test_drive_import_is_private_and_retains_origin(self):
        from tests.test_local_drive_import import Response,Token
        from engineering.storage.google_drive import GoogleDriveClient
        import hashlib
        data=b'Imported original 4m';calls=[]
        meta=dict(id='drive_original_123',name='drive-report.txt',mimeType='text/plain',size=str(len(data)),md5Checksum=hashlib.md5(data).hexdigest(),modifiedTime='2026-10-06T00:00:00Z',capabilities={'canDownload':True},trashed=False)
        def opener(req,timeout):
            calls.append(req.full_url)
            return Response(data if 'alt=media' in req.full_url else json.dumps(meta).encode())
        self.server.drive_client=GoogleDriveClient(Token(),opener)
        self.assertEqual(self.request('GET','/api/drive/status',token=False)[0],403)
        status=json.loads(self.request('GET','/api/drive/status')[2])
        self.assertTrue(status['configured']);self.assertFalse(status['connection_verified'])
        session=self.create();path=f'/api/sessions/{session}/drive-import';payload={'source':'drive_original_123'}
        self.assertEqual(self.request('POST',path,payload,token=False)[0],403);self.assertEqual(calls,[])
        code,_,raw=self.request('POST',path,payload);self.assertEqual(code,201);file=json.loads(raw)
        self.assertEqual(self.request('GET','/api/files/'+file['id'])[2],data)
        self.assertEqual(file['source_metadata']['provider'],'GOOGLE_DRIVE')
        self.assertFalse(file['acceptance_granted']);self.assertNotIn('PRIVATE_TOKEN',raw.decode())
        other=self.create()
        self.assertEqual(json.loads(self.request('GET',f'/api/sessions/{other}')[2])['files'],[])
        self.server.drive_client=None
        self.assertEqual(self.request('POST',path,payload)[0],503)
        self.assertEqual(len(json.loads(self.request('GET',f'/api/sessions/{session}')[2])['files']),1)

    def test_drive_import_shares_upload_limit(self):
        session=self.create()
        self.server.upload_slots.acquire();self.server.upload_slots.acquire()
        try:self.assertEqual(self.request('POST',f'/api/sessions/{session}/drive-import',{'source':'drive_original_123'})[0],429)
        finally:self.server.upload_slots.release();self.server.upload_slots.release()

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

    def test_pdf_preview_endpoint_is_private_png_and_does_not_accept_record(self):
        import fitz
        from engineering.local_app.evidence import register
        session=self.create()
        with fitz.open() as pdf:
            pdf.new_page().insert_text((40,40),'height 4m');data=pdf.tobytes()
        _,_,raw=self.request('POST',f'/api/sessions/{session}/files?name=r.pdf',data,{'Content-Type':'application/octet-stream'})
        f=json.loads(raw);r=register(self.store,session,file_id=f['id'],page=1,quote='height 4m',statement='Unverified')
        path=f"/api/sessions/{session}/evidence/{r['id']}/preview"
        self.assertEqual(self.request('GET',path,token=False)[0],403)
        status,h,png=self.request('GET',path)
        self.assertEqual(status,200);self.assertEqual(h['Content-Type'],'image/png')
        self.assertEqual(h['X-Content-Type-Options'],'nosniff');self.assertEqual(h['Cache-Control'],'no-store')
        self.assertTrue(png.startswith(b'\x89PNG'));self.assertFalse(self.store.get_evidence(session,r['id'])['acceptance_granted'])
        other=self.create();self.assertEqual(self.request('GET',path.replace(session,other))[0],400)
        self.assertTrue(self.server.preview_slots.acquire(False));self.assertTrue(self.server.preview_slots.acquire(False))
        try:self.assertEqual(self.request('GET',path)[0],429)
        finally:self.server.preview_slots.release();self.server.preview_slots.release()

    def test_source_review_api_is_private_and_detects_stale_revision(self):
        from engineering.local_app.evidence import register
        session=self.create()
        _,_,raw=self.request('POST',f'/api/sessions/{session}/files?name=r.txt',b'height 4m',{'Content-Type':'application/octet-stream'})
        f=json.loads(raw);r=register(self.store,session,file_id=f['id'],quote='height 4m',statement='Unknown')
        path=f"/api/sessions/{session}/evidence/{r['id']}/reviews"
        payload=dict(expected_revision=0,decision='SOURCE_CONFIRMED',note='Checked quote',actor='Local',acceptance_granted=True,actor_verified=True)
        self.assertEqual(self.request('POST',path,payload,token=False)[0],403)
        status,_,raw=self.request('POST',path,payload);event=json.loads(raw)
        self.assertEqual(status,201);self.assertFalse(event['acceptance_granted']);self.assertFalse(event['actor_verified'])
        self.assertEqual(self.request('POST',path,payload)[0],409)
        self.assertEqual(self.request('POST',path,dict(payload,expected_revision=True))[0],400)
        self.assertEqual(len(json.loads(self.request('GET',f'/api/sessions/{session}')[2])['evidence'][0]['reviews']),1)

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

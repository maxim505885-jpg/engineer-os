"""Loopback browser API; no model-directed tools or acceptance endpoints."""
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
import json
from pathlib import Path
import secrets
import threading
import time
from urllib.parse import urlsplit,parse_qs,quote
from .files import preserve_file,MAX_FILE_BYTES
from .store import ReviewConflict

UI=Path(__file__).parent/'ui'
_DRIVE_DEFAULT=object()
CSP="default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self' data:; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'"


class RequestProblem(Exception):
    def __init__(self,status,message):self.status=status;self.message=message


class LocalServer(ThreadingHTTPServer):
    daemon_threads=True


def make_server(store,model,host='127.0.0.1',port=0,*,drive_client=_DRIVE_DEFAULT):
    if host!='127.0.0.1':raise ValueError('Application must bind to 127.0.0.1 only')
    from .drive_import import DriveImportError,configured_client,import_original
    if drive_client is _DRIVE_DEFAULT:drive_client=configured_client()
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def setup(self):
            super().setup();self.connection.settimeout(30)

        def check_request(self,api=False):
            if self.headers.get('Host')!=f'127.0.0.1:{self.server.server_port}':raise RequestProblem(403,'Unexpected Host')
            origin=self.headers.get('Origin')
            if origin is not None and origin!=self.server.origin:raise RequestProblem(403,'Cross-origin access rejected')
            if self.headers.get('Sec-Fetch-Site')=='cross-site':raise RequestProblem(403,'Cross-site access rejected')
            if api and not secrets.compare_digest(self.headers.get('X-Engineer-Token',''),self.server.token):raise RequestProblem(403,'Open this app page again; local session token required')

        def respond(self,status,data,ctype='application/json; charset=utf-8',extra=None):
            if not isinstance(data,bytes):data=json.dumps(data,ensure_ascii=False).encode()
            self.send_response(status);self.send_header('Content-Type',ctype);self.send_header('Content-Length',str(len(data)))
            self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.send_header('Content-Security-Policy',CSP)
            for k,v in (extra or {}).items():self.send_header(k,v)
            self.end_headers();self.wfile.write(data)

        def body(self,maximum):
            values=self.headers.get_all('Content-Length') or []
            if len(values)!=1 or not values[0].isdigit():raise RequestProblem(411,'Single Content-Length required')
            if self.headers.get('Transfer-Encoding'):raise RequestProblem(400,'Chunked request bodies unsupported')
            size=int(values[0])
            if size>maximum:raise RequestProblem(413,'Request exceeds size limit')
            data=self.rfile.read(size)
            if len(data)!=size:raise RequestProblem(400,'Incomplete body')
            return data

        def json_body(self):
            if self.headers.get('Content-Type','').split(';')[0]!='application/json':raise RequestProblem(415,'JSON content type required')
            try:value=json.loads(self.body(65536))
            except (UnicodeDecodeError,json.JSONDecodeError):raise RequestProblem(400,'Invalid JSON') from None
            if not isinstance(value,dict):raise RequestProblem(400,'JSON object required')
            return value

        def do_GET(self):self.dispatch(False)
        def do_POST(self):self.dispatch(True)

        def dispatch(self,post):
            try:
                if not self.path.startswith('/') or self.path.startswith('//'):
                    raise RequestProblem(400,'Canonical local request path required')
                path=urlsplit(self.path);route=path.path;parts=route.strip('/').split('/')
                self.check_request(route.startswith('/api/'))
                if not post and route in {'/','/app.js','/styles.css'}:
                    name={'/':'index.html','/app.js':'app.js','/styles.css':'styles.css'}[route]
                    data=(UI/name).read_bytes()
                    if route=='/':data=data.replace(b'__APP_TOKEN__',self.server.token.encode())
                    ctype={'/':'text/html; charset=utf-8','/app.js':'application/javascript; charset=utf-8','/styles.css':'text/css; charset=utf-8'}[route]
                    return self.respond(200,data,ctype)
                if route=='/api/status' and not post:
                    with self.server.health_lock:
                        if time.monotonic()-self.server.health_at>15:
                            self.server.health_cache=model.health();self.server.health_at=time.monotonic()
                        health=self.server.health_cache
                    return self.respond(200,dict(model=health,engineering_status='UNCERTAINTY',acceptance_granted=False))
                if route=='/api/drive/status' and not post:
                    configured=self.server.drive_client is not None
                    return self.respond(200,dict(configured=configured,connection_verified=False,note='Настройки Drive есть; доступ проверяется при импорте.' if configured else 'Drive не настроен на локальном сервере. Можно загрузить файл вручную.'))
                if route=='/api/sessions':
                    return self.respond(201,store.create_session(self.json_body().get('title','Новый диалог'))) if post else self.respond(200,store.sessions())
                if len(parts)==3 and parts[:2]==['api','sessions'] and not post:return self.respond(200,store.snapshot(parts[2]))
                if len(parts)==4 and parts[:2]==['api','sessions'] and post:
                    if parts[3]=='extraction':
                        body=self.json_body()
                        return self.respond(202,store.enqueue_extraction(parts[2],body.get('file_id'),body.get('backend','native')))
                    if parts[3]=='drive-import':
                        body=self.json_body()
                        if not self.server.upload_slots.acquire(blocking=False):raise RequestProblem(429,'Another upload is busy; retry shortly')
                        try:return self.respond(201,import_original(store,parts[2],self.server.drive_client,body.get('source'),expected_sha256=body.get('expected_sha256')))
                        finally:self.server.upload_slots.release()
                    if parts[3]=='evidence':
                        from .evidence import register
                        body=self.json_body()
                        return self.respond(201,register(store,parts[2],file_id=body.get('file_id'),quote=body.get('quote'),statement=body.get('statement'),page=body.get('page'),data_class=body.get('data_class','U')))
                    if parts[3]=='jobs':
                        body=self.json_body();return self.respond(202,store.enqueue(parts[2],body.get('prompt'),body.get('file_ids',[]),mode=body.get('mode','CHAT'),requested_checks=body.get('requested_checks')))
                    if parts[3]=='files':
                        names=parse_qs(path.query).get('name',[])
                        if len(names)!=1:raise RequestProblem(400,'Filename required')
                        if self.headers.get('Content-Type')!='application/octet-stream':raise RequestProblem(415,'Binary content type required')
                        if not self.server.upload_slots.acquire(blocking=False):raise RequestProblem(429,'Another upload is busy; retry shortly')
                        try:return self.respond(201,preserve_file(store,parts[2],names[0],self.body(MAX_FILE_BYTES)))
                        finally:self.server.upload_slots.release()
                if len(parts)>=6 and parts[:2]==['api','sessions'] and parts[3]=='jobs':
                    if len(parts)==6 and parts[5]=='resume' and post:
                        self.json_body()
                        return self.respond(202,store.resume_extraction(parts[2],parts[4]))
                    if len(parts)==6 and parts[5]=='pages' and not post:
                        query=parse_qs(path.query)
                        return self.respond(200,store.extraction_pages(parts[2],parts[4],offset=int(query.get('offset',['0'])[0]),limit=int(query.get('limit',['50'])[0])))
                    if len(parts)==7 and parts[5]=='pages' and not post:
                        return self.respond(200,store.extraction_page(parts[2],parts[4],int(parts[6])))
                if len(parts)==6 and parts[:2]==['api','sessions'] and parts[3]=='evidence' and parts[5]=='reviews' and post:
                    from .review import record_review
                    body=self.json_body()
                    return self.respond(201,record_review(store,parts[2],parts[4],expected_revision=body.get('expected_revision'),decision=body.get('decision'),note=body.get('note'),actor=body.get('actor')))
                if len(parts)==6 and parts[:2]==['api','sessions'] and parts[3]=='evidence' and parts[5]=='preview' and not post:
                    from .preview import render_preview
                    if not self.server.preview_slots.acquire(blocking=False):raise RequestProblem(429,'Another preview is busy; retry shortly')
                    try:return self.respond(200,render_preview(store,parts[2],parts[4]),'image/png')
                    finally:self.server.preview_slots.release()
                if len(parts)==3 and parts[:2]==['api','files'] and not post:
                    f=store.get_file(parts[2]);file=Path(f['path'])
                    self.send_response(200);self.send_header('Content-Type','application/octet-stream');self.send_header('Content-Length',str(file.stat().st_size))
                    self.send_header('Content-Disposition',"attachment; filename*=UTF-8''"+quote(f['name'],safe=''))
                    self.send_header('X-Content-Type-Options','nosniff');self.send_header('Cache-Control','no-store');self.send_header('Content-Security-Policy',CSP);self.end_headers()
                    with file.open('rb') as stream:
                        for chunk in iter(lambda:stream.read(1024*1024),b''):self.wfile.write(chunk)
                    return
                raise RequestProblem(404,'Route not found')
            except RequestProblem as exc:self.respond(exc.status,dict(error=exc.message))
            except DriveImportError as exc:self.respond(exc.status,dict(error=str(exc)))
            except ReviewConflict as exc:self.respond(409,dict(error=str(exc)))
            except ValueError as exc:self.respond(400,dict(error=str(exc)))
            except (BrokenPipeError,ConnectionResetError):pass
            except Exception:self.respond(500,dict(error='Local application error; original data retained'))
    server=LocalServer((host,port),Handler)
    server.token=secrets.token_urlsafe(32);server.origin=f'http://127.0.0.1:{server.server_port}'
    server.drive_client=drive_client
    server.health_cache=None;server.health_at=float('-inf');server.health_lock=threading.Lock();server.upload_slots=threading.BoundedSemaphore(2);server.preview_slots=threading.BoundedSemaphore(2)
    return server

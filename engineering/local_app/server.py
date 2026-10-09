"""Loopback browser API; no model-directed tools or acceptance endpoints."""
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
import json
from pathlib import Path
import secrets
import threading
import time
from urllib.parse import urlsplit,parse_qs,quote
from .files import preserve_file,file_limit
from .store import ReviewConflict

UI=Path(__file__).parent/'ui'
_DRIVE_DEFAULT=object()
CSP="default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self' data:; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'"


class RequestProblem(Exception):
    def __init__(self,status,message):self.status=status;self.message=message


class LocalServer(ThreadingHTTPServer):
    daemon_threads=True


def make_server(store,model,host='127.0.0.1',port=0,*,drive_client=_DRIVE_DEFAULT,recovery_only=False,selection_path=None):
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

        def json_body(self,maximum=65536):
            if self.headers.get('Content-Type','').split(';')[0]!='application/json':raise RequestProblem(415,'JSON content type required')
            try:value=json.loads(self.body(maximum))
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
                if not post and route in {'/','/app.js','/cad-memory.js','/styles.css','/recovery.html','/recovery.js'}:
                    name={'/':'recovery.html' if recovery_only else 'index.html','/app.js':'app.js','/cad-memory.js':'cad-memory.js','/styles.css':'styles.css','/recovery.html':'recovery.html','/recovery.js':'recovery.js'}[route]
                    data=(UI/name).read_bytes()
                    if name.endswith('.html'):data=data.replace(b'__APP_TOKEN__',self.server.token.encode())
                    ctype='text/html; charset=utf-8' if name.endswith('.html') else 'text/css; charset=utf-8' if name.endswith('.css') else 'application/javascript; charset=utf-8'
                    return self.respond(200,data,ctype)
                if route=='/api/data/status' and not post:
                    return self.respond(200,dict(root=str(self.server.data_root),recovery_only=recovery_only))
                if parts[:2]==['api','data'] and len(parts)==3 and post:
                    if not recovery_only:raise RequestProblem(409,'Остановите основное приложение и откройте Recover_ENGINEER_OS.cmd — операции доступны в режиме обслуживания.')
                    if not self.server.data_slots.acquire(blocking=False):raise RequestProblem(409,'Другая операция с данными ещё выполняется.')
                    try:
                        from .backup import create_backup,verify_backup,restore_backup
                        from .settings import activate
                        body=self.json_body()
                        def absolute(key):
                            value=body.get(key)
                            if not isinstance(value,str) or not value.strip() or '\x00' in value or not Path(value).is_absolute():raise ValueError('Укажите полный абсолютный путь: '+key)
                            return Path(value)
                        action=parts[2]
                        if action=='backup':result=create_backup(self.server.data_root,absolute('archive'))
                        elif action=='verify':result=verify_backup(absolute('archive'))
                        elif action=='restore':
                            result=restore_backup(absolute('archive'),absolute('target'))
                            self.server.data_root=Path(result['path'])
                        elif action=='activate':
                            root=activate(absolute('target'),self.server.selection_path)
                            self.server.data_root=root;result=dict(status='SELECTED',path=str(root))
                        else:raise RequestProblem(404,'Unknown data action')
                        return self.respond(200,result)
                    except RuntimeError as exc:raise RequestProblem(409,str(exc)) from None
                    except OSError as exc:raise RequestProblem(400,str(exc)) from None
                    finally:self.server.data_slots.release()
                if recovery_only:raise RequestProblem(409,'Режим обслуживания: чат и модель не запускаются.')
                if route=='/api/status' and not post:
                    with self.server.health_lock:
                        if time.monotonic()-self.server.health_at>15:
                            self.server.health_cache=model.health();self.server.health_at=time.monotonic()
                        health=self.server.health_cache
                    return self.respond(200,dict(model=health,engineering_status='UNCERTAINTY',acceptance_granted=False))
                if route=='/api/drive/status' and not post:
                    configured=self.server.drive_client is not None
                    return self.respond(200,dict(configured=configured,connection_verified=False,note='Настройки Drive есть; доступ проверяется при импорте.' if configured else 'Drive не настроен на локальном сервере. Можно загрузить файл вручную.'))
                if route=='/api/model/settings' and post:
                    from .settings import configure
                    with self.server.health_lock:
                        result=configure(store,model,self.json_body());self.server.health_at=0
                    return self.respond(200,result)
                if route=='/api/sessions':
                    return self.respond(201,store.create_session(self.json_body().get('title','Новый диалог'))) if post else self.respond(200,store.sessions())
                if len(parts)==3 and parts[:2]==['api','sessions'] and not post:return self.respond(200,store.snapshot(parts[2]))
                if len(parts)==4 and parts[:2]==['api','sessions'] and parts[3]=='history' and not post:
                    query=parse_qs(path.query)
                    return self.respond(200,store.history(parts[2],kind=query.get('kind',['messages'])[0],before=int(query['before'][0]) if 'before' in query else None,limit=int(query.get('limit',['50'])[0])))
                if len(parts)==4 and parts[:2]==['api','sessions'] and parts[3]=='requirements' and not post:
                    from .requirements import report
                    return self.respond(200,report(store,parts[2]))
                if len(parts)==4 and parts[:2]==['api','sessions'] and parts[3]=='domain-packets':
                    from .domain_packets import save,report
                    if not post:return self.respond(200,report(store,parts[2]))
                    body=self.json_body()
                    return self.respond(201,save(store,parts[2],packet=body.get('packet'),expected_revision=body.get('expected_revision')))
                if len(parts)==4 and parts[:2]==['api','sessions'] and parts[3]=='real-case':
                    from .real_case import build,report
                    if not post:return self.respond(200,report(store,parts[2]))
                    body=self.json_body()
                    return self.respond(201,build(store,parts[2],job_id=body.get('job_id'),expected_revision=body.get('expected_revision'),manifest=body.get('manifest')))
                if len(parts)==4 and parts[:2]==['api','sessions'] and parts[3]=='final-audit':
                    from .final_audit import build,report
                    if not post:return self.respond(200,report(store,parts[2]))
                    body=self.json_body()
                    return self.respond(201,build(store,parts[2],case_id=body.get('case_id'),expected_revision=body.get('expected_revision')))
                if len(parts)==4 and parts[:2]==['api','sessions'] and parts[3]=='conclusions':
                    from .conclusions import build,report
                    if not post:return self.respond(200,report(store,parts[2]))
                    body=self.json_body(262144)
                    return self.respond(201,build(store,parts[2],expected_revision=body.get('expected_revision'),
                        author=body.get('author'),summary=body.get('summary',''),recommendations=body.get('recommendations',''),
                        limitations=body.get('limitations',''),expected_basis_sha256=body.get('expected_basis_sha256'),template_id=body.get('template_id','legacy'),illustration_requests=body.get('illustration_requests')))
                if len(parts)>=4 and parts[:2]==['api','sessions'] and parts[3]=='knowledge':
                    from . import knowledge
                    sid=parts[2]
                    if len(parts)==4:
                        if not post:return self.respond(200,knowledge.report(store,sid))
                        b=self.json_body()
                        return self.respond(201,knowledge.promote(store,sid,expected_audit_id=b.get('expected_audit_id'),title=b.get('title'),evidence_ids=b.get('evidence_ids'),scope_session_ids=b.get('scope_session_ids'),knowledge_id=b.get('knowledge_id'),expected_revision=b.get('expected_revision',0),actor=b.get('actor')))
                    if len(parts)==5 and not post and parts[4] in {'recall','export'}:
                        if parts[4]=='export':return self.respond(200,knowledge.export(store,sid))
                        return self.respond(200,knowledge.recall(store,sid,query=parse_qs(path.query).get('query',[''])[0]))
                    if len(parts)==6 and post and parts[5] in {'revoke','delete'}:
                        b=self.json_body();operation=knowledge.revoke if parts[5]=='revoke' else knowledge.delete
                        return self.respond(201,operation(store,sid,parts[4],expected_revision=b.get('expected_revision'),actor=b.get('actor'),reason=b.get('reason')))
                if len(parts)>=5 and parts[:2]==['api','sessions'] and parts[3]=='cad':
                    from . import cad
                    if len(parts)==5 and not post:return self.respond(200,cad.inventory(store,parts[2],parts[4]))
                    if len(parts)==6 and parts[5]=='derive' and post:
                        return self.respond(201,cad.derive(store,parts[2],parts[4],request=self.json_body().get('request')))
                    if len(parts)==6 and parts[5]=='locator' and post:
                        b=self.json_body();return self.respond(201,cad.register_locator(store,parts[2],parts[4],handle=b.get('handle'),statement=b.get('statement')))
                    if len(parts)==6 and parts[5]=='export' and not post:
                        data,mime=cad.export(store,parts[2],parts[4])
                        return self.respond(200,data,mime,{'Content-Disposition':'attachment; filename="ENGINEER_OS_DERIVED.dxf"'})
                if len(parts)==6 and parts[:2]==['api','sessions'] and parts[3]=='conclusions' and not post:
                    from .conclusions import export
                    data,mime=export(store,parts[2],revision=int(parts[4]),format=parts[5])
                    return self.respond(200,data,mime,extra={'Content-Disposition':'attachment; filename="ENGINEER_OS_draft_v'+str(int(parts[4]))+'.'+parts[5]+'"'})
                if len(parts)==6 and parts[:2]==['api','sessions'] and parts[3]=='requirements' and parts[5]=='assessments' and post:
                    from .requirements import assess
                    body=self.json_body()
                    return self.respond(201,assess(store,parts[2],set_id=body.get('set_id'),requirement_id=parts[4],expected_revision=body.get('expected_revision'),conclusion=body.get('conclusion'),evidence_ids=body.get('evidence_ids',[]),relation=body.get('relation'),actor=body.get('actor')))
                if len(parts)==4 and parts[:2]==['api','sessions'] and post:
                    if parts[3]=='requirements':
                        from .requirements import create_set
                        body=self.json_body()
                        return self.respond(201,create_set(store,parts[2],text=body.get('text'),source_evidence_ids=body.get('source_evidence_ids')))
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
                        return self.respond(201,register(store,parts[2],file_id=body.get('file_id'),quote=body.get('quote'),statement=body.get('statement'),page=body.get('page'),data_class=body.get('data_class','U'),source_job=body.get('source_job'),logical_unit=body.get('logical_unit')))
                    if parts[3]=='jobs':
                        body=self.json_body();return self.respond(202,store.enqueue(parts[2],body.get('prompt'),body.get('file_ids',[]),mode=body.get('mode','CHAT'),requested_checks=body.get('requested_checks')))
                    if parts[3]=='files':
                        names=parse_qs(path.query).get('name',[])
                        if len(names)!=1:raise RequestProblem(400,'Filename required')
                        if self.headers.get('Content-Type')!='application/octet-stream':raise RequestProblem(415,'Binary content type required')
                        if not self.server.upload_slots.acquire(blocking=False):raise RequestProblem(429,'Another upload is busy; retry shortly')
                        try:return self.respond(201,preserve_file(store,parts[2],names[0],self.body(file_limit(names[0]))))
                        finally:self.server.upload_slots.release()
                if len(parts)>=6 and parts[:2]==['api','sessions'] and parts[3]=='jobs':
                    if len(parts)==6 and parts[5] in {'cancel','retry'} and post:
                        self.json_body()
                        operation=store.cancel if parts[5]=='cancel' else store.retry
                        return self.respond(202,operation(parts[2],parts[4]))
                    if len(parts)==6 and parts[5]=='analysis' and not post:
                        query=parse_qs(path.query)
                        return self.respond(200,store.analysis_receipts(parts[2],parts[4],offset=int(query.get('offset',['0'])[0]),limit=int(query.get('limit',['50'])[0])))
                    if len(parts)==6 and parts[5]=='resume' and post:
                        self.json_body()
                        return self.respond(202,store.resume_extraction(parts[2],parts[4]))
                    if len(parts)==6 and parts[5]=='resume-analysis' and post:
                        self.json_body()
                        return self.respond(202,store.resume_analysis(parts[2],parts[4],model))
                    if len(parts)==6 and parts[5]=='pages' and not post:
                        query=parse_qs(path.query)
                        return self.respond(200,store.extraction_pages(parts[2],parts[4],offset=int(query.get('offset',['0'])[0]),limit=int(query.get('limit',['50'])[0])))
                    if len(parts)==7 and parts[5]=='pages' and not post:
                        return self.respond(200,store.extraction_page(parts[2],parts[4],int(parts[6])))
                if len(parts)==6 and parts[:2]==['api','sessions'] and parts[3]=='evidence' and parts[5]=='reviews' and post:
                    from .review import record_review
                    body=self.json_body()
                    return self.respond(201,record_review(store,parts[2],parts[4],expected_revision=body.get('expected_revision'),decision=body.get('decision'),note=body.get('note'),actor=body.get('actor')))
                if len(parts)==6 and parts[:2]==['api','sessions'] and parts[3]=='files' and parts[5]=='preview' and not post:
                    from .preview import render_original
                    query=parse_qs(path.query)
                    if not self.server.preview_slots.acquire(blocking=False):raise RequestProblem(429,'Another preview is busy; retry shortly')
                    try:return self.respond(200,render_original(store,parts[2],parts[4],int(query.get('page',['1'])[0])),'image/png')
                    finally:self.server.preview_slots.release()
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
    server.data_root=Path(store.root).resolve();server.data_slots=threading.BoundedSemaphore(1)
    server.selection_path=Path(selection_path) if selection_path is not None else Path(__file__).resolve().parents[2]/'.engineer-os/active-data-dir.txt'
    server.health_cache=None;server.health_at=float('-inf');server.health_lock=threading.Lock();server.upload_slots=threading.BoundedSemaphore(2);server.preview_slots=threading.BoundedSemaphore(2)
    return server

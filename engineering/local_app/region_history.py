"""Append-only derived region reads; no evidence or acceptance is created."""
import hashlib,json,math,os,signal,stat,subprocess,sys,time,uuid
from pathlib import Path
from .store import identifier
from .lock import managed_file
MAX_READS_PER_FILE=200
MAX_STORED_BYTES_PER_FILE=64*1024*1024
MAX_RESULT_BYTES=4*1024*1024
PROCESS_TIMEOUT=95

def _json(value):return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)
def _source(store,sid,fid):
    identifier(sid);file=store.get_file(fid)
    if file['session_id']!=sid:raise ValueError('Region source belongs to another conversation')
    if Path(file['name']).suffix.lower()!='.pdf':raise ValueError('PDF region source required')
    path=Path(file['path']);managed_file(path)
    if not path.is_file() or path.stat().st_size!=file['size']:raise ValueError('Region source changed')
    digest=hashlib.sha256();size=0;deadline=time.monotonic()+10
    descriptor=os.open(path,os.O_RDONLY|getattr(os,'O_NOFOLLOW',0)|getattr(os,'O_NONBLOCK',0))
    with os.fdopen(descriptor,'rb') as stream:
        before=os.fstat(stream.fileno())
        if not stat.S_ISREG(before.st_mode) or before.st_size!=file['size'] or before.st_size>128*1024*1024:raise ValueError('Region source size/type changed')
        while True:
            if time.monotonic()>deadline:raise ValueError('Region source verification timeout')
            chunk=stream.read(min(1024*1024,file['size']-size+1))
            if not chunk:break
            size+=len(chunk)
            if size>file['size']:raise ValueError('Region source grew')
            digest.update(chunk)
        after=os.fstat(stream.fileno())
    if size!=file['size'] or (before.st_ino,before.st_mtime_ns,before.st_ctime_ns)!=(after.st_ino,after.st_mtime_ns,after.st_ctime_ns) or digest.hexdigest()!=file['sha256']:raise ValueError('Region source changed')
    return file

def _run(file,request):
    environment={k:v for k,v in os.environ.items() if k in {'PATH','SYSTEMROOT','WINDIR','TEMP','TMP','TESSDATA_PREFIX','ENGINEER_OS_TESSERACT_BIN','ENGINEER_OS_TESSDATA_DIR','ENGINEER_OS_OCR_LAYOUT'}}
    environment['PYTHONUTF8']='1'
    if request['ocr']:
        from .ocr import _paths
        binary,data=_paths()
        environment.update(ENGINEER_OS_TESSERACT_BIN=str(binary),ENGINEER_OS_TESSDATA_DIR=str(data))
    payload=_json(dict(source=file['path'],page=request['page'],bbox=request['bbox'],sha256=request['expected_sha256'],ocr=request['ocr'],ocr_psm=request.get('ocr_psm',6),ocr_preprocess=request.get('ocr_preprocess','none'),ocr_language=request.get('ocr_language','rus+eng'))).encode()
    child=subprocess.Popen([sys.executable,'-m','engineering.local_app.region_process'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,env=environment,cwd=Path(__file__).resolve().parents[2],start_new_session=os.name!='nt')
    try:output,_=child.communicate(payload,timeout=PROCESS_TIMEOUT)
    except subprocess.TimeoutExpired:
        cleanup_failed=False
        try:
            if os.name=='nt':
                killed=subprocess.run([str(Path(os.environ.get('SYSTEMROOT',r'C:\Windows'))/'System32'/'taskkill.exe'),'/PID',str(child.pid),'/T','/F'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=5,check=False)
                cleanup_failed=killed.returncode!=0
            else:
                try:os.killpg(child.pid,signal.SIGKILL)
                except ProcessLookupError:pass
        finally:
            child.kill()
            try:child.communicate(timeout=5)
            except subprocess.TimeoutExpired:raise ValueError('REGION_CLEANUP_FAILED: no result saved') from None
        if cleanup_failed:raise ValueError('REGION_CLEANUP_FAILED: no result saved')
        raise ValueError('REGION_TIMEOUT: no result saved') from None
    if child.returncode or len(output)>MAX_RESULT_BYTES:raise ValueError('REGION_PROCESS_FAILED')
    try:response=json.loads(output)
    except (ValueError,UnicodeError):raise ValueError('REGION_PROCESS_INVALID_RESULT') from None
    if response.get('error'):raise ValueError(response['error'])
    return response['result']

def _validate_request(request,file):
    if not isinstance(request,dict) or set(request)-{'page','bbox','expected_sha256','ocr','ocr_psm','ocr_preprocess','ocr_language'} or not {'page','bbox','expected_sha256','ocr'}<=set(request):raise ValueError('Exact region request fields required')
    if request['expected_sha256']!=file['sha256']:raise ValueError('Region source hash mismatch')
    if type(request['page'])!=int or request['page']<1 or type(request['ocr'])!=bool:raise ValueError('Invalid region request profile')
    if type(request.get('ocr_psm',6))!=int or request.get('ocr_psm',6) not in (6,7,11):raise ValueError('Invalid OCR profile')
    profile=request.get('ocr_preprocess','none')
    if type(profile)!=str or profile not in ('none','padded','italic'):raise ValueError('Invalid OCR preprocessing')
    if profile!='none' and (not request['ocr'] or request.get('ocr_psm',6)!=7):raise ValueError('OCR preprocessing requires selected line')
    language=request.get('ocr_language','rus+eng')
    if type(language)!=str or language not in ('rus+eng','eng'):raise ValueError('Invalid OCR language')
    if language!='rus+eng' and not request['ocr']:raise ValueError('OCR language requires OCR')
    bbox=request['bbox']
    if not isinstance(bbox,list) or len(bbox)!=4 or any(type(v) not in (int,float) or not math.isfinite(v) for v in bbox) or not (0<=bbox[0]<bbox[2] and 0<=bbox[1]<bbox[3]):raise ValueError('Invalid region request bounds')

def _validate(result,file,request):
    _validate_request(request,file)
    from .region_readback import COORDINATE_SPACE
    if not isinstance(result,dict) or result.get('source_sha256')!=file['sha256'] or result.get('source_bytes')!=file['size'] or result.get('page_no')!=request['page'] or result.get('source_bbox')!=request['bbox'] or result.get('coordinate_space')!=COORDINATE_SPACE:raise ValueError('Region result identity mismatch')
    if any(result.get(k) is not False for k in ('acceptance_granted','quality_verified','page_complete','document_complete')) or result.get('scope')!='SELECTED_REGION_READBACK_UNVERIFIED' or result.get('process_isolated') is not True:raise ValueError('Region result status mismatch')
    if not request['ocr'] and result.get('ocr_blocks'):raise ValueError('Unexpected OCR result')
    import base64
    raster=result.get('rendered_region',{})
    try:png=base64.b64decode(raster['png_base64'],validate=True)
    except (KeyError,ValueError,TypeError):raise ValueError('Invalid region raster') from None
    if len(png)>2*1024*1024 or hashlib.sha256(png).hexdigest()!=raster.get('png_sha256') or raster.get('source_bbox')!=request['bbox']:raise ValueError('Region raster identity mismatch')
    if raster.get('source_sha256')!=file['sha256'] or raster.get('page_no')!=request['page'] or raster.get('coordinate_space')!=COORDINATE_SPACE:raise ValueError('Region raster scope mismatch')
    if request['ocr']:
        dossier=result.get('ocr_dossier')
        if not isinstance(dossier,dict) or dossier.get('page_no')!=request['page'] or dossier.get('coordinate_space')!=COORDINATE_SPACE or dossier.get('coverage')!='SELECTED_REGION_EXECUTED' or dossier.get('quality_verified') is not False or dossier.get('acceptance_granted') is not False:raise ValueError('OCR dossier scope mismatch')
        regions=dossier.get('regions')
        if not isinstance(regions,list) or len(regions)!=1:raise ValueError('OCR selected input missing')
        region=regions[0];input_raster=region.get('input_raster',{})
        if region.get('bbox')!=dict(zip(('left','top','right','bottom'),request['bbox'])) or region.get('execution')!='COMPLETED' or region.get('psm')!=request.get('ocr_psm',6) or not isinstance(input_raster,dict) or input_raster.get('png_sha256')!=raster['png_sha256'] or input_raster.get('width')!=raster['width'] or input_raster.get('height')!=raster['height']:raise ValueError('OCR selected raster mismatch')
        language=request.get('ocr_language','rus+eng')
        if region.get('language','rus+eng')!=language:raise ValueError('OCR language binding mismatch')
        engine=result.get('engine_identity')
        if not isinstance(engine,dict) or engine.get('language','rus+eng')!=language:raise ValueError('OCR language identity mismatch')
        profile=request.get('ocr_preprocess','none')
        derived=region.get('processed_raster')
        if profile=='none':
            if derived is not None or region.get('preprocessing','none')!='none':raise ValueError('Unexpected processed raster')
        else:
            from .ocr_label_preprocessing import prepare
            expected,metadata=prepare(png,profile,version=derived.get('transform_version') if isinstance(derived,dict) else None)
            if not isinstance(derived,dict) or region.get('preprocessing')!=profile or derived.get('source_png_sha256')!=raster['png_sha256'] or any(derived.get(k)!=v for k,v in metadata.items()):raise ValueError('OCR processed raster identity mismatch')
            if derived.get('png_sha256')!=hashlib.sha256(expected).hexdigest() or derived.get('png_base64')!=base64.b64encode(expected).decode('ascii'):raise ValueError('OCR processed raster content mismatch')


def _budget(db,fid):
    count,size=db.execute('SELECT count(*),coalesce(sum(length(CAST(result AS BLOB))),0) FROM source_region_reads WHERE file_id=?',(fid,)).fetchone()
    if count>=MAX_READS_PER_FILE or size>=MAX_STORED_BYTES_PER_FILE:raise ValueError('Region history limit reached')
    return size

def read_region(store,sid,fid,request):
    file=_source(store,sid,fid)
    _validate_request(request,file)
    with store.connection() as db:_budget(db,fid)
    result=_run(file,request)
    _validate(result,file,request)
    result['request_binding']=dict(request)
    serialized=_json(result)
    if len(serialized.encode())>MAX_RESULT_BYTES:raise ValueError('Region result size limit')
    _source(store,sid,fid)
    item=dict(id=str(uuid.uuid4()),result=result,created=time.time())
    with store.connection() as db:
        db.execute('BEGIN IMMEDIATE')
        size=_budget(db,fid)
        if size+len(serialized.encode())>MAX_STORED_BYTES_PER_FILE:raise ValueError('Region history byte limit reached')
        db.execute('INSERT INTO source_region_reads VALUES(?,?,?,?,?,?,?)',(item['id'],sid,fid,serialized,hashlib.sha256(serialized.encode()).hexdigest(),file['sha256'],item['created']))
    return item

def get_region(store,sid,fid,read_id):
    identifier(read_id);file=_source(store,sid,fid)
    with store.connection() as db:row=db.execute('SELECT * FROM source_region_reads WHERE id=? AND session_id=? AND file_id=?',(read_id,sid,fid)).fetchone()
    if row is None:raise ValueError('Region read not found')
    raw=row['result']
    if len(raw.encode())>MAX_RESULT_BYTES or hashlib.sha256(raw.encode()).hexdigest()!=row['result_sha256']:raise ValueError('Stored region result changed')
    result=json.loads(raw)
    if row['source_sha256']!=file['sha256'] or result.get('source_sha256')!=file['sha256'] or result.get('acceptance_granted') is not False:raise ValueError('Stored region identity mismatch')
    binding=result.get('request_binding')
    if not isinstance(binding,dict):raise ValueError('Stored region request missing')
    _validate(result,file,binding)
    return dict(id=row['id'],result=result,created=row['created'])

def list_regions(store,sid,fid,offset=0,limit=50):
    _source(store,sid,fid)
    if type(offset)!=int or offset<0 or type(limit)!=int or not 1<=limit<=50:raise ValueError('Invalid region history pagination')
    with store.connection() as db:
        total=db.execute('SELECT count(*) FROM source_region_reads WHERE session_id=? AND file_id=?',(sid,fid)).fetchone()[0]
        rows=db.execute('SELECT id,created FROM source_region_reads WHERE session_id=? AND file_id=? ORDER BY created DESC,id LIMIT ? OFFSET ?',(sid,fid,limit,offset)).fetchall()
    return dict(total=total,offset=offset,limit=limit,items=[dict(r) for r in rows],acceptance_granted=False)

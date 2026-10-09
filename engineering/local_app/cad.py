"""Session-bound CAD derivatives outside original storage, without acceptance authority."""
import hashlib
import json
import uuid
import time
from pathlib import Path
from .store import identifier
from engineering.cad.dxf_workflow import inventory_dxf,derive_annotation,verify_export,_request,_load
MAX_MANIFEST_BYTES=32000

def _source(store,session_id,file_id):
    identifier(session_id);store.snapshot(session_id)
    source=store.get_file(file_id)
    if source['session_id']!=session_id:raise ValueError('CAD source belongs to another conversation')
    path=Path(source['path']);folder=(store.root/'files').resolve()
    if path.is_symlink() or path.resolve().parent!=folder or path.suffix.lower() not in {'.dxf','.dwg'}:raise ValueError('Invalid original CAD path')
    from engineering.cad.intake import inspect_cad
    inspect_cad(path,source['sha256'])
    return source,path

def _folder(store,session_id):
    path=store.root/'derived'
    if path.is_symlink():raise ValueError('Invalid CAD derivative path')
    return path

def inventory(store,session_id,file_id):
    source,path=_source(store,session_id,file_id)
    report=dict(inventory_dxf(path,source['sha256']),file_id=file_id)
    if report.get('format')=='DXF' and 'entity_counts' in report:
        doc,_=_load(path,source['sha256'])
        report['entities']=[dict(handle=e.dxf.handle,type=e.dxftype(),layer=e.dxf.layer[:250]) for e in doc.modelspace()][:100]
        report['entities_truncated']=len(doc.modelspace())>100
    return report

def derive(store,session_id,file_id,*,request):
    source,path=_source(store,session_id,file_id);request=_request(request)
    if request['source_sha256']!=source['sha256']:raise ValueError('CAD source hash mismatch')
    for evidence_id in request['evidence_ids']:
        evidence=store.get_evidence(session_id,evidence_id)
        if evidence['file_id']!=file_id:raise ValueError('Annotation evidence must bind this CAD source')
    folder=_folder(store,session_id);folder.mkdir(parents=True,exist_ok=True)
    if sum(1 for _ in folder.glob(session_id+'-*.json'))>=50:raise ValueError('CAD derivative history limit: 50 per conversation')
    ident=str(uuid.uuid4());output=folder/(session_id+'-'+ident+'.dxf');manifest_path=folder/(session_id+'-'+ident+'.json')
    manifest=derive_annotation(path,output,request)
    manifest.update(id=ident,session_id=session_id,file_id=file_id,status='DERIVED_REVIEW_REQUIRED',acceptance_granted=False)
    encoded=json.dumps(manifest,sort_keys=True,ensure_ascii=False,allow_nan=False).encode()
    try:
        if len(encoded)>MAX_MANIFEST_BYTES:raise ValueError('CAD manifest limit')
        with manifest_path.open('xb') as stream:stream.write(encoded)
    except Exception:
        output.unlink(missing_ok=True);raise
    return manifest

def export(store,session_id,derivative_id):
    identifier(session_id);identifier(derivative_id);store.snapshot(session_id)
    folder=_folder(store,session_id);manifest_path=folder/(session_id+'-'+derivative_id+'.json');output=folder/(session_id+'-'+derivative_id+'.dxf')
    if manifest_path.is_symlink() or output.is_symlink() or not manifest_path.is_file() or manifest_path.stat().st_size>MAX_MANIFEST_BYTES:raise ValueError('CAD derivative unavailable')
    manifest=json.loads(manifest_path.read_bytes())
    if manifest.get('session_id')!=session_id or manifest.get('id')!=derivative_id:raise ValueError('CAD derivative identity mismatch')
    source,path=_source(store,session_id,manifest['file_id'])
    if manifest['source_sha256']!=source['sha256']:raise ValueError('CAD source identity mismatch')
    for evidence_id in manifest['request']['evidence_ids']:
        if store.get_evidence(session_id,evidence_id)['file_id']!=source['id']:raise ValueError('CAD evidence binding changed')
    verification=verify_export(path,output,manifest)
    if verification['status']!='PASS':raise ValueError('CAD derivative verification failed: '+','.join(verification['reasons']))
    data=output.read_bytes()
    if hashlib.sha256(data).hexdigest()!=manifest['output_sha256']:raise ValueError('CAD output changed during export')
    return data,'application/dxf'


def register_locator(store,session_id,file_id,*,handle,statement):
    """Record an actual DXF entity locator, without verifying its engineering meaning."""
    source,path=_source(store,session_id,file_id)
    if not isinstance(handle,str) or not 1<=len(handle)<=16 or any(c not in '0123456789ABCDEF' for c in handle):raise ValueError('Invalid DXF handle')
    if not isinstance(statement,str) or not statement.strip() or len(statement)>1000:raise ValueError('CAD statement must contain 1–1000 characters')
    doc,_=_load(path,source['sha256'])
    entity=next((e for e in doc.modelspace() if e.dxf.handle==handle),None)
    if entity is None:raise ValueError('Entity handle not found in source modelspace')
    locator=dict(format='DXF',source_sha256=source['sha256'],layout='Model',handle=handle,entity_type=entity.dxftype(),layer=entity.dxf.layer[:250])
    quote='DXF '+entity.dxftype()+' entity handle '+handle
    return store.add_evidence(dict(id=str(uuid.uuid4()),session_id=session_id,file_id=file_id,name=source['name'],source_sha256=source['sha256'],
        page=None,quote=quote,statement=statement,data_class='U',data_class_verified=False,source_match='MATCH',
        verification_note='Actual DXF entity handle located. Geometry meaning and engineering claim remain unverified.',
        status='UNVERIFIED',acceptance_granted=False,final_audit='NOT_RUN',created=time.time(),locator=locator,source_confirmable=False,
        provenance=None,document_validation=None))

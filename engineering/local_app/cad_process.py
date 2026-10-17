"""Read-only DXF staging using the existing limited child, not a hostile-code sandbox."""
import hashlib
from pathlib import Path
import re
import tempfile
import threading
from engineering.cad.intake import MAX_BYTES as MAX_SOURCE_BYTES

_slots=threading.BoundedSemaphore(1)

def _checked_hash(path,expected):
    if not isinstance(expected,str) or re.fullmatch('[0-9a-f]{64}',expected) is None:
        raise ValueError('CAD_SOURCE_IDENTITY_INVALID')
    path=Path(path)
    if not path.is_file() or not 0<path.stat().st_size<=MAX_SOURCE_BYTES:
        raise ValueError('CAD_SOURCE_SIZE_LIMIT')
    digest=hashlib.sha256();total=0
    with path.open('rb') as stream:
        while chunk:=stream.read(min(1024**2,MAX_SOURCE_BYTES-total+1)):
            total+=len(chunk)
            if total>MAX_SOURCE_BYTES:raise ValueError('CAD_SOURCE_SIZE_LIMIT')
            digest.update(chunk)
    if digest.hexdigest()!=expected:raise ValueError('CAD_SOURCE_CHANGED')


def run_cad(*,tool,sources,stop,options=None):
    if not _slots.acquire(blocking=False):raise ValueError('CAD_WORKER_BUSY')
    try:return _run_cad(tool=tool,sources=sources,stop=stop,options=options)
    finally:_slots.release()


def _run_cad(*,tool,sources,stop,options=None):
    from .calculation_process import _run_request
    if tool not in ('CAD_INVENTORY','CAD_DIFF'):raise ValueError('CAD_TOOL_NOT_QUALIFIED')
    options={} if options is None else options
    if options!={}:raise ValueError('CAD_OPTIONS_INVALID')
    count=2 if tool=='CAD_DIFF' else 1
    if not isinstance(sources,list) or len(sources)!=count:raise ValueError('CAD_SOURCE_COUNT_INVALID')
    if stop.is_set():raise ValueError('CAD_CANCELLED')
    with tempfile.TemporaryDirectory(prefix='engineer-cad-') as tmp:
        staged=[]
        for index,(path,sha) in enumerate(sources):
            if Path(path).suffix.lower()!='.dxf':raise ValueError('DXF_ORIGINAL_REQUIRED')
            _checked_hash(path,sha);target=Path(tmp)/f'source-{index}.dxf'
            total=0;digest=hashlib.sha256()
            with Path(path).open('rb') as stream,target.open('xb') as output:
                while chunk:=stream.read(1024**2):
                    if stop.is_set():raise ValueError('CAD_CANCELLED')
                    total+=len(chunk)
                    if total>MAX_SOURCE_BYTES:raise ValueError('CAD_SOURCE_SIZE_LIMIT')
                    digest.update(chunk);output.write(chunk)
            if digest.hexdigest()!=sha:raise ValueError('CAD_SOURCE_CHANGED')
            staged.append(dict(path=str(target),sha256=sha))
        data=dict(sources=staged,options=options)
        result=_run_request(tool,data,stop,timeout_seconds=30)
        for path,sha in sources:_checked_hash(path,sha)
        return result


def evaluate_staged(tool,data):
    """Parse only inside the shared memory/time/output boundary."""
    sources=data['sources']
    for source in sources:_checked_hash(source['path'],source['sha256'])
    if tool=='CAD_INVENTORY':
        from engineering.cad.dxf_workflow import inventory_dxf,_load
        source=sources[0];result=inventory_dxf(source['path'],source['sha256'])
        if result.get('format')=='DXF' and 'entity_counts' in result:
            from itertools import islice
            doc,_=_load(source['path'],source['sha256'],inventory=True)
            result['entities']=[dict(handle=e.dxf.handle,type=e.dxftype(),layer=e.dxf.layer[:250]) for e in islice(doc.modelspace(),100)]
            result['entities_truncated']=len(doc.modelspace())>100
    elif tool=='CAD_DIFF':
        from engineering.cad.roundtrip import compare_dxf
        result=compare_dxf(sources[0]['path'],sources[1]['path'],source_sha256=sources[0]['sha256'])
    else:raise ValueError('CAD_TOOL_NOT_QUALIFIED')
    for source in sources:_checked_hash(source['path'],source['sha256'])
    result.update(data_class='PROJECT',acceptance_granted=False,actual_structure_verified=False,dwg_equivalence_verified=False)
    return result

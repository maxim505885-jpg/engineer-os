"""Bounded source staging for disposable IFC declaration workers.

Resource containment reuses the calculator boundary. No network isolation,
geometry qualification, engineering acceptance or actual-condition claim.
"""
import hashlib
from pathlib import Path
import re
import tempfile

MAX_SOURCE_BYTES=50*1024**2


def _checked_hash(path,expected):
    if not isinstance(expected,str) or re.fullmatch('[0-9a-f]{64}',expected) is None:
        raise ValueError('IFC_SOURCE_IDENTITY_INVALID')
    path=Path(path)
    if not path.is_file() or not 0<path.stat().st_size<=MAX_SOURCE_BYTES:
        raise ValueError('IFC_SOURCE_SIZE_LIMIT')
    digest=hashlib.sha256();total=0
    with path.open('rb') as stream:
        while chunk:=stream.read(min(1024**2,MAX_SOURCE_BYTES-total+1)):
            total+=len(chunk)
            if total>MAX_SOURCE_BYTES:raise ValueError('IFC_SOURCE_SIZE_LIMIT')
            digest.update(chunk)
    if digest.hexdigest()!=expected:raise ValueError('IFC_SOURCE_CHANGED')


def run_ifc(*,tool,sources,stop):
    from .calculation_process import _run_request
    if tool not in ('IFC_INVENTORY','IFC_DIFF'):raise ValueError('IFC_TOOL_NOT_QUALIFIED')
    count=2 if tool=='IFC_DIFF' else 1
    if not isinstance(sources,list) or len(sources)!=count:raise ValueError('IFC_SOURCE_COUNT_INVALID')
    if stop.is_set():raise ValueError('IFC_CANCELLED')
    with tempfile.TemporaryDirectory(prefix='engineer-ifc-') as tmp:
        staged=[]
        for index,(path,sha) in enumerate(sources):
            _checked_hash(path,sha);target=Path(tmp)/f'source-{index}.ifc'
            total=0;digest=hashlib.sha256()
            with Path(path).open('rb') as stream,target.open('xb') as output:
                while chunk:=stream.read(1024**2):
                    if stop.is_set():raise ValueError('IFC_CANCELLED')
                    total+=len(chunk)
                    if total>MAX_SOURCE_BYTES:raise ValueError('IFC_SOURCE_SIZE_LIMIT')
                    digest.update(chunk);output.write(chunk)
            if digest.hexdigest()!=sha:raise ValueError('IFC_SOURCE_CHANGED')
            staged.append(dict(path=str(target),sha256=sha))
        result=_run_request(tool,dict(sources=staged),stop)
        for path,sha in sources:_checked_hash(path,sha)
        return result


def evaluate_staged(tool,data):
    """Only called inside the already limited disposable child."""
    sources=data['sources']
    for source in sources:_checked_hash(source['path'],source['sha256'])
    if tool=='IFC_INVENTORY':
        from engineering.bim.ifc_adapter import inspect_ifc
        return inspect_ifc(sources[0]['path'],expected_sha256=sources[0]['sha256'])
    from engineering.bim.ifc_adapter import compare_ifc
    return compare_ifc(sources[0]['path'],sources[1]['path'],source_sha256=sources[0]['sha256'])

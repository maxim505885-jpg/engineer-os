"""Derived Office PDF via qualified local bundle and owned runtime boundary.

Results remain unverified. This adapter neither accepts document contents nor
silently falls back to host Office or a network service.
"""
import hashlib
import json
from pathlib import Path
import re
import tempfile
import threading
from runtime.office_bundle import verify_bundle,BundleError
from runtime.windows_contained_process import run_contained,ContainmentError
from engineering.document_intelligence.office_render_protocol import decode_render_result,MAX_SERIAL_BYTES

MAX_SOURCE=64*1024**2
_slots=threading.BoundedSemaphore(1)
class OfficeRenderError(ValueError):pass

def _cancel(stop):
    if stop.is_set():raise OfficeRenderError('OFFICE_CANCELLED')

def _copy_checked(source,target,expected,maximum,stop):
    digest=hashlib.sha256();total=0
    with Path(source).open('rb') as src,Path(target).open('xb') as dst:
        while chunk:=src.read(1024**2):
            _cancel(stop);total+=len(chunk)
            if total>maximum:raise OfficeRenderError('OFFICE_COPY_SIZE_LIMIT')
            digest.update(chunk);dst.write(chunk)
    if not total or digest.hexdigest()!=expected:raise OfficeRenderError('OFFICE_SOURCE_OR_BUNDLE_CHANGED')

def _source_hash(path,stop):
    path=Path(path)
    for item in (path,*path.parents):
        if item.is_symlink() or item.is_junction():raise OfficeRenderError('OFFICE_SOURCE_LINK')
    if not path.is_file() or not 0<path.stat().st_size<=MAX_SOURCE:raise OfficeRenderError('OFFICE_SOURCE_SIZE_LIMIT')
    digest=hashlib.sha256();total=0
    with path.open('rb') as stream:
        while chunk:=stream.read(1024**2):
            _cancel(stop);total+=len(chunk)
            if total>MAX_SOURCE:raise OfficeRenderError('OFFICE_SOURCE_SIZE_LIMIT')
            digest.update(chunk)
    return digest.hexdigest()

def _file_option(path):
    # Windows extended path avoids QEMU's inaccessible volume-alignment probe.
    return (chr(92)*2+'?'+chr(92)+str(path)).replace(',',',,')

def render_office(source,expected_sha256,suffix,*,bundle_root,manifest_sha256,stop):
    if not isinstance(expected_sha256,str) or not re.fullmatch('[0-9a-f]{64}',expected_sha256):raise OfficeRenderError('OFFICE_SOURCE_IDENTITY_INVALID')
    if suffix not in ('.doc','.docx','.rtf'):raise OfficeRenderError('OFFICE_FORMAT_UNSUPPORTED')
    _cancel(stop)
    if not _slots.acquire(blocking=False):raise OfficeRenderError('OFFICE_RENDER_BUSY')
    try:
        if _source_hash(source,stop)!=expected_sha256:raise OfficeRenderError('OFFICE_SOURCE_CHANGED')
        bundle=verify_bundle(bundle_root,manifest_sha256,stop=stop)
        with tempfile.TemporaryDirectory(prefix='engineer-office-render-') as temp:
            stage=Path(temp).resolve();(stage/'out').mkdir()
            staged=stage/('source'+suffix)
            _copy_checked(source,staged,expected_sha256,MAX_SOURCE,stop)
            image=stage/'worker.qcow2';seed=stage/'seed.iso'
            _copy_checked(bundle['image'],image,bundle['files']['worker.qcow2'],2*1024**3,stop)
            _copy_checked(bundle['seed'],seed,bundle['files']['worker-seed.iso'],2*1024**3,stop)
            request=stage/'request.json';request.write_text(json.dumps(dict(schema=1,source_sha256=expected_sha256,suffix=suffix)),encoding='ascii')
            engine=bundle['engine']
            command=[str(engine/'qemu-system-x86_64.exe'),'-L',str(engine/'share'),'-machine','pc',
                     '-accel','tcg,thread=multi','-smp','2','-m','768','-display','none','-monitor','none',
                     '-serial','file:'+str(stage/'out/serial.log'),'-serial','file:'+str(stage/'out/results.log'),
                     '-nic','none','-no-reboot','-drive','file='+_file_option(image)+',format=qcow2,if=virtio',
                     '-drive','file='+_file_option(seed)+',format=raw,media=cdrom,readonly=on',
                     '-fw_cfg','name=opt/eos/input,file='+str(staged).replace(',',',,'),
                     '-fw_cfg','name=opt/eos/request,file='+str(request).replace(',',',,')]
            process=run_contained(command,engine,stage,stop=stop,timeout_seconds=300,output_limit=MAX_SERIAL_BYTES)
            _cancel(stop)
            if process['reason']!='EXITED' or process['exit_code']!=0:raise OfficeRenderError('OFFICE_WORKER_'+process['reason'])
            with (stage/'out/results.log').open('rb') as stream:raw=stream.read(MAX_SERIAL_BYTES+1)
            if len(raw)>MAX_SERIAL_BYTES:raise OfficeRenderError('OFFICE_OUTPUT_LIMIT')
            observed=process['outputs'].get('out/results.log')
            if observed!=dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()):raise OfficeRenderError('OFFICE_RESULT_CHANGED')
            pdf,lineage=decode_render_result(raw,expected_sha256)
            if _source_hash(staged,stop)!=expected_sha256 or _source_hash(source,stop)!=expected_sha256:raise OfficeRenderError('OFFICE_SOURCE_CHANGED')
            verify_bundle(bundle_root,manifest_sha256,stop=stop)
            _cancel(stop)
            lineage.update(bundle_manifest_sha256=manifest_sha256,guest_worker_sha256=bundle['guest_worker_sha256'],process=process,
                           source_equivalence='NOT_VERIFIED',font_and_layout_equivalence='NOT_VERIFIED')
            return pdf,lineage
    except (OSError,ValueError,ContainmentError) as exc:
        if isinstance(exc,OfficeRenderError):raise
        raise OfficeRenderError(str(exc)) from exc
    finally:_slots.release()


def renderer_config(store):
    """Local operator configuration, never supplied by a document/API request."""
    path=store.root/'office-renderer.json'
    try:
        if path.is_symlink() or path.is_junction():raise OfficeRenderError('OFFICE_CONFIG_LINK')
        with path.open('rb') as stream:raw=stream.read(4097)
        if len(raw)>4096:raise OfficeRenderError('OFFICE_CONFIG_LIMIT')
        value=json.loads(raw)
        if not isinstance(value,dict) or set(value)!={'bundle_root','manifest_sha256'}:raise OfficeRenderError('OFFICE_CONFIG_INVALID')
        if not isinstance(value['bundle_root'],str) or not Path(value['bundle_root']).is_absolute():raise OfficeRenderError('OFFICE_CONFIG_INVALID')
        if not isinstance(value['manifest_sha256'],str) or not re.fullmatch('[0-9a-f]{64}',value['manifest_sha256']):raise OfficeRenderError('OFFICE_CONFIG_INVALID')
        return value
    except (OSError,ValueError,RecursionError) as exc:raise OfficeRenderError('OFFICE_RENDERER_NOT_CONFIGURED') from exc

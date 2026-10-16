"""Explicit optional ODA conversion; output is evidence, never DWG acceptance.

Converter operates only on a staged byte copy, with audit/repair disabled.
An existing destination is never reused. No automatic installation or discovery.
"""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

from .intake import inspect_cad, MAX_BYTES
from .dxf_workflow import inventory_dxf


def _bounded_hash(path):
    """Hash within the existing CAD byte budget and reject changing files."""
    before=path.stat()
    if not path.is_file() or not 0<before.st_size<=MAX_BYTES:
        raise ValueError('CAD_FILE_SIZE_LIMIT')
    digest=hashlib.sha256();total=0
    with path.open('rb') as stream:
        while chunk:=stream.read(min(1024**2,MAX_BYTES-total+1)):
            total+=len(chunk)
            if total>MAX_BYTES:raise ValueError('CAD_FILE_SIZE_LIMIT')
            digest.update(chunk)
    after=path.stat()
    if total!=before.st_size or (before.st_size,before.st_mtime_ns,before.st_ino)!=(after.st_size,after.st_mtime_ns,after.st_ino):
        raise ValueError('CAD_FILE_CHANGED')
    return digest.hexdigest()


def convert_dwg(source, destination, *, converter, source_sha256, timeout=120):
    source=Path(source).resolve();destination=Path(destination).resolve()
    converter=Path(converter).resolve()
    identity=inspect_cad(source,source_sha256)
    if identity['format']!='DWG' or source.suffix.lower()!='.dwg':
        raise ValueError('DWG source required')
    if not converter.is_file():raise ValueError('Explicit installed converter required')
    if not 0<timeout<=600:raise ValueError('Timeout must be 1–600 seconds')
    destination.mkdir(parents=True,exist_ok=False)
    staged=destination/'input';output=destination/'output'
    staged.mkdir();output.mkdir()
    copy=staged/'source.dwg';shutil.copyfile(source,copy)
    if _bounded_hash(copy)!=source_sha256:
        raise ValueError('Staged source identity mismatch')
    command=[str(converter),str(staged),str(output),'ACAD2018','DXF','0','0',copy.name]
    report=dict(status='BLOCK',conversion_status='BLOCK',source_sha256=source_sha256,
                source_size=identity['size'],source_version=identity['version'],
                converter_sha256=hashlib.sha256(converter.read_bytes()).hexdigest(),
                command=command,repair_enabled=False,dwg_equivalence_verified=False,
                acceptance_granted=False,engineering_verified=False,
                ledger=[dict(code='DWG_SOURCE_CENSUS_UNAVAILABLE',status='BLOCK',
                             source_sha256=source_sha256,
                             detail='Independent source entities/resources/geometry census not provided; conversion cannot establish absence of loss.')])
    def entry(code,status,detail):
        report['ledger'].append(dict(code=code,status=status,source_sha256=source_sha256,detail=detail))
    try:
        result=subprocess.run(command,capture_output=True,timeout=timeout,check=False,
                              creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        report['returncode']=result.returncode
        def decode(value):return value.decode('utf-8',errors='replace') if isinstance(value,bytes) else (value or '')
        stdout=decode(result.stdout);stderr=decode(result.stderr)
        (destination/'stdout.log').write_text(stdout,encoding='utf-8')
        (destination/'stderr.log').write_text(stderr,encoding='utf-8')
        if stdout or stderr:entry('CONVERTER_DIAGNOSTICS','WARNING','Review stdout.log and stderr.log; diagnostics are not evidence of completeness.')
        derivative=output/'source.dxf'
        if result.returncode!=0:entry('CONVERTER_NONZERO_EXIT','BLOCK',str(result.returncode))
        elif not derivative.is_file():entry('CONVERTER_OUTPUT_MISSING','BLOCK','No expected DXF')
        else:
            try:
                report['output_sha256']=_bounded_hash(derivative)
            except ValueError as exc:
                report['inventory']=dict(status='BLOCK',reasons=[str(exc)])
                entry('CONVERTER_OUTPUT_UNREADABLE','BLOCK','Derived DXF exceeds size limit or changed during hashing')
            else:
                try:report['inventory']=inventory_dxf(derivative,report['output_sha256'])
                except ValueError as exc:report['inventory']=dict(status='BLOCK',reasons=[str(exc)])
                with derivative.open('rb') as stream:
                    stream.seek(max(0,derivative.stat().st_size-256))
                    tail=[line.strip() for line in stream.read(256).splitlines()]
                complete=tail[-2:]==[b'0',b'EOF']
                if not complete:entry('CONVERTER_OUTPUT_INCOMPLETE','BLOCK','ASCII DXF terminal EOF record missing; file may be truncated')
                try:unchanged=_bounded_hash(derivative)==report['output_sha256']
                except (OSError,ValueError):unchanged=False
                if not unchanged:entry('CONVERTER_OUTPUT_CHANGED','BLOCK','Derived DXF identity differs after inventory')
                if complete and unchanged and report['inventory'].get('inventory_read_complete'):
                    report['conversion_status']='PASS'
                    for reason in report['inventory'].get('reasons',[]):entry(reason,'BLOCK','Derived DXF inventory limitation')
                else:entry('CONVERTER_OUTPUT_UNREADABLE','BLOCK','Derived DXF inventory unavailable or changed')
    except subprocess.TimeoutExpired:
        entry('CONVERTER_TIMEOUT','BLOCK','Converter exceeded configured timeout')
    except OSError as exc:
        entry('CONVERTER_EXECUTION_FAILED','BLOCK',type(exc).__name__)
    finally:
        try:report['source_unchanged']=_bounded_hash(source)==source_sha256
        except (OSError,ValueError):report['source_unchanged']=False
        if not report['source_unchanged']:
            report['conversion_status']='BLOCK';entry('SOURCE_CHANGED','BLOCK','Source identity differs after conversion')
        (destination/'conversion.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    return report



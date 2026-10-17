"""Local capability inventory. Inventory never promotes package presence to READY.

Fresh probes are a separate explicit CLI action; their JSON is diagnostic, not an
authority record and must never be consumed as engineering verification.
"""
import hashlib
import importlib.metadata
import os
from pathlib import Path
import shutil
import sys
import json
import subprocess
import tempfile


def package_version(name):
    try:return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:return None


def find_tesseract():
    configured=os.environ.get('ENGINEER_OS_TESSERACT_BIN')
    if configured:
        candidate=Path(configured)
        return candidate.resolve() if candidate.is_absolute() and candidate.is_file() else None
    found=shutil.which('tesseract')
    candidates=([Path(found)] if found else [])+[Path(os.environ[key])/'Tesseract-OCR/tesseract.exe' for key in ('ProgramFiles','ProgramFiles(x86)') if os.environ.get(key)]
    return next((p.resolve() for p in candidates if p.is_absolute() and p.is_file()),None)


def _sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def capability_report(profile='native'):
    if profile not in ('native','engineering'):raise ValueError('PROFILE_NOT_SUPPORTED')
    capabilities={}
    for key,package,scope in (
        ('pdf','PyMuPDF','CONTROLLED_PDF_TEXT_AND_RASTER'),
        ('tables','docling','LOCAL_MODEL_CONFIGURATION_REQUIRED'),
        ('ifc','ifcopenshell','SYNTHETIC_DECLARATION_INTAKE_ONLY'),
        ('beam','PyniteFEA','SIMPLY_SUPPORTED_UDL_LINEAR_BENCHMARK')):
        version=package_version(package)
        capabilities[key]=dict(installed=version is not None,configured=version is not None and key!='tables',
            version=version,probe_status='NOT_RUN',ready=False,artifact_hashes={},limitations=[scope])
    from .ocr import identity
    ocr=identity()
    capabilities['ocr']=dict(installed=find_tesseract() is not None,configured=ocr['available'],
        version=None,probe_status='NOT_RUN',ready=False,artifact_hashes={k:ocr[k] for k in ('binary_sha256','languages') if k in ocr},
        limitations=['RECOGNIZED_TEXT_IS_UNVERIFIED_CANDIDATE'])
    from .doc_conversion import converter_identity
    office=converter_identity()
    capabilities['office']=dict(installed=office['available'],configured=office['available'] and sys.platform=='linux',
        version=None,probe_status='NOT_RUN',ready=False,artifact_hashes={'executable_sha256':office['executable_sha256']},
        limitations=['WINDOWS_SOURCE_RENDER_ISOLATION_NOT_QUALIFIED','PASSIVE_FORMULA_PREVIEW_DOES_NOT_VERIFY_SOURCE_LAYOUT'])
    return dict(schema='ENGINEER_OS_CAPABILITY_INVENTORY_V1',profile=profile,python=sys.version.split()[0],
        interpreter_sha256=_sha(sys.executable),adapter_sha256=_sha(__file__),capabilities=capabilities,
        network_policy='NO_DOWNLOADS',execution_verified=False,acceptance_granted=False,
        base_start_allowed=True,status='UNCERTAINTY',scope='DIAGNOSTIC_INVENTORY_NOT_AUTHORITY')


def probe_capability(name,*,timeout=60):
    if name not in ('pdf','ocr','ifc','beam','tables','office'):raise ValueError('PROBE_NOT_SUPPORTED')
    if type(timeout) is not int or not 1<=timeout<=120:raise ValueError('PROBE_TIMEOUT_INVALID')
    base=dict(probe_status='BLOCK',ready=False,acceptance_granted=False,
        scope='FIXED_SYNTHETIC_PROBE_ONLY',network_isolation_verified=False,reasons=[])
    if name in ('office','tables'):
        return dict(base,reasons=['WINDOWS_SOURCE_RENDER_ISOLATION_NOT_QUALIFIED' if name=='office' else 'OFFLINE_MODEL_PROFILE_NOT_QUALIFIED'])
    environment=dict(os.environ,HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',HF_DATASETS_OFFLINE='1',DO_NOT_TRACK='1')
    root=Path(__file__).resolve().parents[2]
    environment['PYTHONPATH']=str(root)
    with tempfile.TemporaryFile() as output:
        try:
            child=subprocess.run([sys.executable,'-m','engineering.local_app.profile_probes',name],
                cwd=root,env=environment,stdin=subprocess.DEVNULL,stdout=output,stderr=subprocess.DEVNULL,
                timeout=timeout,check=False)
            output.seek(0);raw=output.read(128*1024+1)
            if child.returncode or len(raw)>128*1024:return dict(base,reasons=['PROBE_EXECUTION_FAILED'])
            value=json.loads(raw)
            if not isinstance(value,dict) or value.get('schema')!='ENGINEER_OS_FIXED_PROBE_V1' or value.get('name')!=name or value.get('passed') is not True:
                return dict(base,reasons=['PROBE_COMPARISON_FAILED'])
            return dict(base,probe_status='PASS',ready=True,receipt=value)
        except subprocess.TimeoutExpired:return dict(base,reasons=['PROBE_TIMEOUT'])
        except (OSError,ValueError):return dict(base,reasons=['PROBE_OUTPUT_INVALID'])

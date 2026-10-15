"""Local derived DOCX. DOC bytes stay immutable and are never executed."""
import hashlib
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile

TIMEOUT=90
MAX_DERIVED=32*1024*1024


def converter_identity():
    executable=os.environ.get('ENGINEER_OS_DOC_CONVERTER') or shutil.which('soffice') or shutil.which('libreoffice')
    path=Path(executable).resolve() if executable else None
    return dict(available=bool(path and path.is_file()),path=str(path) if path else None,
                executable_sha256=hashlib.sha256(path.read_bytes()).hexdigest() if path and path.is_file() else None,
                sandbox_sha256=hashlib.sha256(Path(__file__).with_name('doc_sandbox.py').read_bytes()).hexdigest(),
                adapter_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),platform=sys.platform,
                timeout=TIMEOUT,max_derived=MAX_DERIVED,macros='DISABLED',network='DENIED')


def convert_doc(data):
    from .office import OfficeError
    ident=converter_identity()
    if not data.startswith(b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'):raise OfficeError('DOC requires binary Word original')
    if not ident['available'] or sys.platform!='linux':raise OfficeError('Controlled DOC converter unavailable')
    with tempfile.TemporaryDirectory(prefix='engineer-doc-') as temp:
        root=Path(temp);profile=root/'profile';profile.mkdir();out=root/'out';out.mkdir();source=root/'source.doc';source.write_bytes(data)
        registry='''<?xml version="1.0" encoding="UTF-8"?><oor:items xmlns:oor="http://openoffice.org/2001/registry"><item oor:path="/org.openoffice.Office.Common/Security/Scripting"><prop oor:name="MacroSecurityLevel" oor:op="fuse"><value>3</value></prop></item><item oor:path="/org.openoffice.Office.Writer/Content/Update"><prop oor:name="Link" oor:op="fuse"><value>2</value></prop></item></oor:items>'''
        (profile/'registrymodifications.xcu').write_text(registry)
        runner=Path(__file__).with_name('doc_sandbox.py')
        command=[sys.executable,str(runner),ident['path'],'-env:UserInstallation='+profile.as_uri(),'--headless','--nologo','--nodefault','--nofirststartwizard','--norestore','--convert-to','docx:Office Open XML Text','--outdir',str(out),str(source)]
        with (root/'converter.log').open('wb') as log:
            process=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,cwd=root)
            try:code=process.wait(timeout=TIMEOUT)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid,signal.SIGKILL);process.wait();raise OfficeError('DOC conversion timeout') from None
        target=out/'source.docx'
        if code!=0 or not target.is_file() or not 0<target.stat().st_size<=MAX_DERIVED:raise OfficeError('DOC conversion failed')
        derived=target.read_bytes()
        return derived,dict(original_sha256=hashlib.sha256(data).hexdigest(),derived_sha256=hashlib.sha256(derived).hexdigest(),
                            converter=ident,scope='DERIVED_UNVERIFIED',network_denied=True,macros_disabled=True,acceptance_granted=False)

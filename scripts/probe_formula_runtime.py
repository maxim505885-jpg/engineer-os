"""Development-only distro startup probe using a fixed benign formula fixture.

Never accepts source paths or user documents. Unsandboxed reference is only a
control experiment, never production extraction or a network-denial claim.
"""
import hashlib,json,os,signal,subprocess,sys,tempfile,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from engineering.local_app.word_formula_preview import _scaffold,_converter
from tests.test_word_formula_preview import document

def main():
    converter=_converter()
    if converter is None:raise SystemExit('Converter unavailable')
    scaffold,_=_scaffold(document('<m:oMath><m:f><m:num><m:r><m:t>1</m:t></m:r></m:num><m:den><m:r><m:t>2</m:t></m:r></m:den></m:f></m:oMath>'),'word/document.xml',0)
    binary=converter.parent/'soffice.bin'
    cases=[('launcher-strict',converter,False,3,True),('launcher-svp-strict',converter,True,3,True),
           ('binary-strict',binary,False,3,True),('binary-svp-strict',binary,True,3,True),
           ('launcher-svp-memory6-strict',converter,True,6,True),('launcher-svp-benign-reference',converter,True,3,False)]
    for label,exe,svp,memory,sandbox in cases:
        if not exe.is_file():continue
        with tempfile.TemporaryDirectory(prefix='formula-startup-probe-') as tmp:
            root=Path(tmp);profile=root/'profile';profile.mkdir();out=root/'out';out.mkdir()
            source=root/'formula.docx';source.write_bytes(scaffold)
            command=[str(exe),'-env:UserInstallation='+profile.as_uri(),'--headless','--nologo','--nodefault','--nofirststartwizard','--norestore','--convert-to','pdf:writer_pdf_Export','--outdir',str(out),str(source)]
            env=dict(os.environ,PYTHONPATH=str(ROOT))
            if svp:env['SAL_USE_VCLPLUGIN']='svp'
            if sandbox:
                code="import os,resource,sys;original=resource.setrlimit;resource.setrlimit=lambda which,limits:original(which,("+str(memory)+"*1024**3,"+str(memory)+"*1024**3) if which==resource.RLIMIT_AS else limits);from engineering.local_app.doc_sandbox import apply;apply();os.execv(sys.argv[1],sys.argv[1:])"
                command=[sys.executable,'-c',code]+command
            log=root/'startup.log';timed_out=False
            trace=root/'socket.trace'
            if shutil.which('strace'):
                command=[shutil.which('strace'),'-f','-e','trace=socket,connect,sendto,sendmsg,io_uring_setup','-o',str(trace)]+command
            with log.open('wb') as stream:
                child=subprocess.Popen(command,cwd=root,env=env,stdin=subprocess.DEVNULL,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
                try:child.wait(timeout=15)
                except subprocess.TimeoutExpired:timed_out=True
                finally:
                    try:os.killpg(child.pid,signal.SIGKILL)
                    except ProcessLookupError:pass
                    child.wait()
            pdf=out/'formula.pdf'
            text=log.read_bytes()[-2048:].decode(errors='replace')
            print(json.dumps(dict(case=label,exit_code=child.returncode,timed_out=timed_out,network_denied=sandbox,
                executable=str(exe),pdf_bytes=pdf.stat().st_size if pdf.is_file() else 0,
                pdf_sha256=hashlib.sha256(pdf.read_bytes()).hexdigest() if pdf.is_file() else None,log=text,
                socket_trace=trace.read_text(errors='replace')[-4096:] if trace.is_file() else None)),flush=True)

if __name__=='__main__':main()

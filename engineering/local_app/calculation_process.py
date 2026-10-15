"""Disposable calculator with wall time, output and native memory limits.

Receives fixed calculation JSON or staged IFC copies, never original project paths.
This is a resource boundary, not a network or hostile-code sandbox.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

MEMORY_BYTES=2*1024**3
MAX_OUTPUT=2*1024**2
TIMEOUT=120


def run_calculation(tool,data,stop):
    if tool not in ('BEAM','PLANAR'):raise ValueError('CALCULATOR_NOT_SUPPORTED')
    return _run_request(tool,data,stop)


def probe_memory_limit(stop):
    """Fixed 64 MiB committed allocation; never exposed as an engineering tool.

    Module imports need not exhaust a small commit limit on every machine.
    This same workload must succeed normally and fail under a 16 MiB boundary.
    """
    return _run_request('MEMORY_PROBE',{},stop)


def _run_request(tool,data,stop):
    if tool not in ('BEAM','PLANAR','IFC_INVENTORY','IFC_DIFF','MEMORY_PROBE'):raise ValueError('RESOURCE_TOOL_NOT_SUPPORTED')
    if stop.is_set():raise ValueError('CALCULATION_CANCELLED')
    root=Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix='engineer-calculation-') as tmp:
        folder=Path(tmp);source=folder/'request.json';target=folder/'result.json'
        source.write_text(json.dumps(dict(tool=tool,data=data),allow_nan=False),encoding='utf-8')
        command=[sys.executable,'-m','engineering.local_app.calculation_process',str(source),str(target),str(MEMORY_BYTES),str(TIMEOUT)]
        environment=dict(os.environ,PYTHONPATH=str(root),OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1')
        started=time.monotonic();process=None;job=None;thread=None;child=None
        try:
            if os.name=='nt':
                import win32api,win32event,win32job,win32process
                job=win32job.CreateJobObject(None,'')
                limits=win32job.QueryInformationJobObject(job,win32job.JobObjectExtendedLimitInformation)
                limits['BasicLimitInformation']['LimitFlags']=(win32job.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE|win32job.JOB_OBJECT_LIMIT_PROCESS_MEMORY|win32job.JOB_OBJECT_LIMIT_JOB_MEMORY|win32job.JOB_OBJECT_LIMIT_ACTIVE_PROCESS)
                # Windows venv python.exe redirects through a launcher process.
                limits['BasicLimitInformation']['ActiveProcessLimit']=2
                limits['ProcessMemoryLimit']=MEMORY_BYTES
                limits['JobMemoryLimit']=MEMORY_BYTES
                win32job.SetInformationJobObject(job,win32job.JobObjectExtendedLimitInformation,limits)
                startup=win32process.STARTUPINFO()
                process,thread,_,_=win32process.CreateProcess(None,subprocess.list2cmdline(command),None,None,False,
                    win32process.CREATE_SUSPENDED|win32process.CREATE_NO_WINDOW,environment,str(root),startup)
                win32job.AssignProcessToJobObject(job,process)
                win32process.ResumeThread(thread);thread.Close();thread=None
                def finished():return win32event.WaitForSingleObject(process,50)==win32event.WAIT_OBJECT_0
                def exitcode():return win32process.GetExitCodeProcess(process)
            else:
                child=subprocess.Popen(command,cwd=root,env=environment,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True)
                def finished():return child.poll() is not None
                def exitcode():return child.returncode
            while not finished():
                if stop.is_set():raise ValueError('CALCULATION_CANCELLED')
                if time.monotonic()-started>TIMEOUT:raise ValueError('CALCULATION_TIMEOUT')
                if target.exists() and target.stat().st_size>MAX_OUTPUT:raise ValueError('CALCULATION_OUTPUT_LIMIT')
                time.sleep(.02)
            if exitcode()!=0 or not target.is_file() or target.stat().st_size>MAX_OUTPUT:raise ValueError('CALCULATION_CHILD_FAILED')
            def reject_constant(value):raise ValueError('CALCULATION_NONFINITE_OUTPUT')
            value=json.loads(target.read_text(encoding='utf-8'),parse_constant=reject_constant)
            if not isinstance(value,dict) or value.get('acceptance_granted') is not False:raise ValueError('CALCULATION_RECEIPT_INVALID')
            value['resource_boundary']=dict(memory_bytes=MEMORY_BYTES,timeout_seconds=TIMEOUT,output_bytes=MAX_OUTPUT,
                child_isolated=True,network_isolation_verified=False)
            return value
        except ImportError:raise ValueError('WINDOWS_CALCULATION_JOB_BOUNDARY_UNAVAILABLE') from None
        finally:
            if os.name=='nt':
                if process is not None:
                    try:win32process.TerminateProcess(process,1)
                    except Exception:pass
                if thread is not None:thread.Close()
                if job is not None:job.Close()
                if process is not None:process.Close()
            elif child is not None:
                if child.poll() is None:child.kill()
                child.wait()


def main():
    source,target=map(Path,sys.argv[1:3])
    memory,seconds=map(int,sys.argv[3:5])
    if not 1<=memory<=MEMORY_BYTES or not 1<=seconds<=TIMEOUT:raise ValueError('RESOURCE_LIMIT_INVALID')
    if os.name!='nt':
        import resource
        resource.setrlimit(resource.RLIMIT_AS,(memory,memory))
        resource.setrlimit(resource.RLIMIT_CPU,(seconds,seconds))
    if source.stat().st_size>70000:raise ValueError('CALCULATION_REQUEST_LIMIT')
    request=json.loads(source.read_text(encoding='utf-8'));tool=request['tool'];data=request['data']
    if tool in ('BEAM','PLANAR'):data['evidence_ids']=tuple(data['evidence_ids'])
    if tool=='BEAM':
        from engineering.calculation.control_beam import BeamInput,calculate_beam
        result=calculate_beam(BeamInput(**data))
    elif tool=='PLANAR':
        from engineering.calculation.planar_control import PlanarInput,Node,Member,calculate_planar
        data.update(nodes=tuple(Node(**n) for n in data['nodes']),members=tuple(Member(**m) for m in data['members']),loads=tuple(tuple(load) for load in data['loads']))
        result=calculate_planar(PlanarInput(**data))
    elif tool=='MEMORY_PROBE':
        if data!={}:raise ValueError('FIXED_MEMORY_PROBE_REQUIRED')
        allocation=bytearray(64*1024**2)
        for index in range(0,len(allocation),4096):allocation[index]=1
        result=dict(status='PASS',scope='FIXED_MEMORY_ALLOCATION_PROBE_ONLY',
                    allocated_bytes=len(allocation),acceptance_granted=False)
    elif tool in ('IFC_INVENTORY','IFC_DIFF'):
        from .ifc_process import evaluate_staged
        result=evaluate_staged(tool,data)
    else:raise ValueError('CALCULATOR_NOT_SUPPORTED')
    raw=json.dumps(result,ensure_ascii=False,allow_nan=False)
    if len(raw.encode('utf-8'))>MAX_OUTPUT:raise ValueError('CALCULATION_OUTPUT_LIMIT')
    target.write_text(raw,encoding='utf-8')


if __name__=='__main__':main()

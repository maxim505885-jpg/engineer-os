"""Owned Windows AppContainer process with zero capabilities and bounded lifetime.

Trusted callers construct the command and private staging directory. This is a
runtime primitive, not a document or engineering acceptance gate. Runtime must
already be hash-qualified; OS system files remain available under Windows ACLs.
"""
import ctypes as C
from ctypes import wintypes as W
import hashlib
import os
from pathlib import Path, PurePosixPath
import subprocess
import sys
import time
import uuid
from types import SimpleNamespace

class ContainmentError(RuntimeError):
    pass

def _no_links(path):
    for item in (path, *path.parents):
        if item.is_symlink() or item.is_junction():
            raise ContainmentError("Reparse paths are not supported")

def validate_launch(command, runtime_dir, staging_dir, timeout_seconds, output_limit, output_paths):
    if not isinstance(command, (list, tuple)) or not 1 <= len(command) <= 64:
        raise ContainmentError("Invalid command")
    if any(not isinstance(arg, str) or not arg or len(arg) > 8192 or "\0" in arg for arg in command):
        raise ContainmentError("Invalid command argument")
    if sum(len(arg) for arg in command) > 30000:
        raise ContainmentError("Command size limit")
    exe, engine, stage = Path(command[0]), Path(runtime_dir), Path(staging_dir)
    for path in (exe, engine, stage):
        if not path.is_absolute(): raise ContainmentError("Absolute paths required")
        _no_links(path)
    exe, engine, stage = exe.resolve(), engine.resolve(), stage.resolve()
    if not exe.is_file() or not engine.is_dir() or not stage.is_dir() or not exe.is_relative_to(engine):
        raise ContainmentError("Runtime executable unavailable or outside runtime")
    if engine == Path(engine.anchor) or stage == Path(stage.anchor) or engine.is_relative_to(stage) or stage.is_relative_to(engine):
        raise ContainmentError("Runtime and staging must be disjoint private directories")
    if type(timeout_seconds) not in (int, float) or not 0 < timeout_seconds <= 600:
        raise ContainmentError("Invalid timeout")
    if type(output_limit) is not int or not 0 < output_limit <= 64 * 1024**2:
        raise ContainmentError("Invalid output limit")
    if not isinstance(output_paths, (list, tuple)) or not 1 <= len(output_paths) <= 8:
        raise ContainmentError("Invalid output paths")
    seen = set()
    for name in output_paths:
        if not isinstance(name, str) or not name or len(name) > 256 or "\\" in name or ":" in name or "\0" in name:
            raise ContainmentError("Invalid output path")
        path = PurePosixPath(name)
        if path.is_absolute() or any(part in ("", ".", "..") for part in name.split("/")) or name.casefold() in seen or name.casefold() == "process.log":
            raise ContainmentError("Invalid output path")
        seen.add(name.casefold())
        _no_links(stage / name)
    return exe, engine, stage

def _native_api():
    K=C.WinDLL('kernel32',use_last_error=True);U=C.WinDLL('userenv',use_last_error=True)
    class CAP(C.Structure):_fields_=[('sid',C.c_void_p),('caps',C.c_void_p),('count',W.DWORD),('reserved',W.DWORD)]
    class SI(C.Structure):
     _fields_=[('cb',W.DWORD),('reserved',W.LPWSTR),('desktop',W.LPWSTR),('title',W.LPWSTR),('x',W.DWORD),('y',W.DWORD),('xs',W.DWORD),('ys',W.DWORD),('xc',W.DWORD),('yc',W.DWORD),('fill',W.DWORD),('flags',W.DWORD),('show',W.WORD),('reserved2',W.WORD),('resbytes',C.c_void_p),('stdin',W.HANDLE),('stdout',W.HANDLE),('stderr',W.HANDLE)]
    class SIX(C.Structure):_fields_=[('si',SI),('attrs',C.c_void_p)]
    class PI(C.Structure):_fields_=[('process',W.HANDLE),('thread',W.HANDLE),('pid',W.DWORD),('tid',W.DWORD)]
    U.CreateAppContainerProfile.argtypes=[W.LPCWSTR,W.LPCWSTR,W.LPCWSTR,C.c_void_p,W.DWORD,C.POINTER(C.c_void_p)];U.CreateAppContainerProfile.restype=C.c_long
    U.DeleteAppContainerProfile.argtypes=[W.LPCWSTR];U.DeleteAppContainerProfile.restype=C.c_long
    K.InitializeProcThreadAttributeList.argtypes=[C.c_void_p,W.DWORD,W.DWORD,C.POINTER(C.c_size_t)];K.InitializeProcThreadAttributeList.restype=W.BOOL
    K.UpdateProcThreadAttribute.argtypes=[C.c_void_p,W.DWORD,C.c_size_t,C.c_void_p,C.c_size_t,C.c_void_p,C.c_void_p];K.UpdateProcThreadAttribute.restype=W.BOOL
    K.CreateProcessW.argtypes=[W.LPCWSTR,W.LPWSTR,C.c_void_p,C.c_void_p,W.BOOL,W.DWORD,C.c_void_p,W.LPCWSTR,C.POINTER(SIX),C.POINTER(PI)];K.CreateProcessW.restype=W.BOOL
    for name,args,ret in [('ResumeThread',[W.HANDLE],W.DWORD),('WaitForSingleObject',[W.HANDLE,W.DWORD],W.DWORD),('CloseHandle',[W.HANDLE],W.BOOL),('DeleteProcThreadAttributeList',[C.c_void_p],None),('GetExitCodeProcess',[W.HANDLE,C.POINTER(W.DWORD)],W.BOOL)]:
     fn=getattr(K,name);fn.argtypes=args;fn.restype=ret
    K.TerminateProcess.argtypes=[W.HANDLE,W.UINT];K.TerminateProcess.restype=W.BOOL
    adv=C.WinDLL('advapi32',use_last_error=True)
    adv.GetLengthSid.argtypes=[C.c_void_p];adv.GetLengthSid.restype=W.DWORD
    adv.FreeSid.argtypes=[C.c_void_p];adv.FreeSid.restype=C.c_void_p
    adv.OpenProcessToken.argtypes=[W.HANDLE,W.DWORD,C.POINTER(W.HANDLE)];adv.OpenProcessToken.restype=W.BOOL
    adv.GetTokenInformation.argtypes=[W.HANDLE,C.c_int,C.c_void_p,W.DWORD,C.POINTER(W.DWORD)];adv.GetTokenInformation.restype=W.BOOL
    return SimpleNamespace(K=K,U=U,adv=adv,CAP=CAP,SIX=SIX,PI=PI)

def _check(ok):
    if not ok: raise C.WinError(C.get_last_error())

def _grant(path, sid, mask, flags=3):
    import win32security as security
    sd=security.GetFileSecurity(str(path),security.DACL_SECURITY_INFORMATION)
    dacl=sd.GetSecurityDescriptorDacl()
    if dacl is None: raise ContainmentError("Null DACL unsupported")
    dacl.AddAccessAllowedAceEx(security.ACL_REVISION_DS,flags,mask,sid)
    if flags:
        security.SetNamedSecurityInfo(str(path),security.SE_FILE_OBJECT,security.DACL_SECURITY_INFORMATION,None,None,dacl,None)
    else:
        sd.SetSecurityDescriptorDacl(1,dacl,0)
        security.SetFileSecurity(str(path),security.DACL_SECURITY_INFORMATION,sd)

def _revoke(path,sid,flags):
    import win32security as security
    sd=security.GetFileSecurity(str(path),security.DACL_SECURITY_INFORMATION);dacl=sd.GetSecurityDescriptorDacl()
    if dacl is None: raise ContainmentError("Null DACL during cleanup")
    for index in reversed(range(dacl.GetAceCount())):
        if str(dacl.GetAce(index)[2])==str(sid): dacl.DeleteAce(index)
    if flags: security.SetNamedSecurityInfo(str(path),security.SE_FILE_OBJECT,security.DACL_SECURITY_INFORMATION,None,None,dacl,None)
    else:
        sd.SetSecurityDescriptorDacl(1,dacl,0);security.SetFileSecurity(str(path),security.DACL_SECURITY_INFORMATION,sd)

def _outputs(stage,names,limit,*,hash_files=False):
    result={};total=0
    for name in names:
        path=stage/name;_no_links(path)
        if not path.exists(): continue
        if not path.is_file(): raise ContainmentError("Output is not a regular file")
        size=path.stat().st_size;total+=size
        if total>limit: raise ContainmentError("OUTPUT_LIMIT")
        entry=dict(bytes=size)
        if hash_files:
            with path.open("rb") as stream: data=stream.read(limit+1)
            if len(data)!=size or len(data)>limit: raise ContainmentError("Output changed or grew")
            entry['sha256']=hashlib.sha256(data).hexdigest()
        result[name]=entry
    return result

def _terminate_job(job, api, *, timeout=5):
    api.TerminateJobObject(job,124)
    deadline=time.monotonic()+timeout
    while api.QueryInformationJobObject(job,api.JobObjectBasicAccountingInformation)['ActiveProcesses']:
        if time.monotonic()>=deadline:
            raise ContainmentError('JOB_TERMINATION_UNCONFIRMED')
        time.sleep(0.01)

def run_contained(command,runtime_dir,staging_dir,*,stop,timeout_seconds=300,output_limit=48*1024**2,output_paths=('out/results.log','out/serial.log')):
    exe,engine,stage=validate_launch(command,runtime_dir,staging_dir,timeout_seconds,output_limit,output_paths)
    if sys.platform!='win32': raise ContainmentError("Windows AppContainer required")
    if stop.is_set(): raise ContainmentError("CANCELLED")
    import win32security as security
    import win32job
    import win32con
    import msvcrt
    api=_native_api();K,U,adv=api.K,api.U,api.adv
    name='EngineerOS.Worker.'+uuid.uuid4().hex;sidptr=C.c_void_p();pi=api.PI();job=None;attrs=None;log=None;profile=False;grants=[];cleanup=[];attrs_initialized=False
    receipt=dict(scope='OWNED_PROCESS_ONLY',acceptance_granted=False,reason='NOT_STARTED',exit_code=None)
    try:
        hr=U.CreateAppContainerProfile(name,name,'ENGINEER OS isolated worker',None,0,C.byref(sidptr))
        if hr!=0: raise ContainmentError('CreateAppContainerProfile failed '+hex(hr&0xffffffff))
        profile=True;sid=security.SID(C.string_at(sidptr,adv.GetLengthSid(sidptr)))
        for parent in sorted(set(engine.parents)|set(stage.parents),key=lambda p:len(p.parts)):
            if parent.is_relative_to(Path.home()) and parent!=Path(parent.anchor):
                grants.append((parent,0));_grant(parent,sid,0x80|0x20,0)
        grants.append((engine,3));_grant(engine,sid,win32con.GENERIC_READ|win32con.GENERIC_EXECUTE)
        grants.append((stage,3));_grant(stage,sid,win32con.GENERIC_ALL)
        subprocess.run([str(Path(os.environ['SystemRoot'])/'System32/icacls.exe'),str(stage),'/setintegritylevel','(OI)(CI)L'],check=True,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=subprocess.CREATE_NO_WINDOW)
        log=(stage/'process.log').open('xb');handle=msvcrt.get_osfhandle(log.fileno());os.set_handle_inheritable(handle,True)
        cap=api.CAP(sidptr,None,0,0);size=C.c_size_t();K.InitializeProcThreadAttributeList(None,2,0,C.byref(size));attrs=C.create_string_buffer(size.value);_check(K.InitializeProcThreadAttributeList(attrs,2,0,C.byref(size)));attrs_initialized=True
        _check(K.UpdateProcThreadAttribute(attrs,0,0x20009,C.byref(cap),C.sizeof(cap),None,None))
        handles=(W.HANDLE*1)(handle);_check(K.UpdateProcThreadAttribute(attrs,0,0x20002,handles,C.sizeof(handles),None,None))
        startup=api.SIX();startup.si.cb=C.sizeof(startup);startup.si.flags=0x100;startup.si.stdout=handle;startup.si.stderr=handle;startup.attrs=C.cast(attrs,C.c_void_p)
        env={key:os.environ[key] for key in ('SystemRoot','WINDIR','SystemDrive') if key in os.environ}
        env.update(TEMP=str(stage),TMP=str(stage),USERPROFILE=str(stage),LOCALAPPDATA=str(stage),APPDATA=str(stage))
        block=C.create_unicode_buffer('\0'.join(key+'='+value for key,value in sorted(env.items()))+'\0\0')
        job=win32job.CreateJobObject(None,'');limits=win32job.QueryInformationJobObject(job,win32job.JobObjectExtendedLimitInformation)
        limits['BasicLimitInformation']['LimitFlags']=0x2000|0x100|0x200|0x8;limits['BasicLimitInformation']['ActiveProcessLimit']=4
        limits['ProcessMemoryLimit']=2*1024**3;limits['JobMemoryLimit']=3*1024**3;win32job.SetInformationJobObject(job,win32job.JobObjectExtendedLimitInformation,limits)
        _check(K.CreateProcessW(str(exe),C.create_unicode_buffer(subprocess.list2cmdline(command)),None,None,True,0x80000|0x400|0x4|0x8000000,block,str(stage),C.byref(startup),C.byref(pi)))
        win32job.AssignProcessToJobObject(job,pi.process)
        token=W.HANDLE();_check(adv.OpenProcessToken(pi.process,8,C.byref(token)))
        try:
            flag=W.DWORD();needed=W.DWORD();_check(adv.GetTokenInformation(token,29,C.byref(flag),C.sizeof(flag),C.byref(needed)))
            caps=C.create_string_buffer(1024);_check(adv.GetTokenInformation(token,30,caps,1024,C.byref(needed)))
            count=C.cast(caps,C.POINTER(W.DWORD))[0]
            if flag.value!=1 or count!=0: raise ContainmentError('Unexpected process token')
            receipt.update(appcontainer=1,capability_count=0,pid=pi.pid)
        finally: K.CloseHandle(token)
        if K.ResumeThread(pi.thread)==0xffffffff: raise C.WinError(C.get_last_error())
        started=time.monotonic();reason='EXITED'
        while K.WaitForSingleObject(pi.process,100)==258:
            if stop.is_set(): reason='CANCELLED';break
            if time.monotonic()-started>=timeout_seconds: reason='TIMEOUT';break
            try: _outputs(stage,(*output_paths,'process.log'),output_limit)
            except ContainmentError: reason='OUTPUT_LIMIT';break
        # Terminate all owned descendants even when the main process exited.
        if reason!='EXITED': win32job.TerminateJobObject(job,124)
        _check(K.WaitForSingleObject(pi.process,5000)==0)
        code=W.DWORD();_check(K.GetExitCodeProcess(pi.process,C.byref(code)))
        _terminate_job(job,win32job)
        receipt.update(reason=reason,exit_code=code.value,seconds=round(time.monotonic()-started,3))
    finally:
        if job:
            try: _terminate_job(job,win32job)
            except Exception: cleanup.append('JOB_TERMINATION_UNCONFIRMED')
            finally: job.Close()
        if pi.process:
            if K.WaitForSingleObject(pi.process,0)==258: K.TerminateProcess(pi.process,124);K.WaitForSingleObject(pi.process,5000)
            K.CloseHandle(pi.process)
        if pi.thread: K.CloseHandle(pi.thread)
        if attrs_initialized: K.DeleteProcThreadAttributeList(attrs)
        if log: log.close()
        for path,flags in reversed(grants):
            try: _revoke(path,sid,flags)
            except Exception as exc: cleanup.append(type(exc).__name__)
        if profile and U.DeleteAppContainerProfile(name)!=0: cleanup.append('PROFILE_DELETE_FAILED')
        if sidptr: adv.FreeSid(sidptr)
        if cleanup: raise ContainmentError('Containment cleanup failed: '+','.join(cleanup))
    receipt['outputs']=_outputs(stage,(*output_paths,'process.log'),output_limit,hash_files=True)
    return receipt

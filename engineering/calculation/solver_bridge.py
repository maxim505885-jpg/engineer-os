"""Controlled external solver execution bridge.

The bridge intentionally knows no vendor-specific command-line switches.
A caller must provide a confirmed executable and arguments for its installed
solver version. Execution uses shell=False and produces hash-addressed receipts.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
import subprocess
import time

from .solver_receipt import SolverReceipt
from .execution_identity import SolverExecutionIdentity,command_fingerprint

@dataclass(frozen=True)
class SolverCommand:
    executable:str
    args:tuple[str,...]
    cwd:str
    input_path:str
    output_path:str
    log_path:str
    solver_name:str
    solver_version:str
    timeout_seconds:int=1800

    def __post_init__(self):
        for value in (self.executable,self.cwd,self.input_path,self.output_path,self.log_path,
                      self.solver_name,self.solver_version):
            if not isinstance(value,str) or not value.strip() or len(value)>4000:
                raise ValueError("bounded solver command fields required")
        if not isinstance(self.args,(tuple,list)) or len(self.args)>100 or any(
            not isinstance(x,str) or len(x)>2000 for x in self.args):
            raise ValueError("bounded solver args required")
        if type(self.timeout_seconds) is not int or not 1<=self.timeout_seconds<=86400:
            raise ValueError("bounded solver timeout required")

def _sha(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk=f.read(1024*1024)
            if not chunk:break
            h.update(chunk)
    return h.hexdigest()

def execute_solver(command:SolverCommand)->SolverReceipt:
    if not isinstance(command,SolverCommand):
        raise ValueError("typed solver command required")
    exe=Path(command.executable)
    cwd=Path(command.cwd)
    inp=Path(command.input_path)
    out=Path(command.output_path)
    log=Path(command.log_path)
    if not exe.is_absolute() or not exe.is_file():
        raise ValueError("absolute existing executable required")
    if not cwd.is_absolute() or not cwd.is_dir():
        raise ValueError("absolute existing cwd required")
    for p in (inp,out,log):
        if not p.is_absolute():
            raise ValueError("absolute solver paths required")
    if not inp.is_file():
        raise ValueError("solver input missing")
    try:
        inp.relative_to(cwd);out.relative_to(cwd);log.relative_to(cwd)
    except ValueError as exc:
        raise ValueError("solver files must stay inside cwd") from exc

    # Resolve parent symlinks before containment/alias checks. Each run owns new
    # output/log paths; pre-existing evidence must never be reused or replaced.
    for path in (out,log):
        if path.exists() or path.is_symlink():raise ValueError("solver output/log must not already exist")
    cwd=cwd.resolve();inp=inp.resolve();out=out.resolve();log=log.resolve()
    for path in (inp,out,log):
        try:path.relative_to(cwd)
        except ValueError as exc:raise ValueError("solver files must stay inside resolved cwd") from exc
    if len({inp,out,log})!=3:raise ValueError("solver input/output/log paths must be distinct")
    for path in (out,log):
        if path.exists() or path.is_symlink():raise ValueError("solver output/log must not already exist")
    input_sha=_sha(inp)
    executable_sha=_sha(exe)
    started=time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())
    log.parent.mkdir(parents=True,exist_ok=True)
    # Direct output capture retains diagnostics on timeouts and avoids buffering
    # arbitrary solver output in RAM. Exclusive creation preserves prior logs.
    with log.open('x+b') as stream:
        captured_log_stat=os.fstat(stream.fileno())
        proc=subprocess.run(
            [str(exe),*command.args],cwd=str(cwd),shell=False,
            stdin=subprocess.DEVNULL,stdout=stream,stderr=subprocess.STDOUT,
            timeout=command.timeout_seconds,check=False,
            env={k:os.environ[k] for k in ("SYSTEMROOT","WINDIR","TEMP","TMP","PATH","HOME") if k in os.environ},
        )
        if log.is_symlink() or log.resolve()!=log or not log.is_file():
            raise RuntimeError("solver log path changed during execution")
        current_log_stat=log.stat()
        if (current_log_stat.st_dev,current_log_stat.st_ino)!=(captured_log_stat.st_dev,captured_log_stat.st_ino):
            raise RuntimeError("solver log file was replaced during execution")
        stream.flush();stream.seek(0)
        captured_log_sha=hashlib.file_digest(stream,'sha256').hexdigest()
    finished=time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())
    if not inp.is_file() or _sha(inp)!=input_sha:raise RuntimeError("solver input changed during execution")
    if not exe.is_file() or _sha(exe)!=executable_sha:raise RuntimeError("solver executable changed during execution")
    if out.is_symlink() or out.resolve()!=out or not out.is_file() or out.stat().st_size==0:
        raise RuntimeError("solver did not produce a fresh regular output artifact")
    if out.samefile(inp) or out.samefile(log) or inp.samefile(log):
        raise RuntimeError("solver input/output/log file identities must be distinct")
    return SolverReceipt(
        solver_name=command.solver_name,
        solver_version=command.solver_version,
        input_sha256=input_sha,
        output_sha256=_sha(out),
        log_sha256=captured_log_sha,
        exit_code=proc.returncode,
        started_at=started,
        finished_at=finished,
    )


def execute_solver_with_identity(command:SolverCommand):
    """Execute once and return receipt plus immutable executable/command identity."""
    executable_sha=_sha(Path(command.executable))
    receipt=execute_solver(command)
    if _sha(Path(command.executable))!=executable_sha:
        raise RuntimeError("solver executable changed during execution")
    identity=SolverExecutionIdentity(
        solver_name=command.solver_name,
        solver_version=command.solver_version,
        executable_sha256=executable_sha,
        command_sha256=command_fingerprint(
            solver_name=command.solver_name,
            solver_version=command.solver_version,
            executable_sha256=executable_sha,
            args=command.args,
            timeout_seconds=command.timeout_seconds,
        ),
        input_sha256=receipt.input_sha256,
        output_sha256=receipt.output_sha256,
        log_sha256=receipt.log_sha256,
    )
    return receipt,identity

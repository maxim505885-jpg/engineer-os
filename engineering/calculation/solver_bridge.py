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

    input_sha=_sha(inp)
    started=time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())
    proc=subprocess.run(
        [str(exe),*command.args],
        cwd=str(cwd),
        shell=False,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=command.timeout_seconds,
        check=False,
        env={k:v for k,v in os.environ.items() if k.upper() not in {
            "ENGINEER_OS_LOCAL_MODEL_KEY","OPENAI_API_KEY","SUPABASE_SERVICE_ROLE_KEY"}},
    )
    log.parent.mkdir(parents=True,exist_ok=True)
    log.write_bytes(proc.stdout or b"")
    finished=time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())
    if not out.exists():
        out.write_bytes(b"")
    return SolverReceipt(
        solver_name=command.solver_name,
        solver_version=command.solver_version,
        input_sha256=input_sha,
        output_sha256=_sha(out),
        log_sha256=_sha(log),
        exit_code=proc.returncode,
        started_at=started,
        finished_at=finished,
    )

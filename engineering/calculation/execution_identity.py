"""Immutable identity for a concrete solver execution."""
from __future__ import annotations
from dataclasses import dataclass
import hashlib, json, re
from .solver_receipt import SolverReceipt

_SHA256=re.compile(r"^[0-9a-f]{64}$")

@dataclass(frozen=True)
class SolverExecutionIdentity:
    solver_name:str
    solver_version:str
    executable_sha256:str
    command_sha256:str
    input_sha256:str
    output_sha256:str
    log_sha256:str

    def __post_init__(self):
        for v in (self.solver_name,self.solver_version):
            if not isinstance(v,str) or not v.strip() or len(v)>500:
                raise ValueError("solver identity text required")
        for v in (self.executable_sha256,self.command_sha256,self.input_sha256,self.output_sha256,self.log_sha256):
            if not isinstance(v,str) or not _SHA256.fullmatch(v):
                raise ValueError("solver identity sha256 required")

def command_fingerprint(*,solver_name,solver_version,executable_sha256,args,timeout_seconds):
    if not isinstance(args,(tuple,list)) or any(not isinstance(x,str) for x in args):
        raise ValueError("bounded solver args required")
    payload=dict(solver_name=solver_name,solver_version=solver_version,
                 executable_sha256=executable_sha256,args=list(args),
                 timeout_seconds=timeout_seconds)
    return hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(",",":")).encode()).hexdigest()

def audit_execution_identity(identity:SolverExecutionIdentity,receipt:SolverReceipt)->dict:
    if not isinstance(identity,SolverExecutionIdentity) or not isinstance(receipt,SolverReceipt):
        raise ValueError("typed execution identity and receipt required")
    mismatches=[]
    for name in ("solver_name","solver_version","input_sha256","output_sha256","log_sha256"):
        if getattr(identity,name)!=getattr(receipt,name):mismatches.append(name)
    return dict(status="BLOCK" if mismatches else "READY_FOR_RESULT_INTEGRITY_REVIEW",
                mismatches=mismatches,
                reasons=["SOLVER_EXECUTION_IDENTITY_MISMATCH"] if mismatches else
                        ["EXECUTION_IDENTITY_NOT_ENGINEERING_ACCEPTANCE"],
                acceptance_granted=False)

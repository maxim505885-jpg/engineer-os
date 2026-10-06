"""Fail-closed solver execution receipt contract.

A receipt records identity and output hashes. It does not prove that the solver
was trustworthy, that inputs were semantically correct, or that results match
the real structure.
"""
from __future__ import annotations

from dataclasses import dataclass
import re

_SHA256=re.compile(r"^[0-9a-f]{64}$")

@dataclass(frozen=True)
class SolverReceipt:
    solver_name:str
    solver_version:str
    input_sha256:str
    output_sha256:str
    log_sha256:str
    exit_code:int
    started_at:str
    finished_at:str

    def __post_init__(self):
        for value in (self.solver_name,self.solver_version,self.started_at,self.finished_at):
            if not isinstance(value,str) or not value.strip() or len(value)>500:
                raise ValueError("bounded solver receipt text required")
        for value in (self.input_sha256,self.output_sha256,self.log_sha256):
            if not isinstance(value,str) or not _SHA256.fullmatch(value):
                raise ValueError("solver receipt hashes required")
        if type(self.exit_code) is not int or self.exit_code < -255 or self.exit_code > 255:
            raise ValueError("bounded solver exit code required")

def audit_solver_receipt(receipt:SolverReceipt)->dict:
    if not isinstance(receipt,SolverReceipt):
        raise ValueError("typed solver receipt required")
    if receipt.exit_code!=0:
        return dict(status="BLOCK",reasons=["SOLVER_EXIT_NONZERO"],acceptance_granted=False)
    return dict(status="READY_FOR_RESULT_VERIFICATION",
                reasons=["SOLVER_OUTPUT_NOT_SEMANTICALLY_VERIFIED","ACTUAL_STRUCTURE_CORRELATION_NOT_ACCEPTED"],
                acceptance_granted=False)

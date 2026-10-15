"""Fail-closed verification of solver output/log identity and review completeness."""
from __future__ import annotations
from dataclasses import dataclass
import re
from .solver_receipt import SolverReceipt

_SHA256=re.compile(r"^[0-9a-f]{64}$")
_DECISIONS={"VERIFIED","REJECTED","NOT_VERIFIED"}

@dataclass(frozen=True)
class SolverResultVerification:
    input_sha256:str
    output_sha256:str
    log_sha256:str
    output_source_ref:str
    log_source_ref:str
    completeness:str
    consistency:str
    log_review:str
    critical_findings:tuple[str,...]=()

    def __post_init__(self):
        for v in (self.input_sha256,self.output_sha256,self.log_sha256):
            if not isinstance(v,str) or not _SHA256.fullmatch(v):
                raise ValueError("result verification sha256 required")
        for v in (self.output_source_ref,self.log_source_ref):
            if not isinstance(v,str) or not v.strip() or len(v)>2000:
                raise ValueError("result source refs required")
        for v in (self.completeness,self.consistency,self.log_review):
            if v not in _DECISIONS:raise ValueError("invalid result verification decision")
        if not isinstance(self.critical_findings,(tuple,list)) or len(self.critical_findings)>100 or any(
            not isinstance(x,str) or not x.strip() or len(x)>1000 for x in self.critical_findings):
            raise ValueError("bounded critical findings required")

def audit_solver_results(review:SolverResultVerification,receipt:SolverReceipt)->dict:
    if not isinstance(review,SolverResultVerification) or not isinstance(receipt,SolverReceipt):
        raise ValueError("typed result verification and receipt required")
    mismatches=[name for name in ("input_sha256","output_sha256","log_sha256")
                if getattr(review,name)!=getattr(receipt,name)]
    reasons=[]
    if receipt.exit_code!=0:reasons.append("SOLVER_EXIT_NONZERO")
    if mismatches:reasons.append("RESULT_RECEIPT_HASH_MISMATCH")
    if review.completeness!="VERIFIED":reasons.append("RESULT_COMPLETENESS_NOT_VERIFIED")
    if review.consistency!="VERIFIED":reasons.append("RESULT_CONSISTENCY_NOT_VERIFIED")
    if review.log_review!="VERIFIED":reasons.append("SOLVER_LOG_NOT_VERIFIED")
    if review.critical_findings:reasons.append("SOLVER_CRITICAL_FINDINGS_PRESENT")
    return dict(status="BLOCK" if reasons else "READY_FOR_STRUCTURE_CORRELATION",
                mismatches=mismatches,critical_findings=list(review.critical_findings),
                reasons=reasons or ["RESULTS_VERIFIED_NOT_ENGINEERING_ACCEPTANCE"],
                acceptance_granted=False)

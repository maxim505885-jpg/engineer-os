"""Source-bound semantic review contract for structural calculation packages.

This module checks review completeness only. It does not decode LIR/SCAD,
execute a solver, or prove that a reviewer statement is true.
"""
from __future__ import annotations
from dataclasses import dataclass
from .model_intake import CalculationArtifactRole

_DECISIONS={"VERIFIED","REJECTED","NOT_VERIFIED"}

@dataclass(frozen=True)
class CalculationSemanticReview:
    role: CalculationArtifactRole
    statement: str
    source_ids: tuple[str,...]
    decision: str
    basis: str

    def __post_init__(self):
        if not isinstance(self.role,CalculationArtifactRole):
            raise ValueError("typed calculation role required")
        if any(not isinstance(v,str) or not v.strip() or len(v)>4000 for v in (self.statement,self.basis)):
            raise ValueError("bounded semantic review text required")
        if (not isinstance(self.source_ids,(tuple,list)) or not self.source_ids or len(self.source_ids)>100
                or any(not isinstance(v,str) or not v.strip() or len(v)>200 for v in self.source_ids)
                or len(set(self.source_ids))!=len(self.source_ids)):
            raise ValueError("distinct source ids required")
        if self.decision not in _DECISIONS:
            raise ValueError("invalid semantic decision")

def audit_calculation_semantics(reviews) -> dict:
    if not isinstance(reviews,(tuple,list)) or len(reviews)>100:
        raise ValueError("bounded semantic reviews required")
    if any(not isinstance(r,CalculationSemanticReview) for r in reviews):
        raise ValueError("typed semantic reviews required")
    roles=[r.role for r in reviews]
    if len(set(roles))!=len(roles):
        raise ValueError("semantic roles must be distinct")
    missing=[r.value for r in CalculationArtifactRole if r not in set(roles)]
    rejected=[r.role.value for r in reviews if r.decision=="REJECTED"]
    unverified=[r.role.value for r in reviews if r.decision!="VERIFIED"]
    if missing or rejected or unverified:
        return dict(status="BLOCK",missing_roles=missing,rejected_roles=rejected,
                    unverified_roles=unverified,
                    reasons=["CALCULATION_SEMANTIC_REVIEW_INCOMPLETE"],acceptance_granted=False)
    return dict(status="READY_FOR_SOLVER_VERIFICATION",missing_roles=[],rejected_roles=[],
                unverified_roles=[],
                reasons=["SOLVER_EXECUTION_NOT_PROVEN","ACTUAL_STRUCTURE_CORRELATION_NOT_ACCEPTED"],
                acceptance_granted=False)

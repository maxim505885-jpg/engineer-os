"""Correlation contract between calculation assumptions and actual-structure evidence."""
from __future__ import annotations
from dataclasses import dataclass

_REQUIRED=("GEOMETRY","MATERIALS_SECTIONS","LOADS_COMBINATIONS","SUPPORTS_RELEASES")
_DECISIONS={"VERIFIED","REJECTED","NOT_VERIFIED"}

@dataclass(frozen=True)
class StructureCorrelationItem:
    role:str
    calculation_source_ids:tuple[str,...]
    actual_source_ids:tuple[str,...]
    statement:str
    basis:str
    decision:str

    def __post_init__(self):
        if self.role not in _REQUIRED:raise ValueError("unsupported structure correlation role")
        for values in (self.calculation_source_ids,self.actual_source_ids):
            if not isinstance(values,(tuple,list)) or not values or len(values)>100 or any(
                not isinstance(x,str) or not x.strip() or len(x)>200 for x in values) or len(set(values))!=len(values):
                raise ValueError("distinct correlation source ids required")
        for v in (self.statement,self.basis):
            if not isinstance(v,str) or not v.strip() or len(v)>4000:
                raise ValueError("bounded correlation text required")
        if self.decision not in _DECISIONS:raise ValueError("invalid correlation decision")

def audit_structure_correlation(items)->dict:
    if not isinstance(items,(tuple,list)) or len(items)>len(_REQUIRED) or any(
        not isinstance(x,StructureCorrelationItem) for x in items):
        raise ValueError("bounded typed structure correlation required")
    roles=[x.role for x in items]
    if len(set(roles))!=len(roles):raise ValueError("structure correlation roles must be distinct")
    missing=[x for x in _REQUIRED if x not in roles]
    rejected=[x.role for x in items if x.decision=="REJECTED"]
    unverified=[x.role for x in items if x.decision!="VERIFIED"]
    reasons=[]
    if missing:reasons.append("STRUCTURE_CORRELATION_ROLES_MISSING")
    if rejected:reasons.append("STRUCTURE_CORRELATION_REJECTED")
    if unverified:reasons.append("STRUCTURE_CORRELATION_NOT_VERIFIED")
    return dict(status="BLOCK" if reasons else "READY_FOR_ENGINEERING_REVIEW",
                missing_roles=missing,rejected_roles=rejected,unverified_roles=unverified,
                reasons=reasons or ["ACTUAL_STRUCTURE_CORRELATION_NOT_ENGINEERING_ACCEPTANCE"],
                acceptance_granted=False)

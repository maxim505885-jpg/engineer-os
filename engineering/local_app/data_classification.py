"""Engineering data-class review for source candidates."""
from __future__ import annotations
from dataclasses import dataclass
_CLASSES={"P","F","M","T","C","A","I","U"}
_DECISIONS={"VERIFIED","REJECTED","NOT_VERIFIED"}

@dataclass(frozen=True)
class DataClassReview:
    candidate_id:str
    data_class:str
    decision:str
    basis:str

    def __post_init__(self):
        if not isinstance(self.candidate_id,str) or not self.candidate_id.strip():raise ValueError("candidate id required")
        if self.data_class not in _CLASSES:raise ValueError("invalid engineering data class")
        if self.decision not in _DECISIONS:raise ValueError("invalid data-class decision")
        if not isinstance(self.basis,str) or not self.basis.strip() or len(self.basis)>4000:raise ValueError("bounded data-class basis required")

def audit_data_classes(reviews,required_ids)->dict:
    if not isinstance(reviews,(tuple,list)) or len(reviews)>100 or any(not isinstance(x,DataClassReview) for x in reviews):
        raise ValueError("bounded data-class reviews required")
    if not isinstance(required_ids,(tuple,list,set)) or any(not isinstance(x,str) for x in required_ids):
        raise ValueError("required candidate ids required")
    ids=[x.candidate_id for x in reviews]
    if len(set(ids))!=len(ids):raise ValueError("data-class candidate ids must be distinct")
    required=set(required_ids)
    missing=sorted(required-set(ids))
    extra=sorted(set(ids)-required)
    unverified=sorted(x.candidate_id for x in reviews if x.decision!="VERIFIED")
    reasons=[]
    if missing:reasons.append("DATA_CLASS_REVIEWS_MISSING")
    if extra:reasons.append("DATA_CLASS_REVIEWS_OUT_OF_SCOPE")
    if unverified:reasons.append("DATA_CLASS_NOT_VERIFIED")
    return dict(status="BLOCK" if reasons else "READY_FOR_DOMAIN_REVIEW",
                missing_ids=missing,extra_ids=extra,unverified_ids=unverified,
                reasons=reasons or ["DATA_CLASSES_VERIFIED_NOT_ENGINEERING_ACCEPTANCE"],
                acceptance_granted=False)

"""Identity-bound verification receipt for a normative source document."""
from __future__ import annotations
from dataclasses import dataclass
import re
_SHA256=re.compile(r"^[0-9a-f]{64}$")
_DECISIONS={"VERIFIED","REJECTED","NOT_VERIFIED"}

@dataclass(frozen=True)
class NormativeSourceVerification:
    candidate_id:str
    document:str
    edition:str
    authority:str
    source_ref:str
    source_sha256:str
    verification_method:str
    decision:str

    def __post_init__(self):
        for v in (self.candidate_id,self.document,self.edition,self.authority,self.source_ref,self.verification_method):
            if not isinstance(v,str) or not v.strip() or len(v)>4000:
                raise ValueError("bounded normative source fields required")
        if not isinstance(self.source_sha256,str) or not _SHA256.fullmatch(self.source_sha256):
            raise ValueError("normative source sha256 required")
        if self.decision not in _DECISIONS:raise ValueError("invalid normative source decision")

def audit_normative_source(review:NormativeSourceVerification)->dict:
    if not isinstance(review,NormativeSourceVerification):
        raise ValueError("typed normative source verification required")
    if review.decision=="REJECTED":
        return dict(status="BLOCK",reasons=["NORMATIVE_SOURCE_REJECTED"],acceptance_granted=False)
    if review.decision!="VERIFIED":
        return dict(status="BLOCK",reasons=["NORMATIVE_SOURCE_NOT_VERIFIED"],acceptance_granted=False)
    return dict(status="READY_FOR_APPLICABILITY_REVIEW",
                reasons=["NORMATIVE_SOURCE_IDENTITY_VERIFIED_NOT_APPLICABILITY"],
                acceptance_granted=False)

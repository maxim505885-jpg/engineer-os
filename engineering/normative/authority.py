"""Fail-closed normative authority/applicability review contract.

A structured receipt is not self-authenticating. This module validates the
review shape and keeps the result below engineering acceptance.
"""
from __future__ import annotations
from dataclasses import dataclass

_DECISIONS={"VERIFIED","REJECTED","NOT_VERIFIED"}

@dataclass(frozen=True)
class NormativeAuthorityReview:
    document: str
    edition: str
    clause: str
    authority: str
    source_ref: str
    applicability_basis: str
    decision: str

    def __post_init__(self):
        for value in (self.document,self.edition,self.clause,self.authority,self.source_ref,self.applicability_basis):
            if not isinstance(value,str) or not value.strip() or len(value)>4000:
                raise ValueError("bounded normative authority fields are required")
        if self.decision not in _DECISIONS:
            raise ValueError("invalid normative authority decision")

def audit_normative_authority(review: NormativeAuthorityReview) -> dict:
    if not isinstance(review,NormativeAuthorityReview):
        raise ValueError("typed normative authority review required")
    if review.decision=="REJECTED":
        return dict(status="BLOCK",reasons=["NORMATIVE_AUTHORITY_REJECTED"],acceptance_granted=False)
    if review.decision!="VERIFIED":
        return dict(status="BLOCK",reasons=["NORMATIVE_AUTHORITY_NOT_VERIFIED"],acceptance_granted=False)
    return dict(
        status="READY_FOR_EXPERT_APPLICABILITY_REVIEW",
        reasons=["AUTHORITY_RECEIPT_NOT_SELF_AUTHENTICATING","ENGINEERING_APPLICABILITY_NOT_ACCEPTED"],
        acceptance_granted=False,
    )

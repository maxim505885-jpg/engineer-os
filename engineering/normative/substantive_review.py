"""Dated, source-bound recorded judgement; never an acceptance credential."""
from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class NormativeSubstantiveReview:
    reviewer: str
    reviewed_at: str
    assessment_date: str
    edition_basis: str
    applicability: str
    applicability_basis: str
    input_status: str
    outcome: str
    rationale: str
    limitations: list[str]

    def __post_init__(self):
        for value in (self.reviewer,self.edition_basis,self.applicability_basis,self.rationale):
            if not isinstance(value,str) or not value.strip() or len(value)>1000:
                raise ValueError('Bounded substantive review basis required')
        try:
            reviewed=date.fromisoformat(self.reviewed_at)
            assessed=date.fromisoformat(self.assessment_date)
            if reviewed.isoformat()!=self.reviewed_at or assessed.isoformat()!=self.assessment_date or assessed>reviewed or reviewed>date.today():
                raise ValueError('Invalid normative review dates')
        except (ValueError,TypeError):
            raise ValueError('Ordered ISO normative review dates required') from None
        if self.applicability not in {'APPLIES','OUT_OF_SCOPE','UNKNOWN','CONFLICT'}:
            raise ValueError('Invalid applicability decision')
        if self.input_status not in {'DOCUMENTED','UNVERIFIED','MISSING','CONFLICT'}:
            raise ValueError('Invalid input verification status')
        if self.outcome not in {'PASS','WARNING','UNCERTAINTY','ERROR','BLOCK'}:
            raise ValueError('Invalid substantive outcome')
        if self.outcome in {'PASS','ERROR'} and (self.applicability!='APPLIES' or self.input_status!='DOCUMENTED'):
            raise ValueError('Positive or proven-error judgement requires documented applicable inputs')
        if not isinstance(self.limitations,list) or not 1<=len(self.limitations)<=10 or any(not isinstance(v,str) or not v.strip() or len(v)>1000 for v in self.limitations):
            raise ValueError('Explicit bounded review limitations required')


def evaluate_substantive_review(review,*,source_linked,edition_verified,authority_verified,basis_current):
    if not isinstance(review,NormativeSubstantiveReview):
        raise ValueError('Typed substantive review required')
    reasons=[]
    if not source_linked:reasons.append('NORMATIVE_REVIEW_SOURCE_CHANGED')
    if not basis_current:reasons.append('NORMATIVE_REVIEW_BASIS_CHANGED')
    if not edition_verified:reasons.append('NORMATIVE_EDITION_NOT_VERIFIED')
    if not authority_verified:reasons.append('NORMATIVE_AUTHORITY_NOT_VERIFIED')
    if review.applicability=='CONFLICT':reasons.append('NORMATIVE_APPLICABILITY_CONFLICT')
    if review.input_status in {'MISSING','CONFLICT'}:reasons.append('NORMATIVE_INPUT_'+review.input_status)
    if reasons:status='BLOCK'
    elif review.applicability in {'UNKNOWN','OUT_OF_SCOPE'}:
        status='UNCERTAINTY';reasons.append('NORMATIVE_APPLICABILITY_'+review.applicability)
    elif review.input_status=='UNVERIFIED':
        status='UNCERTAINTY';reasons.append('NORMATIVE_INPUT_UNVERIFIED')
    elif review.outcome in {'PASS','ERROR'}:
        status='UNCERTAINTY';reasons.append('REVIEWER_AUTHORITY_NOT_VERIFIED')
    else:status=review.outcome
    return dict(status=status,declared_outcome=review.outcome,reviewer=review.reviewer,
        reviewed_at=review.reviewed_at,assessment_date=review.assessment_date,
        applicability=review.applicability,input_status=review.input_status,
        rationale=review.rationale,limitations=list(review.limitations),reasons=reasons,
        scope='RECORDED_SOURCE_REVIEW',acceptance_granted=False,engineering_verified=False)

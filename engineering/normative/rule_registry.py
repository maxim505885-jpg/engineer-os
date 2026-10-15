"""Version-bound normative arithmetic readiness; records never authenticate truth.

No preloaded clauses, current-edition assertions, acceptance or source discovery.
"""
from dataclasses import asdict, dataclass
from datetime import date
import hashlib
import json
import re
from .numeric_comparison import compare_quantity
from .source_verification import NormativeSourceVerification, audit_normative_source
from .authority import NormativeAuthorityReview, audit_normative_authority
from .substantive_review import NormativeSubstantiveReview

@dataclass(frozen=True)
class Rule:
    rule_id: str
    rule_version: str
    document: str
    edition: str
    scope: str
    clause: str
    requirement: str
    normative_source_sha256: str
    effective_from: str
    effective_until: str
    operator: str
    limit: str
    limit_unit: str
    clause_text: str = ''
    source_locator: str = ''
    accepted_data_classes: tuple[str,...] = ('PROJECT','ACTUAL','MEASURED','TESTED','CALCULATED')

@dataclass(frozen=True)
class RuleRegistry:
    rules: tuple[Rule,...]
    registry_version: str = '1'

@dataclass(frozen=True)
class ActualQuantity:
    value: str
    unit: str
    evidence_ids: tuple[str,...]
    source_sha256: str
    locator: str
    data_class: str

@dataclass(frozen=True)
class AssessmentReceipt:
    rule_id: str
    rule_version: str
    rule_sha256: str
    assessment_date: str
    actual: ActualQuantity | None
    source_review: NormativeSourceVerification | None
    authority_review: NormativeAuthorityReview | None
    substantive_review: NormativeSubstantiveReview | None

def _text(value):
    return isinstance(value,str) and bool(value.strip()) and len(value)<=4000

def _sha(value):
    return isinstance(value,str) and re.fullmatch('[0-9a-f]{64}',value) is not None

def _day(value):
    if not isinstance(value,str):raise ValueError('ISO_DATE_REQUIRED')
    parsed=date.fromisoformat(value)
    if parsed.isoformat()!=value:raise ValueError('ISO_DATE_REQUIRED')
    return parsed

def rule_digest(rule):
    """Digest binds the entire exact declared rule, not its normative correctness."""
    if not isinstance(rule,Rule):raise ValueError('TYPED_RULE_REQUIRED')
    return hashlib.sha256(json.dumps(asdict(rule),sort_keys=True,allow_nan=False,separators=(',',':'),ensure_ascii=False).encode('utf-8')).hexdigest()

def assess_rule(registry, receipt):
    base=dict(status='BLOCK',scope='VERSION_BOUND_ARITHMETIC_READINESS_ONLY',comparison_ready=False,
              acceptance_granted=False,engineering_verified=False,normative_truth_verified=False,
              current_edition_verified=False,reasons=[])
    def stop(reason,status='BLOCK'):
        return dict(base,status=status,reasons=[reason])
    if not isinstance(registry,RuleRegistry) or not isinstance(registry.rules,tuple) or not 1<=len(registry.rules)<=1000 or not _text(registry.registry_version):
        return stop('TYPED_BOUNDED_REGISTRY_REQUIRED')
    if not isinstance(receipt,AssessmentReceipt):return stop('TYPED_ASSESSMENT_RECEIPT_REQUIRED')
    seen=set()
    try:
        for rule in registry.rules:
            if not isinstance(rule,Rule):return stop('TYPED_RULE_REQUIRED')
            if not all(_text(getattr(rule,key)) for key in ('rule_id','rule_version','document','edition','scope','clause','requirement')):return stop('RULE_IDENTITY_SCOPE_AND_REQUIREMENT_REQUIRED')
            if not _sha(rule.normative_source_sha256):return stop('NORMATIVE_SOURCE_SHA256_REQUIRED')
            if (not isinstance(rule.accepted_data_classes,tuple) or not rule.accepted_data_classes or len(set(rule.accepted_data_classes))!=len(rule.accepted_data_classes) or any(c not in ('PROJECT','ACTUAL','MEASURED','TESTED','CALCULATED') for c in rule.accepted_data_classes)):return stop('INVALID_RULE_DATA_CLASSES')
            key=(rule.rule_id,rule.rule_version)
            if key in seen:return stop('DUPLICATE_RULE_VERSION')
            seen.add(key)
            if _day(rule.effective_from)>_day(rule.effective_until):return stop('INVALID_EFFECTIVE_INTERVAL')
            check=compare_quantity(actual=rule.limit,actual_unit=rule.limit_unit,limit=rule.limit,limit_unit=rule.limit_unit,operator=rule.operator)
            if check['status']=='BLOCK':return stop('INVALID_RULE_QUANTITY_OR_OPERATOR')
        if not _text(receipt.rule_id) or not _text(receipt.rule_version):return stop('RECEIPT_RULE_IDENTITY_REQUIRED')
        matches=[rule for rule in registry.rules if (rule.rule_id,rule.rule_version)==(receipt.rule_id,receipt.rule_version)]
        if len(matches)!=1:return stop('RULE_VERSION_NOT_REGISTERED')
        rule=matches[0]
        digest=rule_digest(rule)
        if not _sha(receipt.rule_sha256) or receipt.rule_sha256!=digest:return stop('RULE_CONTENT_OR_VERSION_CHANGED')
        assessed=_day(receipt.assessment_date)
        if not _day(rule.effective_from)<=assessed<=_day(rule.effective_until):return stop('ASSESSMENT_OUTSIDE_DECLARED_EFFECTIVE_INTERVAL')
    except (ValueError,TypeError,AttributeError):return stop('INVALID_RULE_OR_ASSESSMENT_CONTRACT')
    base.update(registry_version=registry.registry_version,rule=asdict(rule),rule_sha256=digest,assessment_date=receipt.assessment_date)
    source=receipt.source_review
    authority=receipt.authority_review
    substantive=receipt.substantive_review
    actual=receipt.actual
    if not isinstance(source,NormativeSourceVerification):return stop('NORMATIVE_SOURCE_VERIFICATION_RECEIPT_REQUIRED')
    if audit_normative_source(source)['status']=='BLOCK':return stop('NORMATIVE_SOURCE_NOT_VERIFIED')
    if (source.candidate_id,source.document,source.edition,source.source_sha256)!=(rule.rule_id,rule.document,rule.edition,rule.normative_source_sha256):return stop('NORMATIVE_SOURCE_RULE_IDENTITY_MISMATCH')
    if not isinstance(authority,NormativeAuthorityReview):return stop('NORMATIVE_AUTHORITY_RECEIPT_REQUIRED')
    if audit_normative_authority(authority)['status']=='BLOCK':return stop('NORMATIVE_AUTHORITY_NOT_VERIFIED')
    if (authority.document,authority.edition,authority.clause,authority.authority,authority.source_ref)!=(rule.document,rule.edition,rule.clause,source.authority,source.source_ref):return stop('NORMATIVE_AUTHORITY_RULE_IDENTITY_MISMATCH')
    if not isinstance(substantive,NormativeSubstantiveReview):return stop('SUBSTANTIVE_REVIEW_REQUIRED')
    if substantive.assessment_date!=receipt.assessment_date:return stop('SUBSTANTIVE_REVIEW_DATE_MISMATCH')
    if substantive.applicability=='CONFLICT':return stop('APPLICABILITY_CONFLICT')
    if substantive.applicability!='APPLIES':return stop('APPLICABILITY_NOT_ESTABLISHED','UNCERTAINTY')
    if substantive.input_status in ('MISSING','CONFLICT'):return stop('ACTUAL_INPUTS_MISSING_OR_CONFLICT')
    if substantive.input_status!='DOCUMENTED':return stop('ACTUAL_INPUTS_NOT_DOCUMENTED','UNCERTAINTY')
    if substantive.outcome in ('ERROR','BLOCK'):return stop('SUBSTANTIVE_REVIEW_HAS_UNRESOLVED_FINDINGS')
    if substantive.outcome=='WARNING':return stop('SUBSTANTIVE_REVIEW_HAS_WARNING','UNCERTAINTY')
    if not isinstance(actual,ActualQuantity):return stop('TYPED_ACTUAL_QUANTITY_REQUIRED')
    if not _sha(actual.source_sha256) or not _text(actual.locator):return stop('ACTUAL_SOURCE_PROVENANCE_REQUIRED')
    if (not isinstance(actual.evidence_ids,tuple) or not 1<=len(actual.evidence_ids)<=100 or
        not all(_text(value) for value in actual.evidence_ids) or len(set(actual.evidence_ids))!=len(actual.evidence_ids)):
        return stop('ACTUAL_EVIDENCE_IDS_REQUIRED')
    if actual.data_class not in ('PROJECT','ACTUAL','MEASURED','TESTED','CALCULATED'):return stop('ACTUAL_INPUT_DATA_CLASS_NOT_SUPPORTED')
    if actual.data_class not in rule.accepted_data_classes:return stop('ACTUAL_INPUT_DATA_CLASS_NOT_ALLOWED_BY_RULE')
    comparison=compare_quantity(actual=actual.value,actual_unit=actual.unit,limit=rule.limit,limit_unit=rule.limit_unit,operator=rule.operator)
    if comparison['status']=='BLOCK':return dict(base,comparison=comparison,reasons=['QUANTITY_COMPARISON_BLOCKED'])
    recorded=asdict(receipt)
    receipt_sha256=hashlib.sha256(json.dumps(recorded,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode('utf-8')).hexdigest()
    return dict(base,status='UNCERTAINTY',comparison_ready=True,comparison=comparison,
                actual=asdict(actual),receipt=recorded,receipt_sha256=receipt_sha256,
                reasons=['ARITHMETIC_COMPARISON_ONLY','DECLARED_EFFECTIVE_INTERVAL_NOT_INDEPENDENTLY_VERIFIED',
                         'SOURCE_AND_REVIEW_RECEIPTS_NOT_SELF_AUTHENTICATING','ACTUAL_EVIDENCE_NOT_INDEPENDENTLY_VERIFIED'],
                limitations=['NO_CURRENT_OR_LATEST_EDITION_CLAIM','NO_ENGINEERING_ACCEPTANCE'])

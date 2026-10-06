"""Stage-8 immutable FINAL AUDIT over a fresh Stage-7 real-case snapshot.

FINAL AUDIT is deterministic and fail-closed. It may produce ACCEPTED only when
all required case dimensions are ready and no upstream blockers remain.
"""
from __future__ import annotations

import hashlib
import json
import time
import uuid

from .real_case import report as real_case_report

CHECKED_DIMENSIONS=(
    "CASE_FRESHNESS",
    "SOURCE_IDENTITY",
    "TZ_TRACEABILITY",
    "EVIDENCE_REVIEW",
    "SPECIALIST_COVERAGE",
    "DOMAIN_PREREQUISITES",
    "CASE_QC",
    "ACCEPTANCE_BASIS",
)

_READY_STAGE={
    "source_identity":{"READY"},
    "requirements":{"READY_FOR_ENGINEERING_REVIEW"},
    "evidence":{"READY_FOR_ENGINEERING_REVIEW"},
    "specialists":{"READY_FOR_CASE_QC"},
    "domain_prerequisites":{"READY_FOR_CASE_QC"},
    "qc":{"READY_FOR_REAL_CASE_REVIEW"},
}

def _digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(",",":")).encode()).hexdigest()

def evaluate_case(case,*,fresh:bool,stale_reasons=()):
    if not isinstance(case,dict):raise ValueError("Stage-7 case object required")
    if type(fresh) is not bool:raise ValueError("fresh flag required")
    reasons=[];checks=[]
    checks.append(dict(dimension="CASE_FRESHNESS",status="PASS" if fresh else "BLOCK",
                       reasons=[] if fresh else list(stale_reasons) or ["CASE_NOT_FRESH"]))
    if not fresh:reasons.extend(list(stale_reasons) or ["CASE_NOT_FRESH"])

    stages=case.get("stages") or {}
    mapping=(
        ("SOURCE_IDENTITY","source_identity"),
        ("TZ_TRACEABILITY","requirements"),
        ("EVIDENCE_REVIEW","evidence"),
        ("SPECIALIST_COVERAGE","specialists"),
        ("DOMAIN_PREREQUISITES","domain_prerequisites"),
        ("CASE_QC","qc"),
    )
    for dimension,key in mapping:
        stage=stages.get(key)
        allowed=_READY_STAGE[key]
        if not isinstance(stage,dict):
            status="BLOCK";why=[f"{key.upper()}_STAGE_MISSING"]
        elif stage.get("status") not in allowed:
            status="BLOCK";why=list(stage.get("reasons") or [f"{key.upper()}_NOT_READY"])
        else:
            status="PASS";why=[]
        checks.append(dict(dimension=dimension,status=status,reasons=why))
        if status=="BLOCK":reasons.extend(why)

    evidence=case.get("evidence")
    domains=case.get("domain_packets")
    identity=case.get("identity")
    basis_reasons=[]
    if not isinstance(identity,dict) or not identity.get("core_job_id") or not identity.get("originals"):
        basis_reasons.append("CASE_IDENTITY_BASIS_MISSING")
    if not isinstance(evidence,list) or not evidence:
        basis_reasons.append("EVIDENCE_ACCEPTANCE_BASIS_MISSING")
    if not isinstance(domains,dict):
        basis_reasons.append("DOMAIN_ACCEPTANCE_BASIS_MISSING")
    checks.append(dict(dimension="ACCEPTANCE_BASIS",status="BLOCK" if basis_reasons else "PASS",reasons=basis_reasons))
    reasons.extend(basis_reasons)

    if case.get("point7_readiness")!="READY_FOR_REAL_CASE_REVIEW":
        reasons.append("POINT7_NOT_READY_FOR_FINAL_AUDIT")
    if case.get("engineering_status") not in {"READY_FOR_FINAL_AUDIT","READY_FOR_ENGINEERING_DECISION"}:
        reasons.append("CASE_ENGINEERING_STATUS_NOT_READY")
    if case.get("acceptance_granted") is True:
        reasons.append("PREEXISTING_ACCEPTANCE_NOT_ALLOWED")
    if case.get("final_audit") not in {"NOT_RUN",None}:
        reasons.append("CASE_ALREADY_HAS_FINAL_AUDIT_STATE")

    reasons=list(dict.fromkeys(reasons))
    accepted=not reasons and all(x["status"]=="PASS" for x in checks)
    deterministic=dict(
        schema="ENGINEER_OS_FINAL_AUDIT_V1",
        case_id=case.get("id"),
        case_sha256=case.get("case_sha256"),
        checked_dimensions=list(CHECKED_DIMENSIONS),
        checks=checks,
        blocker_codes=reasons,
        decision="ACCEPTED" if accepted else "BLOCK",
        acceptance_granted=accepted,
        engineering_verified=accepted,
        final_audit="COMPLETED",
    )
    deterministic["audit_sha256"]=_digest(deterministic)
    if accepted:
        deterministic["acceptance_certificate"]=dict(
            case_id=case.get("id"),case_sha256=case.get("case_sha256"),
            audit_sha256=deterministic["audit_sha256"],
            basis_sha256=_digest(dict(identity=identity,evidence=evidence,domains=domains)),
        )
    else:
        deterministic["acceptance_certificate"]=None
    return deterministic

def evaluate_offline_stage7(case):
    if not isinstance(case,dict):raise ValueError("Stage-7 offline case required")
    reasons=list(case.get("block_reasons") or [])
    if case.get("stage7_completion") not in {"COMPLETE","COMPLETE_WITH_OPEN_ENGINEERING_BLOCKS"}:
        reasons.append("STAGE7_WORKFLOW_NOT_COMPLETE")
    if case.get("source_identity_status")!="PASS":reasons.append("SOURCE_IDENTITY_NOT_PASS")
    if case.get("missing_roles"):reasons.append("REQUIRED_SOURCE_ROLES_MISSING")
    if not case.get("workflow_complete"):reasons.append("STAGE7_WORKFLOW_NOT_COMPLETE")
    if case.get("tz_traceability_status")!="PASS":reasons.append("TZ_TRACEABILITY_NOT_RECORDED")
    if case.get("evidence_review_status")!="PASS":reasons.append("EVIDENCE_REVIEW_NOT_RECORDED")
    if case.get("specialist_coverage_status")!="PASS":reasons.append("SPECIALIST_COVERAGE_NOT_RECORDED")
    if case.get("domain_prerequisites_status")!="PASS":reasons.append("DOMAIN_PREREQUISITES_NOT_RECORDED")
    if case.get("case_qc_status")!="PASS":reasons.append("CASE_QC_NOT_RECORDED")
    if case.get("engineering_status")!="READY_FOR_FINAL_AUDIT":
        reasons.append("CASE_ENGINEERING_STATUS_NOT_READY")
    reasons=list(dict.fromkeys(reasons))

    def dimension(name,status_key,extra=()):
        local=[x for x in extra if x in reasons]
        if case.get(status_key)!="PASS":
            code={
                "tz_traceability_status":"TZ_TRACEABILITY_NOT_RECORDED",
                "evidence_review_status":"EVIDENCE_REVIEW_NOT_RECORDED",
                "specialist_coverage_status":"SPECIALIST_COVERAGE_NOT_RECORDED",
                "domain_prerequisites_status":"DOMAIN_PREREQUISITES_NOT_RECORDED",
                "case_qc_status":"CASE_QC_NOT_RECORDED",
            }[status_key]
            if code not in local:local.append(code)
        return dict(dimension=name,status="BLOCK" if local else "PASS",reasons=local)

    checks=[
        dict(dimension="CASE_FRESHNESS",status="PASS",reasons=[]),
        dict(dimension="SOURCE_IDENTITY",status="PASS" if case.get("source_identity_status")=="PASS" else "BLOCK",
             reasons=[] if case.get("source_identity_status")=="PASS" else ["SOURCE_IDENTITY_NOT_PASS"]),
        dimension("TZ_TRACEABILITY","tz_traceability_status",("V4_DOCUMENT_COMPLETENESS_BLOCK",)),
        dimension("EVIDENCE_REVIEW","evidence_review_status"),
        dimension("SPECIALIST_COVERAGE","specialist_coverage_status",("POINT6_NORMATIVE_DECISION_PENDING","POINT6_SOLVER_DECISION_PENDING")),
        dimension("DOMAIN_PREREQUISITES","domain_prerequisites_status",("ACTUAL_STRUCTURE_CORRELATION_PENDING",)),
        dimension("CASE_QC","case_qc_status"),
    ]
    basis_blockers=list(reasons)
    checks.append(dict(dimension="ACCEPTANCE_BASIS",status="BLOCK" if basis_blockers else "PASS",reasons=basis_blockers))
    deterministic=dict(
        schema="ENGINEER_OS_FINAL_AUDIT_V1",
        source_schema=case.get("schema"),
        case_id=case.get("case_id"),
        case_sha256=case.get("case_sha256"),
        checked_dimensions=list(CHECKED_DIMENSIONS),
        checks=checks,
        blocker_codes=reasons,
        decision="BLOCK" if reasons else "ACCEPTED",
        acceptance_granted=not reasons,
        engineering_verified=not reasons,
        final_audit="COMPLETED",
        acceptance_certificate=None,
    )
    deterministic["audit_sha256"]=_digest(deterministic)
    if not reasons:
        deterministic["acceptance_certificate"]=dict(case_sha256=case.get("case_sha256"),audit_sha256=deterministic["audit_sha256"])
    return deterministic

def build(store,session_id,*,case_id,expected_revision):
    report=real_case_report(store,session_id)
    if not report.get("cases"):raise ValueError("Stage-7 case not found")
    current=next((x for x in report["cases"] if x.get("current")),None)
    if current is None:raise ValueError("Current Stage-7 case not found")
    if current["id"]!=case_id:raise ValueError("FINAL AUDIT must target the current Stage-7 case")
    result=evaluate_case(current,fresh=bool(report.get("current_fresh")),stale_reasons=current.get("stale_reasons") or [])
    event=dict(result,id=str(uuid.uuid4()),session_id=session_id,case_id=case_id,created=time.time(),
               scope="FINAL_AUDIT",case_revision=current["revision"])
    return store.add_final_audit(event,expected_revision)

def report(store,session_id):
    state=store.final_audit_state(session_id)
    if not state:
        return dict(audits=[],revision=0,status="NOT_RUN",acceptance_granted=False,final_audit="NOT_RUN")
    case_report=real_case_report(store,session_id)
    current_case=next((x for x in case_report.get("cases",[]) if x.get("current")),None)
    latest=state[-1]
    stale=[]
    if current_case is None:stale.append("CURRENT_CASE_MISSING")
    else:
        if latest["case_id"]!=current_case["id"]:stale.append("AUDITED_CASE_SUPERSEDED")
        if latest.get("case_sha256")!=current_case.get("case_sha256"):stale.append("AUDITED_CASE_IDENTITY_CHANGED")
        if not case_report.get("current_fresh"):stale.extend(current_case.get("stale_reasons") or ["CURRENT_CASE_STALE"])
    rows=[]
    for audit in state:
        row=dict(audit)
        row["current"]=audit["id"]==latest["id"]
        row["fresh"]=row["current"] and not stale
        row["stale_reasons"]=stale if row["current"] else ["SUPERSEDED_FINAL_AUDIT"]
        row["effective_decision"]=audit["decision"] if row["fresh"] else "BLOCK"
        row["effective_acceptance_granted"]=bool(row["fresh"] and audit["acceptance_granted"] and audit["decision"]=="ACCEPTED")
        rows.append(row)
    effective="ACCEPTED" if rows[-1]["effective_acceptance_granted"] else "BLOCK"
    return dict(audits=rows,revision=latest["revision"],status=effective,current_audit_id=latest["id"],
                current_fresh=not stale,acceptance_granted=effective=="ACCEPTED",final_audit="COMPLETED")

def acceptance_gate(store,session_id):
    r=report(store,session_id)
    return r.get("status")=="ACCEPTED" and r.get("acceptance_granted") is True and r.get("current_fresh") is True

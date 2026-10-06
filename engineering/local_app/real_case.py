"""Immutable stage-7 engineering case snapshots.

A case snapshot assembles the full current engineering context around one CORE_RUN.
It never upgrades preliminary/model output into engineering acceptance.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import time
import uuid

from .core_plan import verify_originals
from .requirements import report as requirements_report,source_check
from .domain_packets import report as domain_report


def _digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()


def _job(snapshot,job_id):
    for job in snapshot['jobs']:
        if job['id']==job_id:return job
    raise ValueError('CORE_RUN job not found in this conversation')


def _selected_candidates(store,session_id,snapshot,file_ids):
    selected=set(file_ids);rows=[]
    for candidate in snapshot['evidence']:
        if candidate['file_id'] not in selected:continue
        checked=source_check(store,session_id,candidate,selected_files=file_ids)
        rows.append(dict(
            candidate_id=candidate['id'],
            file_id=candidate['file_id'],
            source_sha256=candidate['source_sha256'],
            data_class=candidate['data_class'],
            review_revision=candidate['review_revision'],
            review_event_id=(candidate['latest_review'] or {}).get('id'),
            status=checked['status'],
            reasons=checked['reasons'],
        ))
    return rows


CASE_ROLES={'TOR','REPORT','CALCULATION_REPORT','MODEL','GEODESY','GRAPHICS','PHOTO','OTHER'}

def _manifest(value,file_ids):
    if value is None:return {}
    if not isinstance(value,dict) or len(value)>len(CASE_ROLES):raise ValueError('Invalid case source manifest')
    allowed=set(file_ids);out={}
    for role,ids in value.items():
        if role not in CASE_ROLES or not isinstance(ids,list) or not ids or len(ids)>20 or len(set(ids))!=len(ids):
            raise ValueError('Invalid case source manifest role')
        if any(not isinstance(x,str) or x not in allowed for x in ids):
            raise ValueError('Case source manifest references a file outside CORE_RUN')
        out[role]=list(ids)
    return out

def _source_stage(files,result,manifest):
    reasons=[]
    for f in files:
        path=Path(f['path'])
        if not path.is_file() or path.stat().st_size!=f['size']:
            reasons.append('SOURCE_IDENTITY_OR_LOCATION_CHANGED')
    if not manifest:reasons.append('CASE_SOURCE_ROLES_NOT_DECLARED')
    else:
        if 'TOR' not in manifest:reasons.append('CASE_TOR_SOURCE_NOT_DECLARED')
        if 'REPORT' not in manifest:reasons.append('CASE_REPORT_SOURCE_NOT_DECLARED')
    analysis=(result or {}).get('document_analysis')
    if analysis:
        if not analysis.get('all_batches_completed'):reasons.append('DOCUMENT_ANALYSIS_INCOMPLETE')
        if analysis.get('blocked_pages'):reasons.append('DOCUMENT_BLOCKED_PAGES_PRESENT')
        if analysis.get('failed_pages'):reasons.append('DOCUMENT_FAILED_PAGES_PRESENT')
        if analysis.get('budget_exhausted'):reasons.append('DOCUMENT_ANALYSIS_BUDGET_EXHAUSTED')
    return dict(status='BLOCK' if reasons else 'READY',reasons=list(dict.fromkeys(reasons)))


def _requirements_stage(report):
    reasons=[]
    if not report.get('set_id'):reasons.append('TZ_CHECKLIST_MISSING')
    rows=report.get('requirements',[])
    if not rows:reasons.append('TZ_REQUIREMENTS_MISSING')
    for row in rows:
        if row.get('traceability')!='SOURCE_LINKED':reasons.append('TZ_REQUIREMENT_NOT_SOURCE_LINKED')
        if row.get('status')=='BLOCK':reasons.append('TZ_REQUIREMENT_BLOCKED')
    return dict(status='BLOCK' if reasons else 'READY_FOR_ENGINEERING_REVIEW',
                reasons=list(dict.fromkeys(reasons)),requirements_total=len(rows))


def _evidence_stage(candidates):
    reasons=[]
    if not candidates:reasons.append('EVIDENCE_CANDIDATES_MISSING')
    if any(row['status']!='SOURCE_REVIEWED' for row in candidates):reasons.append('SOURCE_REVIEW_PREREQUISITES_OPEN')
    return dict(status='BLOCK' if reasons else 'READY_FOR_ENGINEERING_REVIEW',
                reasons=reasons,candidates_total=len(candidates))


def _specialist_stage(job):
    result=job.get('result') or {};run=result.get('core_run')
    reasons=[]
    if job.get('mode')!='CORE_RUN':reasons.append('CASE_REQUIRES_CORE_RUN')
    if job.get('state')!='SUCCEEDED':reasons.append('CORE_RUN_NOT_SUCCEEDED')
    if not run:reasons.append('CORE_RUN_RESULT_MISSING')
    else:
        if not run.get('analysis_complete'):reasons.append('SPECIALIST_ANALYSIS_INCOMPLETE')
        for row in run.get('results',[]):
            if row.get('execution')!='COMPLETED':reasons.append('SPECIALIST_EXECUTION_INCOMPLETE')
            if row.get('status') in {'ERROR','BLOCK'}:reasons.append('SPECIALIST_RESULT_BLOCKED')
    return dict(status='BLOCK' if reasons else 'READY_FOR_CASE_QC',
                reasons=list(dict.fromkeys(reasons)),
                requested_checks=list(job.get('requested_checks',[])),
                results=(run or {}).get('results',[]))


def _domain_stage(job,domains):
    requested=set(job.get('requested_checks',[]));required=[]
    if 'normative' in requested:required.append('NORMATIVE')
    if 'calculation' in requested:required.append('CALCULATION')
    by_kind={row['kind']:row for row in domains.get('packets',[])}
    reasons=[]
    for kind in required:
        if kind not in by_kind:
            reasons.append(kind+'_DOMAIN_PACKET_MISSING')
        elif by_kind[kind].get('point6_readiness')!='READY_FOR_ENGINEERING_DECISION':
            reasons.append(kind+'_POINT6_ENGINEERING_DECISION_PENDING')
    return dict(status='BLOCK' if reasons else 'READY_FOR_CASE_QC',
                reasons=reasons,required_kinds=required,
                packet_revisions={kind:by_kind[kind]['revision'] for kind in required if kind in by_kind})


def _qc_stage(requirements,evidence,specialists,domains):
    reasons=[]
    for stage in (requirements,evidence,specialists,domains):
        if stage['status']=='BLOCK':reasons.extend(stage['reasons'])
    return dict(status='BLOCK' if reasons else 'READY_FOR_REAL_CASE_REVIEW',
                reasons=list(dict.fromkeys(reasons)),
                acceptance_granted=False,final_audit='NOT_RUN')


def build(store,session_id,*,job_id,expected_revision,manifest=None):
    snapshot=store.snapshot(session_id);job=_job(snapshot,job_id)
    if job.get('mode')!='CORE_RUN':raise ValueError('Stage 7 requires a CORE_RUN job')
    if not job.get('result'):raise ValueError('CORE_RUN has no saved result')
    files=[store.get_file(fid) for fid in job['file_ids']]
    if any(f['session_id']!=session_id for f in files):raise ValueError('Attachment isolation failure')
    verify_originals(files)
    manifest=_manifest(manifest,job['file_ids'])

    requirements=requirements_report(store,session_id,selected_files=job['file_ids'])
    domains=domain_report(store,session_id,selected_files=job['file_ids'])
    candidates=_selected_candidates(store,session_id,snapshot,job['file_ids'])

    source=_source_stage(files,job['result'],manifest)
    req_stage=_requirements_stage(requirements)
    evidence=_evidence_stage(candidates)
    specialists=_specialist_stage(job)
    domain=_domain_stage(job,domains)
    qc=_qc_stage(req_stage,evidence,specialists,domain)

    originals=[dict(id=f['id'],name=f['name'],sha256=f['sha256'],size=f['size']) for f in files]
    identity=dict(
        core_job_id=job['id'],
        core_job_state=job['state'],
        prompt=job['prompt'],
        requested_checks=list(job['requested_checks']),
        originals=originals,
        source_manifest=manifest,
        requirements_digest=_digest(requirements),
        evidence_digest=_digest(candidates),
        domain_digest=_digest(domains),
        core_result_digest=_digest(job['result']),
    )
    event=dict(
        id=str(uuid.uuid4()),session_id=session_id,job_id=job_id,created=time.time(),
        scope='REAL_ENGINEERING_CASE_SNAPSHOT',
        identity=identity,
        source_manifest=manifest,
        stages=dict(source_identity=source,requirements=req_stage,evidence=evidence,
                    specialists=specialists,domain_prerequisites=domain,qc=qc),
        requirements=requirements,
        evidence=candidates,
        domain_packets=domains,
        point7_readiness=qc['status'],
        engineering_status='BLOCK',
        evidentiary_status='CASE_SNAPSHOT_NOT_ACCEPTANCE',
        acceptance_granted=False,
        final_audit='NOT_RUN',
    )
    event['case_sha256']=_digest(event)
    return store.add_real_case_snapshot(event,expected_revision)


def report(store,session_id):
    state=store.real_case_state(session_id)
    if not state:
        return dict(cases=[],revision=0,status='NOT_PROVIDED',acceptance_granted=False,final_audit='NOT_RUN')
    current=state[-1]
    stale_reasons=[]
    try:
        snapshot=store.snapshot(session_id);job=_job(snapshot,current['job_id'])
        files=[store.get_file(fid) for fid in job['file_ids']]
        verify_originals(files)
        requirements=requirements_report(store,session_id,selected_files=job['file_ids'])
        domains=domain_report(store,session_id,selected_files=job['file_ids'])
        candidates=_selected_candidates(store,session_id,snapshot,job['file_ids'])
        if _digest(requirements)!=current['identity']['requirements_digest']:stale_reasons.append('TZ_STATE_CHANGED')
        if _digest(candidates)!=current['identity']['evidence_digest']:stale_reasons.append('EVIDENCE_STATE_CHANGED')
        if _digest(domains)!=current['identity']['domain_digest']:stale_reasons.append('DOMAIN_STATE_CHANGED')
        if _digest(job.get('result'))!=current['identity']['core_result_digest']:stale_reasons.append('CORE_RESULT_CHANGED')
        current_ids=[(f['id'],f['sha256'],f['size']) for f in files]
        expected=[(f['id'],f['sha256'],f['size']) for f in current['identity']['originals']]
        if current_ids!=expected:stale_reasons.append('ORIGINAL_SET_CHANGED')
    except Exception:
        stale_reasons.append('CASE_REVALIDATION_FAILED')
    rows=[]
    for item in state:
        row=dict(item)
        row['current']=item['id']==current['id']
        row['fresh']=row['current'] and not stale_reasons
        row['stale_reasons']=stale_reasons if row['current'] else ['SUPERSEDED_CASE_SNAPSHOT']
        rows.append(row)
    return dict(cases=rows,revision=state[-1]['revision'],
                status='BLOCK' if stale_reasons or current['point7_readiness']=='BLOCK' else current['point7_readiness'],
                current_case_id=current['id'],current_fresh=not stale_reasons,
                acceptance_granted=False,final_audit='NOT_RUN')

"""User-authored ТЗ checklist and deterministic source gates, never acceptance."""
import time
import uuid
import json
from .analysis_identity import digest
from .source_binding import validate_candidate


def create_set(store,session_id,*,text,source_evidence_ids=None):
    if not isinstance(text,str) or not text.strip() or len(text)>50000:raise ValueError('ТЗ checklist must contain 1–50000 characters')
    lines=[line.strip() for line in text.splitlines() if line.strip()]
    if not 1<=len(lines)<=50 or any(len(line)>2000 for line in lines):raise ValueError('ТЗ: 1–50 requirements, each up to 2000 characters')
    source_evidence_ids=[] if source_evidence_ids is None else source_evidence_ids
    if not isinstance(source_evidence_ids,list) or len(source_evidence_ids)>20 or any(not isinstance(e,str) for e in source_evidence_ids) or len(set(source_evidence_ids))!=len(source_evidence_ids):raise ValueError('Select at most20 distinct ToR source candidates')
    state=store.snapshot(session_id);candidates={r['id']:r for r in state['evidence']};bases=[]
    for eid in source_evidence_ids:
        base=store.get_evidence(session_id,eid);current=candidates[eid]
        bases.append(dict(candidate_id=eid,candidate_sha256=digest(base),review_revision=current['review_revision'],review_event_id=(current['latest_review'] or {}).get('id')))
    store.requirements_state(session_id)
    return store.add_requirement_set(dict(id=str(uuid.uuid4()),session_id=session_id,created=time.time(),
        requirements=[dict(id=str(uuid.uuid4()),text=line) for line in lines],origin='USER_AUTHORED_CHECKLIST',scope='UNVERIFIED_TZ',source_bases=bases,acceptance_granted=False))


def assess(store,session_id,*,set_id,requirement_id,expected_revision,conclusion,evidence_ids,relation,actor=None):
    if type(expected_revision) is not int or expected_revision<0:raise ValueError('Assessment revision required')
    if not isinstance(conclusion,str) or not conclusion.strip() or len(conclusion)>2000:raise ValueError('Conclusion must contain 1–2000 characters')
    if relation not in {'SUPPORTS','CONTRADICTS','UNKNOWN'}:raise ValueError('Invalid source relation')
    if not isinstance(evidence_ids,list) or len(evidence_ids)>20 or any(not isinstance(e,str) for e in evidence_ids) or len(set(evidence_ids))!=len(evidence_ids):raise ValueError('Select at most 20 distinct evidence candidates')
    if actor is not None and (not isinstance(actor,str) or not actor.strip() or len(actor)>120):raise ValueError('Assessment actor must contain1–120 characters')
    sources=[]
    candidates={r['id']:r for r in store.snapshot(session_id)['evidence']}
    for eid in evidence_ids:
        r=store.get_evidence(session_id,eid);current=candidates[eid]
        sources.append(dict(candidate_id=eid,candidate_sha256=digest(r),review_revision=current['review_revision'],review_event_id=current['latest_review']['id'] if current['latest_review'] else None))
    event=dict(id=str(uuid.uuid4()),session_id=session_id,set_id=set_id,requirement_id=requirement_id,conclusion=conclusion.strip(),relation=relation,sources=sources,created=time.time(),
               origin='USER_AUTHORED_ASSESSMENT',actor=actor.strip() if actor is not None else None,actor_verified=False,engineering_verified=False,acceptance_granted=False)
    return store.add_requirement_assessment(session_id,event,expected_revision)


def source_check(store,session_id,r,expected=None,selected_files=None):
    reasons=[]
    base=store.get_evidence(session_id,r['id'])
    if expected and (digest(base)!=expected['candidate_sha256'] or r['review_revision']!=expected['review_revision'] or (r['latest_review'] or {}).get('id')!=expected['review_event_id']):reasons.append('SOURCE_REVIEW_CHANGED')
    if selected_files is not None and r['file_id'] not in selected_files:reasons.append('SOURCE_NOT_SELECTED')
    if r['source_match']!='MATCH':reasons.append('QUOTE_NOT_MATCHED')
    if not r['latest_review'] or r['latest_review']['decision']!='SOURCE_CONFIRMED':reasons.append('SOURCE_NOT_CONFIRMED')
    elif r['latest_review'].get('candidate_digest')!=digest(base):reasons.append('SOURCE_REVIEW_BASIS_CHANGED')
    if r['name'].lower().endswith('.pdf') and (r.get('provenance') or {}).get('status')!='UNIQUE':reasons.append('PDF_LOCATION_NOT_UNIQUE')
    if base.get('source_confirmable') is False:reasons.append('SOURCE_LOCATION_UNVERIFIED')
    try:validate_candidate(store,session_id,base,require_confirmable=False)
    except Exception:reasons.append('SOURCE_IDENTITY_OR_LOCATION_CHANGED')
    return dict(candidate_id=r['id'],file_id=r['file_id'],quote=r['quote'],statement=r['statement'],page=r['page'],locator=r.get('locator'),
        data_class=r['data_class'],data_class_verified=False,source_sha256=r['source_sha256'],review_revision=r['review_revision'],
        review_event_id=(r['latest_review'] or {}).get('id'),reviewer=(r['latest_review'] or {}).get('actor'),reviewer_verified=False,status='BLOCK' if reasons else 'SOURCE_REVIEWED',reasons=reasons,
        limitations=(r.get('source_binding') or {}).get('limitations',[]),scope='SOURCE_REVIEW_ONLY',acceptance_granted=False)


def report(store,session_id,*,selected_files=None):
    state=store.requirements_state(session_id);sets=state['sets'];current=sets[-1] if sets else None
    if current is None:return dict(set_id=None,requirements=[],status='BLOCK',reasons=['TZ_CHECKLIST_MISSING'],scope='REQUIREMENT_TRACEABILITY_ONLY',acceptance_granted=False,final_audit='NOT_RUN')
    candidates={r['id']:r for r in store.snapshot(session_id)['evidence']};rows=[]
    tor_sources=[]
    for expected in current.get('source_bases',[]):
        source=candidates.get(expected['candidate_id'])
        if source:tor_sources.append(source_check(store,session_id,source,expected,selected_files))
        else:tor_sources.append(dict(candidate_id=expected['candidate_id'],status='BLOCK',reasons=['CANDIDATE_MISSING']))
    tor_status='SOURCE_REVIEWED' if tor_sources and all(s['status']!='BLOCK' for s in tor_sources) else 'BLOCK'
    tor_reasons=list(dict.fromkeys(reason for s in tor_sources for reason in s['reasons'])) if tor_sources else ['TZ_SOURCE_NOT_BOUND']
    for requirement in current['requirements']:
        history=[e for e in state['assessments'] if e['set_id']==current['id'] and e['requirement_id']==requirement['id']]
        event=history[-1] if history else None;reasons=[];sources=[]
        if not event:reasons.append('NOT_ASSESSED')
        else:
            if not event['sources']:reasons.append('NO_SOURCE_CANDIDATES')
            if event['relation']=='CONTRADICTS':reasons.append('DECLARED_CONTRADICTION')
            if event['relation']=='UNKNOWN':reasons.append('RELATION_UNKNOWN')
            for expected in event['sources']:
                r=candidates.get(expected['candidate_id'])
                if r is None:reasons.append('CANDIDATE_MISSING');continue
                checked=source_check(store,session_id,r,expected,selected_files);sources.append(checked);reasons.extend(checked['reasons'])
        linked=bool(event and sources and not reasons)
        if linked:reasons=['ENGINEERING_VERIFICATION_REQUIRED','DATA_CLASS_NOT_VERIFIED']
        rows.append(dict(requirement,status='UNCERTAINTY' if linked else 'BLOCK',traceability='SOURCE_LINKED' if linked else 'NOT_ESTABLISHED',
            assessment_actor=event.get('actor') if event else None,assessment_actor_verified=False,conclusion=event['conclusion'] if event else None,relation=event['relation'] if event else 'UNKNOWN',revision=event['revision'] if event else 0,
            sources=sources,history=history,reasons=list(dict.fromkeys(reasons)),acceptance_granted=False))
    return dict(set_id=current['id'],requirements=rows,set_versions=len(sets),tor_sources=tor_sources,tor_source_status=tor_status,tor_source_reasons=tor_reasons,tor_transcription_verified=False,status='BLOCK' if any(r['status']=='BLOCK' for r in rows) else 'UNCERTAINTY',
        scope='REQUIREMENT_TRACEABILITY_ONLY',engineering_verified=False,acceptance_granted=False,final_audit='NOT_RUN')


def context(store,session_id,selected_files):
    result=report(store,session_id,selected_files=selected_files);items=[];budget=14000
    for r in result['requirements']:
        row={k:v for k,v in r.items() if k!='history'};cost=len(json.dumps(row,ensure_ascii=False))
        if cost>budget:break
        items.append(row);budget-=cost
    tor=[dict(s,quote=s.get('quote','')[:1000],statement=s.get('statement','')[:1000]) for s in result.get('tor_sources',[])[:5]]
    clipped=len(tor)<len(result.get('tor_sources',[])) or any(len(s.get('quote',''))>1000 or len(s.get('statement',''))>1000 for s in result.get('tor_sources',[]))
    return dict(result,tor_sources=tor,requirements=items,total_requirements=len(result['requirements']),context_truncated=clipped or len(items)<len(result['requirements']))


def finding_gates(store,session_id,findings,selected_files):
    candidates={r['id']:r for r in store.snapshot(session_id)['evidence']};out=[]
    for finding in findings:
        refs=finding['source_ids'];sources=[source_check(store,session_id,candidates[e],selected_files=selected_files) for e in refs if e in candidates]
        reasons=[reason for s in sources for reason in s['reasons']]
        if not sources:reasons.append('NO_CANDIDATE_REFERENCE')
        if any(e not in candidates for e in refs):reasons.append('ORIGINAL_REFERENCE_ONLY')
        linked=bool(sources and not reasons)
        out.append(dict(text=finding['text'],source_ids=refs,sources=sources,traceability='SOURCE_LINKED' if linked else 'NOT_ESTABLISHED',
            status='UNCERTAINTY' if linked else 'BLOCK',reasons=reasons or ['ENGINEERING_VERIFICATION_REQUIRED'],acceptance_granted=False))
    return out

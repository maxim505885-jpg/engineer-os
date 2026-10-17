"""Explicit local responsible-review records, never model/import self-assertions.

The MAC authenticates local issuance, not civil identity or physical truth.
Initial supported Evidence class: PROJECT, with unchanged source/class review.
Other subject kinds fail closed until their domain prerequisites are implemented.
"""
from datetime import datetime,timezone
import copy
import hashlib
import hmac
import json
import os
from pathlib import Path
import secrets
import uuid
from .analysis_identity import digest
from .core_plan import verify_originals
from .lock import managed_file
from .store import identifier,ReviewConflict

INTENT='RESPONSIBLE_ENGINEERING_REVIEW'
DOMAIN=b'ENGINEER_OS_VERIFICATION_V1\x00'
MAX_EVENT_BYTES=2*1024**2
MAX_SESSION_BYTES=64*1024**2


def _signature(key,body):
    return hmac.new(key,DOMAIN+json.dumps(body,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode(),hashlib.sha256).hexdigest()


def provision_key(store,*,review_intent):
    if review_intent!='PROVISION_LOCAL_REVIEW_AUTHORITY':raise ValueError('Explicit provisioning intent required')
    key=store.verification_key()
    if key is not None:return dict(status='PASS',scope='LOCAL_ISSUER_KEY_ALREADY_PROVISIONED',acceptance_granted=False)
    with store.connection() as db:
        if db.execute('SELECT 1 FROM engineering_verifications LIMIT 1').fetchone():raise ValueError('KEY_LOST_EXISTING_RECORDS_REQUIRE_RECOVERY')
    path=store.root/'engineering-verification.key';managed_file(path)
    descriptor=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|getattr(os,'O_NOFOLLOW',0),0o600)
    with os.fdopen(descriptor,'wb') as stream:stream.write(secrets.token_bytes(32));stream.flush();os.fsync(stream.fileno())
    return dict(status='PASS',scope='LOCAL_ISSUER_KEY_PROVISIONED_NOT_ENGINEERING_ACCEPTANCE',acceptance_granted=False)


def review_catalog(store,session_id):
    snapshot=store.snapshot(session_id);requirements=store.requirements_state(session_id)
    subjects=[dict(kind='EVIDENCE',id=row['id'],label=row['data_class']+' · '+row['statement'][:150]) for row in snapshot['evidence']]
    if requirements['sets']:
        current=requirements['sets'][-1]
        subjects.insert(0,dict(kind='REQUIREMENTS',id=current['id'],label='Current ToR · '+str(len(current['requirements']))+' requirements'))
    for job in snapshot['jobs']:
        if job['mode']=='CORE_RUN' and job['state']=='SUCCEEDED':
            for row in ((job.get('result') or {}).get('core_run') or {}).get('results',[]):
                subjects.append(dict(kind='SPECIALIST',id=job['id']+':'+row['agent'],label=row.get('label',row['agent'])+' · '+job['id'][:8]))
    return dict(subjects=subjects,supported_kinds=['EVIDENCE','REQUIREMENTS','SPECIALIST'],
        key_provisioned=store.verification_key() is not None,acceptance_granted=False,
        limitations=['PROJECT_CLASS_ONLY','COMPLETE_PLAINTEXT_TOR_ONLY','PROJECT_PLAINTEXT_REPORT_REVIEW_ONLY','DOMAIN_ISSUANCE_NOT_IMPLEMENTED'])


def verification_stamp(store,session_id):
    identifier(session_id)
    stamp=hashlib.sha256(b'ENGINEER_OS_REVIEW_CONTEXT_V1\x00')
    stamp.update(hashlib.sha256(Path(__file__).read_bytes()).digest())
    key=store.verification_key();stamp.update(hashlib.sha256(key).digest() if key is not None else b'NO_KEY')
    with store.connection() as db:
        for row in db.execute('SELECT id,subject_kind,subject_id,revision,record FROM engineering_verifications WHERE session_id=? ORDER BY subject_kind,subject_id,revision',(session_id,)):
            stamp.update(json.dumps(list(row),ensure_ascii=False,separators=(',',':')).encode());stamp.update(b'\n')
    return stamp.hexdigest()


def _subject(store,session_id,kind,subject_id):
    identifier(session_id)
    if kind=='SPECIALIST':return _specialist_subject(store,session_id,subject_id)
    identifier(subject_id)
    if kind=='REQUIREMENTS':return _requirements_subject(store,session_id,subject_id)
    if kind!='EVIDENCE':raise ValueError('VERIFICATION_SUBJECT_KIND_NOT_IMPLEMENTED')
    from .requirements import source_check
    snapshot=store.snapshot(session_id)
    candidate=next((row for row in snapshot['evidence'] if row['id']==subject_id),None)
    if candidate is None:raise ValueError('Verification subject not found in this conversation')
    checked=source_check(store,session_id,candidate)
    reasons=list(checked['reasons'])
    if candidate['data_class']=='U':reasons.append('DATA_CLASS_UNKNOWN')
    elif candidate['data_class']!='P':reasons.append('EVIDENCE_DATA_CLASS_QUALIFICATION_NOT_IMPLEMENTED')
    source=store.get_file(candidate['file_id'])
    try:verify_originals([source])
    except (OSError,ValueError):reasons.append('VERIFICATION_SOURCE_CHANGED')
    subject=dict(candidate_id=candidate['id'],file_id=candidate['file_id'],source_sha256=candidate['source_sha256'],
        data_class=candidate['data_class'],review_revision=candidate['review_revision'],
        review_event_id=(candidate['latest_review'] or {}).get('id'),status=checked['status'],reasons=checked['reasons'])
    # Bind full quotation/statement/locator, not only the case's compact row.
    base=dict(subject=subject,candidate=candidate,sources=[[source['id'],source['sha256'],source['size']]],
        implementation_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    return subject,[source['id']],list(dict.fromkeys(reasons)),digest(base)


def _requirements_subject(store,session_id,subject_id):
    from .requirements import report
    subject=report(store,session_id,apply_verification=False)
    if subject.get('set_id')!=subject_id:raise ValueError('Current requirements subject required')
    reasons=list(subject.get('reasons',[]));rows=subject['requirements'];candidates={r['id']:r for r in store.snapshot(session_id)['evidence']}
    source_ids={r['candidate_id'] for r in subject.get('tor_sources',[])}
    for row in rows:
        if row['status']=='BLOCK' or row['traceability']!='SOURCE_LINKED' or row['relation']!='SUPPORTS':reasons.extend(row['reasons'] or ['REQUIREMENT_NOT_SUPPORTED'])
        source_ids.update(r['candidate_id'] for r in row['sources'])
    if not rows or not source_ids:reasons.append('REQUIREMENT_SOURCES_REQUIRED')
    if subject.get('tor_source_status')!='SOURCE_REVIEWED':reasons.append('TOR_SOURCE_NOT_REVIEWED')
    dependencies=[];refs=set()
    for candidate_id in sorted(source_ids):
        state=review_subject(store,session_id,'EVIDENCE',candidate_id)
        refs.update(state['source_refs'])
        if state['verified_subject'] is None:reasons.append('REQUIREMENT_EVIDENCE_VERIFICATION_REQUIRED')
        else:
            record=state['verified_subject']['engineering_verification']
            dependencies.append([candidate_id,record['verification_id'],record['signature']])
    # Plaintext full-source transcription can be checked deterministically here.
    # Rich Office/PDF/image-only ToR requires T04 source-layout qualification;
    # a reviewer string or partial quotation cannot bypass that missing proof.
    tor=subject.get('tor_sources',[]);transcription=False
    if len(tor)==1 and tor[0]['candidate_id'] in candidates:
        candidate=candidates[tor[0]['candidate_id']];source=store.get_file(candidate['file_id']);path=Path(source['path'])
        if Path(source['name']).suffix.lower() in ('.txt','.md') and source['size']<=65536:
            try:
                verify_originals([source]);text=path.read_bytes().decode('utf-8-sig')
                transcription=(candidate['quote'].strip()==text.strip() and [r['text'] for r in rows]==[line.strip() for line in text.splitlines() if line.strip()])
            except (OSError,ValueError):pass
    if not transcription:reasons.append('TZ_TRANSCRIPTION_QUALIFICATION_REQUIRED')
    basis=digest(dict(subject=subject,dependencies=dependencies,
        implementation_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()))
    return subject,sorted(refs),list(dict.fromkeys(reasons)),basis


def _enrich(base,kind,decision):
    value=copy.deepcopy(base);value['engineering_verified']=True
    if kind=='EVIDENCE':value['data_class_verified']=True
    elif kind=='REQUIREMENTS':
        value.update(tor_transcription_verified=True,status=decision,reasons=[])
        for row in value['requirements']:row.update(engineering_verified=True,status=decision,reasons=[])
    elif kind=='SPECIALIST':value['status']=decision
    return value


def _specialist_subject(store,session_id,subject_id):
    if not isinstance(subject_id,str) or subject_id.count(':')!=1:raise ValueError('SPECIALIST_JOB_AND_ROLE_REQUIRED')
    job_id,agent=subject_id.split(':');identifier(job_id)
    snapshot=store.snapshot(session_id);job=next((row for row in snapshot['jobs'] if row['id']==job_id),None)
    if job is None:raise ValueError('CORE job not found in this conversation')
    result=job.get('result') or {};run=result.get('core_run') or {}
    subject=next((row for row in run.get('results',[]) if row['agent']==agent),None)
    if subject is None:raise ValueError('Specialist role not found')
    reasons=[];dependencies=[]
    if job['mode']!='CORE_RUN' or job['state']!='SUCCEEDED' or not run.get('analysis_complete'):reasons.append('SPECIALIST_CORE_NOT_COMPLETE')
    if set(job['requested_checks'])!={'report'}:reasons.append('SPECIALIST_SCOPE_NOT_QUALIFIED')
    if subject.get('execution')!='COMPLETED' or subject.get('status') in ('BLOCK','ERROR'):reasons.append('SPECIALIST_RESULT_NOT_READY')
    if (run.get('engineering_review') or {}).get('status')=='BLOCK':reasons.append('SPECIALIST_ENGINEERING_RECONCILIATION_BLOCKED')
    if result.get('context_truncated'):reasons.append('SPECIALIST_CONTEXT_INCOMPLETE')
    from .requirements import report
    requirements=report(store,session_id,selected_files=job['file_ids'])
    if requirements.get('engineering_verified') is not True:reasons.append('SPECIALIST_REQUIREMENTS_REVIEW_REQUIRED')
    else:dependencies.append(requirements['engineering_verification']['signature'])
    if digest(result.get('requirements_report'))!=digest(requirements):reasons.append('SPECIALIST_REQUIREMENTS_CHANGED_SINCE_ANALYSIS')
    from .domain_packets import report as domain_report
    domains=domain_report(store,session_id,selected_files=job['file_ids'])
    if domains['packets']:reasons.append('SPECIALIST_DOMAIN_QUALIFICATION_NOT_IMPLEMENTED')
    candidates={row['id']:row for row in snapshot['evidence']}
    evidence_ids=set()
    for finding in subject.get('findings',[]):
        if finding.get('relation')!='SUPPORTS' or not finding.get('requirement_ids'):reasons.append('SPECIALIST_FINDING_NOT_REQUIREMENT_BOUND')
        evidence_ids.update(finding.get('source_ids',[]))
    for gate in subject.get('finding_gates',[]):
        if gate['status']=='BLOCK':reasons.append('SPECIALIST_SOURCE_GATE_BLOCKED')
    if not evidence_ids:reasons.append('SPECIALIST_SOURCE_REFERENCES_REQUIRED')
    for candidate_id in sorted(evidence_ids):
        if candidate_id not in candidates:reasons.append('SPECIALIST_REQUIRES_REVIEWED_EVIDENCE');continue
        state=review_subject(store,session_id,'EVIDENCE',candidate_id)
        if state['verified_subject'] is None:reasons.append('SPECIALIST_EVIDENCE_VERIFICATION_REQUIRED')
        else:dependencies.append(state['verified_subject']['engineering_verification']['signature'])
    files=[store.get_file(fid) for fid in job['file_ids']]
    for source in files:
        if Path(source['name']).suffix.lower() not in ('.txt','.md') or source['size']>65536 or source['text_truncated']:
            reasons.append('SPECIALIST_DOCUMENT_QUALIFICATION_REQUIRED');continue
        try:
            verify_originals([source])
            if Path(source['path']).read_bytes().decode('utf-8-sig').strip()!=source['text'].strip():reasons.append('SPECIALIST_SOURCE_TEXT_CHANGED')
        except (OSError,ValueError):reasons.append('SPECIALIST_SOURCE_CHANGED')
    basis=digest(dict(subject=subject,job_id=job_id,job_result_sha256=digest(result),dependencies=dependencies,
        sources=[[f['id'],f['sha256'],f['size']] for f in files],implementation_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()))
    return subject,sorted(f['id'] for f in files),list(dict.fromkeys(reasons)),basis


def _latest(store,session_id,kind,subject_id,db=None):
    def read(connection):
        row=connection.execute('SELECT record FROM engineering_verifications WHERE session_id=? AND subject_kind=? AND subject_id=? ORDER BY revision DESC LIMIT 1',(session_id,kind,subject_id)).fetchone()
        return json.loads(row['record']) if row else None
    if db is not None:return read(db)
    with store.connection() as connection:return read(connection)


def _overlay(store,session_id,kind,subject_id,base,basis,event,reasons):
    if event is None or reasons:return None
    try:
        signed=event['subject'];record=signed['engineering_verification'];key=store.verification_key()
        if key is None or event['decision'] not in ('ACCEPTED','ACCEPTED ALTERNATIVE'):return None
        if (event['session_id'],event['subject_kind'],event['subject_id'],event['basis_sha256'])!=(session_id,kind,subject_id,basis):return None
        if (record['session_id'],record['subject_kind'],record['subject_id'],record['basis_sha256'],record['verification_id'],record['revision'])!=(session_id,kind,subject_id,basis,event['id'],event['revision']):return None
        expected=_enrich(base,kind,event['decision'])
        if {k:v for k,v in signed.items() if k!='engineering_verification'}!=expected:return None
        if record['subject_sha256']!=digest(expected) or record['decision']!=event['decision']:return None
        if not hmac.compare_digest(record['signature'],_signature(key,{k:v for k,v in record.items() if k!='signature'})):return None
        return signed
    except (KeyError,TypeError,ValueError):return None


def review_subject(store,session_id,subject_kind,subject_id):
    base,refs,reasons,basis=_subject(store,session_id,subject_kind,subject_id)
    event=_latest(store,session_id,subject_kind,subject_id)
    revision=event['revision'] if event else 0
    candidates=store.snapshot(session_id)['evidence']
    ids=({subject_id} if subject_kind=='EVIDENCE' else {source for finding in base.get('findings',[]) for source in finding.get('source_ids',[])} if subject_kind=='SPECIALIST' else {r['candidate_id'] for r in base.get('tor_sources',[])}|{r['candidate_id'] for row in base.get('requirements',[]) for r in row['sources']})
    context=[{key:row.get(key) for key in ('id','file_id','name','quote','statement','page','locator','data_class','source_sha256')} for row in candidates if row['id'] in ids]
    return dict(subject=base,source_refs=refs,source_context=context,prerequisite_reasons=reasons,basis_sha256=basis,
        event_revision=revision,expected_revision=digest([basis,revision]),
        verified_subject=_overlay(store,session_id,subject_kind,subject_id,base,basis,event,reasons),
        scope='LOCAL_RESPONSIBLE_REVIEW_NOT_CIVIL_IDENTITY',acceptance_granted=False)


def issue_verification(store,session_id,*,subject_kind,subject_id,expected_revision,
        decision,reviewer,method,source_refs,reason,review_intent):
    if review_intent!=INTENT:raise ValueError('Explicit responsible review intent required')
    if decision not in ('ACCEPTED','ACCEPTED ALTERNATIVE','REVOKED'):raise ValueError('Invalid responsible review decision')
    for name,value,limit in (('reviewer',reviewer,120),('method',method,2000),('reason',reason,4000)):
        if not isinstance(value,str) or not value.strip() or len(value)>limit:raise ValueError('Bounded '+name+' required')
    key=store.verification_key()
    if key is None:raise ValueError('LOCAL_REVIEW_KEY_NOT_PROVISIONED')
    from .build_identity import runtime_report
    if runtime_report(store)['status']=='BLOCK':raise ValueError('REVIEW_BUILD_IDENTITY_CHANGED')
    with store.connection() as db:
        db.execute('BEGIN IMMEDIATE')
        state=review_subject(store,session_id,subject_kind,subject_id)
        if state['expected_revision']!=expected_revision:raise ReviewConflict('Review basis changed; reopen before signing')
        if state['prerequisite_reasons'] and decision!='REVOKED':raise ValueError('VERIFICATION_PREREQUISITES_OPEN')
        if not isinstance(source_refs,list) or source_refs!=state['source_refs']:raise ValueError('Exact responsible source references required')
        if db.execute('SELECT count(*) FROM engineering_verifications WHERE session_id=?',(session_id,)).fetchone()[0]>=10000:raise ValueError('Verification history limit')
        event_id=str(uuid.uuid4());revision=state['event_revision']+1
        subject=copy.deepcopy(state['subject']) if decision=='REVOKED' else _enrich(state['subject'],subject_kind,decision)
        record=dict(decision=decision,reviewer=reviewer.strip(),method=method.strip(),reason=reason.strip(),
            version='1',verified_at=datetime.now(timezone.utc).isoformat(),source_refs=source_refs,
            subject_sha256=digest(subject),session_id=session_id,subject_kind=subject_kind,subject_id=subject_id,
            basis_sha256=state['basis_sha256'],verification_id=event_id,revision=revision,
            scope='LOCAL_RESPONSIBLE_REVIEW_NOT_CIVIL_IDENTITY',reviewer_identity_verified=False)
        record['verified_scope']={'EVIDENCE':'PROJECT_DECLARATION_CLASS_ONLY','REQUIREMENTS':'COMPLETE_PLAINTEXT_TOR_TRACEABILITY_ONLY','SPECIALIST':'PROJECT_PLAINTEXT_REPORT_REVIEW_ONLY'}[subject_kind]
        record['signature']=_signature(key,record);subject['engineering_verification']=record
        event=dict(id=event_id,session_id=session_id,subject_kind=subject_kind,subject_id=subject_id,
            revision=revision,basis_sha256=state['basis_sha256'],decision=decision,subject=subject,acceptance_granted=False)
        encoded=json.dumps(event,ensure_ascii=False,allow_nan=False)
        if len(encoded.encode('utf-8'))>MAX_EVENT_BYTES:raise ValueError('Verification record size limit')
        used=db.execute('SELECT coalesce(sum(length(cast(record AS BLOB))),0) FROM engineering_verifications WHERE session_id=?',(session_id,)).fetchone()[0]
        if used+len(encoded.encode('utf-8'))>MAX_SESSION_BYTES:raise ValueError('Verification history byte limit')
        db.execute('INSERT INTO engineering_verifications VALUES(?,?,?,?,?,?)',(event_id,session_id,subject_kind,subject_id,revision,encoded))
    return event


def revalidate_verification(store,record):
    try:
        state=review_subject(store,record['session_id'],record['subject_kind'],record['subject_id'])
        subject=state['verified_subject']
        valid=subject is not None and subject['engineering_verification']['verification_id']==record['id']
    except (KeyError,TypeError,ValueError,OSError):valid=False
    return dict(status='PASS' if valid else 'BLOCK',current=valid,scope='LOCAL_REVIEW_RECORD_FRESHNESS',acceptance_granted=False)


def overlay_evidence(store,session_id,subject):
    """Only current locally issued review can enrich the exact compact case row."""
    return overlay_subject(store,session_id,'EVIDENCE',subject['candidate_id'],subject)


def overlay_subject(store,session_id,kind,subject_id,subject):
    if _latest(store,session_id,kind,subject_id) is None:return subject
    state=review_subject(store,session_id,kind,subject_id)
    if state['subject']!=subject:return subject
    return state['verified_subject'] or subject

"""Bounded local knowledge: exact accepted origins, explicit session scope.

Recall is context, never evidence or acceptance for another object. Immutable
revision metadata survives content deletion; content is stored separately so a
DELETE removes it from every revision. Previously exported/backed-up copies
are outside this operation and cannot be retroactively erased.

Each source session has at most 1000 promotion events. A promotion permits at
most one subsequent revoke, and each knowledge ID permits one terminal delete,
so complete metadata history is bounded by 3000 revisions. Withdrawals do not
consume the promotion budget; full promotion capacity still permits deletion.
Recall excludes unavailable sources independently, without stopping others.
Scope and origin metadata are authenticated with the already provisioned local
verification key; active unsigned or altered revisions cannot authorize recall.
The MAC authenticates storage integrity, not civil identity or engineering truth.
Report/export fail closed for altered metadata or an unavailable key. Deletion
can still purge payload after key loss; its unsigned tombstone does not claim
integrity and causes export verification to report an error.
"""
from __future__ import annotations
import hashlib
import hmac
import json
import time
import uuid
from .store import identifier, ReviewConflict

MAX_RECORDS=1000
MAX_PROMOTIONS=1000
MAX_HISTORY=3*MAX_PROMOTIONS

def _digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()

def _metadata_mac(row,key):
    if not isinstance(key,bytes) or len(key)!=32:raise ValueError('Local verification key required for confirmed knowledge')
    metadata={k:v for k,v in row.items() if k not in {'metadata_mac','title','evidence','target_session_id','trust'}}
    body=json.dumps(metadata,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()
    return hmac.new(key,b'ENGINEER_OS_KNOWLEDGE_V1\x00'+body,hashlib.sha256).hexdigest()

def _metadata_verified(row,key):
    signature=row.get('metadata_mac')
    if not isinstance(signature,str):return False
    try:return hmac.compare_digest(signature,_metadata_mac(row,key))
    except (ValueError,TypeError):return False

def _text(value,name,limit):
    if not isinstance(value,str) or not value.strip() or len(value)>limit:raise ValueError(name+' is required or too long')
    return value.strip()

def _session(db,sid):
    identifier(sid)
    if db.execute('SELECT id FROM sessions WHERE id=?',(sid,)).fetchone() is None:raise ValueError('Conversation not found')

def _authority(store,sid):
    from .final_audit import report as audit_report
    from .real_case import report as case_report
    r=audit_report(store,sid)
    if r.get('status')!='ACCEPTED' or r.get('acceptance_granted') is not True or r.get('current_fresh') is not True:
        raise ValueError('A fresh accepted FINAL AUDIT is required')
    audits=r.get('audits') or [];audit=audits[-1] if audits else None
    case=next((x for x in case_report(store,sid).get('cases',[]) if x.get('current')),None)
    if (not audit or not case or audit.get('effective_acceptance_granted') is not True
            or audit.get('fresh') is not True or audit.get('effective_decision')!='ACCEPTED'
            or audit.get('id')!=r.get('current_audit_id') or audit.get('case_id')!=case.get('id')
            or audit.get('case_sha256')!=case.get('case_sha256')):
        raise ValueError('Accepted audit origin does not match the current case')
    return audit,case

def _latest(db,kid,sid):
    identifier(kid)
    row=db.execute('SELECT record FROM knowledge_revisions WHERE id=? AND source_session_id=? ORDER BY revision DESC LIMIT 1',(kid,sid)).fetchone()
    if row is None:raise ValueError('Knowledge not found in source conversation')
    return json.loads(row['record'])

def _append(db,row,content=None):
    if db.execute('SELECT count(*) FROM knowledge_revisions WHERE source_session_id=?',(row['source_session_id'],)).fetchone()[0]>=MAX_HISTORY:
        raise ValueError('Knowledge history exceeds supported capacity')
    db.execute('INSERT INTO knowledge_revisions VALUES(?,?,?,?)',(row['id'],row['revision'],row['source_session_id'],json.dumps(row,ensure_ascii=False)))
    if content is not None:db.execute('INSERT INTO knowledge_content VALUES(?,?,?)',(row['id'],row['revision'],json.dumps(content,ensure_ascii=False)))
    return dict(row,**(content or dict(title='',evidence=[])))

def _rows(store,sid):
    with store.connection() as db:
        _session(db,sid)
        rows=db.execute('SELECT r.record,c.content FROM knowledge_revisions r LEFT JOIN knowledge_content c USING(id,revision) WHERE r.source_session_id=? ORDER BY r.id,r.revision LIMIT ?', (sid,MAX_HISTORY+1)).fetchall()
    if len(rows)>MAX_HISTORY:raise ValueError('Knowledge export exceeds supported capacity')
    result=[]
    metadata=[json.loads(row['record']) for row in rows]
    if any(not isinstance(meta,dict) for meta in metadata):raise ValueError('Invalid knowledge metadata')
    deleted={meta.get('id') for meta in metadata if meta.get('state')=='DELETED'}
    for row,meta in zip(rows,metadata):
        content=json.loads(row['content']) if row['content'] else dict(title='',evidence=[])
        if not isinstance(content,dict):raise ValueError('Invalid knowledge payload')
        if meta.get('source_session_id')!=sid or not _metadata_verified(meta,store.verification_key()):raise ValueError('Knowledge metadata integrity or verification key unavailable')
        if meta.get('state')=='ACTIVE' and not row['content'] and meta['id'] not in deleted:raise ValueError('Active knowledge content missing')
        if row['content'] and _digest(content)!=meta.get('content_sha256'):raise ValueError('Knowledge content integrity failed')
        result.append(dict(meta,**content))
    return result

def promote(store,source_session_id,*,expected_audit_id,title,evidence_ids,scope_session_ids=None,knowledge_id=None,expected_revision=0,actor):
    """Derive a reference from exact checked evidence; no caller supplied body."""
    identifier(source_session_id);identifier(expected_audit_id)
    title=_text(title,'title',200);actor=_text(actor,'actor',200)
    if type(expected_revision) is not int or expected_revision<0:raise ValueError('Invalid revision')
    if not isinstance(evidence_ids,list) or not 1<=len(evidence_ids)<=100 or any(not isinstance(x,str) for x in evidence_ids) or len(set(evidence_ids))!=len(evidence_ids):raise ValueError('Select 1–100 distinct evidence IDs')
    for eid in evidence_ids:identifier(eid)
    scope=[source_session_id] if scope_session_ids is None else scope_session_ids
    if not isinstance(scope,list) or not 1<=len(scope)<=100 or any(not isinstance(x,str) for x in scope) or len(set(scope))!=len(scope):raise ValueError('Explicit distinct session scope required')
    for sid in scope:identifier(sid)
    audit,case=_authority(store,source_session_id)
    if audit['id']!=expected_audit_id:raise ReviewConflict('FINAL AUDIT changed')
    evidence=[]
    for eid in evidence_ids:
        matches=[x for x in case.get('evidence',[]) if x.get('candidate_id',x.get('id'))==eid]
        if len(matches)!=1 or matches[0].get('engineering_verified') is not True:raise ValueError('Evidence is not checked in the accepted case')
        evidence.append(matches[0])
    content=dict(title=title,evidence=evidence)
    if len(json.dumps(content,ensure_ascii=False))>262144:raise ValueError('Knowledge content exceeds supported capacity')
    with store.connection() as db:
        db.execute('BEGIN IMMEDIATE');_session(db,source_session_id)
        for sid in scope:_session(db,sid)
        if knowledge_id is None:
            if expected_revision!=0:raise ReviewConflict('New knowledge requires revision zero')
            knowledge_id=str(uuid.uuid4());revision=1
        else:
            old=_latest(db,knowledge_id,source_session_id)
            if old['revision']!=expected_revision:raise ReviewConflict('Knowledge revision changed')
            if old['state']=='DELETED':raise ValueError('Deleted knowledge cannot be restored')
            revision=expected_revision+1
        if db.execute("SELECT count(*) FROM knowledge_revisions WHERE source_session_id=? AND json_extract(record,'$.state')='ACTIVE'",(source_session_id,)).fetchone()[0]>=MAX_PROMOTIONS:
            raise ValueError('Knowledge capacity reached')
        row=dict(schema='ENGINEER_OS_KNOWLEDGE_V1',id=knowledge_id,revision=revision,source_session_id=source_session_id,
                 scope_session_ids=sorted(scope),audit_id=audit['id'],case_id=case['id'],case_sha256=case['case_sha256'],
                 audit_sha256=audit['audit_sha256'],content_sha256=_digest(content),evidence_ids=evidence_ids,
                 state='ACTIVE',created=time.time(),actor=actor,reason='',evidentiary_status='NOT_EVIDENCE',
                 acceptance_granted=False,mandatory_reverification=True)
        # Authority is recomputed after obtaining the writer lock; state changes
        # before this transaction cannot promote obsolete acceptance.
        current,_=_authority(store,source_session_id)
        if any(current.get(k)!=audit.get(k) for k in ('id','case_id','case_sha256','audit_sha256')):raise ReviewConflict('Accepted origin changed')
        row['metadata_mac']=_metadata_mac(row,store.verification_key())
        return _append(db,row,content)

def report(store,source_session_id):
    rows=_rows(store,source_session_id);latest={}
    for row in rows:latest[row['id']]=row
    return dict(schema='ENGINEER_OS_KNOWLEDGE_REPORT_V1',records=list(latest.values()),history_count=len(rows))

def recall(store,target_session_id,*,query=''):
    if not isinstance(query,str) or len(query)>1000:raise ValueError('Invalid recall query')
    with store.connection() as db:
        _session(db,target_session_id)
        sources=[r[0] for r in db.execute('SELECT DISTINCT source_session_id FROM knowledge_revisions')]
    records=[];blocked_sources=0
    for sid in sources:
        try:source_records=report(store,sid)['records']
        except (ValueError,KeyError,TypeError,OSError):
            blocked_sources+=1
            continue
        for row in source_records:
            if row['state']!='ACTIVE' or not _metadata_verified(row,store.verification_key()):continue
            if target_session_id not in row['scope_session_ids']:continue
            if query.strip().casefold() not in json.dumps(dict(title=row['title'],evidence=row['evidence']),ensure_ascii=False).casefold():continue
            try:audit,case=_authority(store,sid)
            except (ValueError,KeyError,OSError):continue
            if any(audit.get(key)!=row.get(target) for key,target in (('id','audit_id'),('case_id','case_id'),('case_sha256','case_sha256'),('audit_sha256','audit_sha256'))):continue
            # Stored payload hashes are not acceptance authority. Reconstruct
            # the selected evidence from the exact currently accepted case.
            selected=[];ids=row.get('evidence_ids')
            if not isinstance(ids,list) or not ids or any(not isinstance(eid,str) for eid in ids) or len(set(ids))!=len(ids):continue
            for eid in ids:
                matches=[item for item in case.get('evidence',[]) if item.get('candidate_id',item.get('id'))==eid]
                if len(matches)!=1 or matches[0].get('engineering_verified') is not True:break
                selected.append(matches[0])
            if len(selected)!=len(ids) or selected!=row.get('evidence'):continue
            records.append(dict(row,target_session_id=target_session_id,trust='CONFIRMED_REFERENCE',mandatory_reverification=True,
                                evidentiary_status='NOT_EVIDENCE',acceptance_granted=False))
            if len(records)>MAX_RECORDS:raise ValueError('Recall exceeds supported capacity')
    return dict(schema='ENGINEER_OS_KNOWLEDGE_RECALL_V1',records=records,blocked_source_count=blocked_sources,mandatory_reverification=True,evidentiary_status='NOT_EVIDENCE',acceptance_granted=False)

def _withdraw(store,source_session_id,knowledge_id,*,expected_revision,actor,reason,state):
    actor=_text(actor,'actor',200);reason=_text(reason,'reason',2000)
    if type(expected_revision) is not int or expected_revision<1:raise ValueError('Invalid revision')
    with store.connection() as db:
        db.execute('BEGIN IMMEDIATE');_session(db,source_session_id)
        old=_latest(db,knowledge_id,source_session_id)
        if old['revision']!=expected_revision:raise ReviewConflict('Knowledge revision changed')
        if old['state']=='DELETED':raise ValueError('Knowledge already deleted')
        if state=='REVOKED' and old['state']=='REVOKED':raise ValueError('Knowledge already revoked')
        row=dict(old,revision=expected_revision+1,state=state,actor=actor,reason=reason,created=time.time())
        # Withdrawal remains available if the key was lost; that row cannot
        # authorize recall. Never mint a replacement verification authority.
        key=store.verification_key()
        row['metadata_mac']=_metadata_mac(row,key) if key is not None else None
        result=_append(db,row)
        if state=='DELETED':
            db.execute('PRAGMA secure_delete=ON')
            db.execute('DELETE FROM knowledge_content WHERE id=?',(knowledge_id,))
        return result

def revoke(store,source_session_id,knowledge_id,*,expected_revision,actor,reason):
    return _withdraw(store,source_session_id,knowledge_id,expected_revision=expected_revision,actor=actor,reason=reason,state='REVOKED')

def delete(store,source_session_id,knowledge_id,*,expected_revision,actor,reason):
    return _withdraw(store,source_session_id,knowledge_id,expected_revision=expected_revision,actor=actor,reason=reason,state='DELETED')

def export(store,source_session_id):
    return dict(schema='ENGINEER_OS_KNOWLEDGE_EXPORT_V1',source_session_id=source_session_id,records=_rows(store,source_session_id),
                evidentiary_status='NOT_EVIDENCE',acceptance_granted=False,mandatory_reverification=True)

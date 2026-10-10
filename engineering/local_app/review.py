"""Append-only source review decisions, never engineering acceptance."""
from pathlib import Path
import time
import uuid


def record_review(store,session_id,candidate_id,*,expected_revision,decision,note,actor):
    if type(expected_revision) is not int or expected_revision<0:raise ValueError('Review revision must be a nonnegative integer')
    if not isinstance(decision,str) or decision not in {'SOURCE_CONFIRMED','REJECTED','NEEDS_DATA'}:raise ValueError('Invalid source review decision')
    for name,value,limit in [('note',note,2000),('actor',actor,120)]:
        if not isinstance(value,str) or not value.strip() or len(value)>limit:raise ValueError(name+' is required and exceeds limit')
    r=store.get_evidence(session_id,candidate_id);f=store.get_file(r['file_id'])
    if f['session_id']!=session_id or f['sha256']!=r['source_sha256']:raise ValueError('Original identity check failed')
    from .core_plan import verify_originals
    verify_originals([f])
    if decision=='SOURCE_CONFIRMED':
        from .source_binding import validate_candidate
        validate_candidate(store,session_id,r)
        if r['source_match']!='MATCH':raise ValueError('Unchecked quote cannot be confirmed as a source match')
        if Path(f['name']).suffix.lower()=='.pdf' and (r.get('provenance') or {}).get('status')!='UNIQUE':raise ValueError('PDF region must be unambiguous for source confirmation')
    event=dict(id=str(uuid.uuid4()),candidate_id=candidate_id,session_id=session_id,decision=decision,note=note.strip(),actor=actor.strip(),actor_verified=False,source_sha256=r['source_sha256'],scope='SOURCE_REVIEW_ONLY',acceptance_granted=False,created=time.time())
    return store.append_review(event,expected_revision)

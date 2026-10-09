"""Observed preview coverage, never a document completeness certificate."""


def unknown_coverage(reason='LEGACY_UNKNOWN'):
    return dict(scope='TEXT_PREVIEW_ONLY',status='UNKNOWN',method='UNKNOWN',
                total_pages=None,attempted_pages=None,pages_with_text=None,
                pages_without_text=[],unattempted_pages=None,page_records=[],
                source_chars=None,stored_chars=None,stop_reasons=[reason],
                completeness='NOT_CHECKED',ocr='NOT_RUN')


def summary(coverage):
    c=coverage or unknown_coverage()
    keys=('scope','status','method','total_pages','attempted_pages','pages_with_text',
          'pages_without_text','unattempted_pages','source_chars','stored_chars',
          'stop_reasons','completeness','ocr')
    return {key:c.get(key) for key in keys}


def incomplete(coverage):
    c=coverage or unknown_coverage()
    return c['status']=='UNKNOWN' or bool(c['stop_reasons'] or c['pages_without_text'])


def automatic_summary(source):
    result=dict(scope='UNVERIFIED_EXTRACTION',status='RECORDED',
                method=source['backend'].upper(),completeness='NOT_CHECKED',
                pages_without_text=source['pages_without_text'],
                **{key:source[key] for key in ('total_pages','processed_pages','blocked_pages','failed_pages','ocr')})
    if 'total_units' in source:
        result.update(total_pages=None,processed_pages=None,total_units=source['total_units'],processed_units=source['processed_units'],
                      unit_label=source['unit_label'],limitations=source.get('limitations',[]),physical_pages=None)
    return result


def source_dossier(store,session_id,file):
    """Observe one source's latest journal; never certify content completeness.

    Read the complete journal rather than the windowed UI or claimed counters.
    Its digest also binds text/coordinates that the compact dossier omits.
    """
    import hashlib
    import json
    from .analysis_identity import digest,parser_identity
    from .extraction import MAX_PAGES
    from .office import MAX_UNITS
    def bounded(value):
        if len(json.dumps(value,ensure_ascii=False))>32768:raise ValueError('Source coverage dossier limit exceeded')
        return value
    original=store.get_file(file['id'])
    if original['session_id']!=session_id:raise ValueError('Source outside conversation')
    result=dict(file_id=original['id'],source_sha256=original['sha256'],
                scope='TEXT_PREVIEW_ONLY',completeness='NOT_CHECKED',acceptance_granted=False,
                preview=summary(original.get('extraction_coverage')))
    with store.connection() as db:
        row=db.execute("SELECT * FROM jobs WHERE session_id=? AND mode LIKE 'EXTRACT_%' AND EXISTS (SELECT 1 FROM json_each(jobs.file_ids) WHERE value=?) ORDER BY created DESC,rowid DESC LIMIT 1",
                       (session_id,original['id'])).fetchone()
        if row is None:return bounded(result)
        job=store.job_dict(row);run=(job.get('result') or {}).get('extraction') or {}
        result.update(scope='UNVERIFIED_EXTRACTION',job_id=job['id'],job_state=job['state'],
                      journal_sha256=None,run_sha256=digest(run))
        if not run:
            result.update(status='UNKNOWN',limitations={'EXTRACTION_NOT_RECORDED':1})
            return bounded(result)
        logical='total_units' in run
        total=run.get('total_units' if logical else 'total_pages')
        if type(total) is not int or not 0<total<=(MAX_UNITS if logical else MAX_PAGES):raise ValueError('Invalid extraction extent')
        present=set();failed=blocked=images=vectors=0;limitations={};journal=hashlib.sha256()
        def record_limits(values):
            if not isinstance(values,list):raise ValueError('Invalid extraction limitations')
            for limitation in values:
                if not isinstance(limitation,str) or len(limitation)>240:raise ValueError('Invalid extraction limitation')
                limitations[limitation]=limitations.get(limitation,0)+1
                if len(limitations)>100:raise ValueError('Extraction limitation inventory limit exceeded')
        record_limits(run.get('limitations',[]))
        for page in db.execute('SELECT page,record FROM extraction_pages WHERE job_id=? ORDER BY page',(job['id'],)):
            raw=page['record'];record=json.loads(raw);number=page['page']
            journal.update(str(number).encode()+b':'+raw.encode()+b'\n')
            if record.get('page')!=number or not 1<=number<=total:raise ValueError('Invalid extraction journal identity')
            present.add(number)
            failed+=record.get('execution')=='FAILED';blocked+=record.get('status')=='BLOCK'
            if record.get('source_sha256')!=original['sha256']:
                limitations['PAGE_SOURCE_IDENTITY_CHANGED']=limitations.get('PAGE_SOURCE_IDENTITY_CHANGED',0)+1
            record_limits(record.get('limitations',[]))
            visual=record.get('visual_components') or {}
            images+=visual.get('images',0);vectors+=visual.get('vector_paths',0)
        missing=[]
        for number in range(1,total+1):
            if number in present:continue
            if missing and missing[-1][1]==number-1:missing[-1][1]=number
            else:missing.append([number,number])
    identity_reasons=[]
    if run.get('file_id')!=original['id'] or run.get('source_sha256')!=original['sha256']:
        identity_reasons.append('SOURCE_IDENTITY_CHANGED')
    try:
        if run.get('parser_identity')!=parser_identity(run.get('backend')):identity_reasons.append('PARSER_IDENTITY_CHANGED')
    except Exception:identity_reasons.append('PARSER_IDENTITY_UNAVAILABLE')
    result.update(status='RECORDED',backend=run.get('backend'),unit_kind='LOGICAL_UNIT' if logical else 'PAGE',
                  physical_pages=None if logical else total,total_units=total,processed_units=len(present),
                  missing_units=total-len(present),missing_ranges=missing[:100],missing_ranges_omitted=max(0,len(missing)-100),
                  failed_units=failed,blocked_units=blocked,limitations=limitations,
                  unverified_images=images,unverified_vector_paths=vectors,
                  journal_sha256=journal.hexdigest(),identity_reasons=identity_reasons)
    return bounded(result)

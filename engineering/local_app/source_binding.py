"""Revalidate logical Office locations against original bytes, never model text."""
import hashlib
from pathlib import Path
from .core_plan import verify_originals
from .analysis_identity import parser_identity,digest
from .office import read


def office_location(store,session_id,file,source_job,logical_unit,quote):
    return _office_location(store,session_id,file,source_job,logical_unit,quote)


def office_image_location(store,session_id,file,source_job,logical_unit):
    """Bind an original image asset without claiming a complete parent quote."""
    return _office_location(store,session_id,file,source_job,logical_unit,'',image_preview=True)


def _office_location(store,session_id,file,source_job,logical_unit,quote,*,image_preview=False):
    if file['session_id']!=session_id:raise ValueError('Source isolation failure')
    if type(logical_unit) is not int or logical_unit<1:raise ValueError('Office logical unit required')
    child=store.extraction_job(session_id,source_job)
    if child['file_ids']!=[file['id']]:raise ValueError('Extraction source mismatch')
    verify_originals([file]);backend=Path(file['name']).suffix.lower()[1:]
    run=(child['result'] or {}).get('extraction',{})
    if run.get('source_sha256')!=file['sha256'] or run.get('parser_identity')!=parser_identity(backend):raise ValueError('Source/parser identity changed')
    record=store.extraction_page(session_id,source_job,logical_unit)
    data=Path(file['path']).read_bytes();conversion=run.get('conversion')
    if len(data)!=file['size'] or hashlib.sha256(data).hexdigest()!=file['sha256']:raise ValueError('Office bytes changed during source read')
    if backend=='doc':
        if not conversion or conversion.get('original_sha256')!=file['sha256']:raise ValueError('DOC conversion unavailable')
        data=(store.root/'derived'/(source_job+'.docx')).read_bytes()
        if hashlib.sha256(data).hexdigest()!=conversion['derived_sha256']:raise ValueError('DOC derivative changed')
    units,global_limits=read(data,'docx' if backend=='doc' else backend)
    if logical_unit>len(units):raise ValueError('Logical unit outside source')
    item=units[logical_unit-1];locator=dict(item['locator'])
    if conversion:locator.update(scope='DERIVED_DOCX_LOCATION',derived_sha256=conversion['derived_sha256'])
    text='\n'.join(b['text'] for b in record['blocks'])
    exact_text=text==item['text'] and not record.get('text_truncated')
    clipped_image_text=(image_preview and bool(record.get('text_truncated')) and
                        'TEXT_LIMIT' in record.get('limitations',[]) and len(text)<len(item['text']) and
                        item['text'].startswith(text))
    if (record.get('execution')!='COMPLETED' or record.get('source_sha256')!=file['sha256'] or
            record.get('locator')!=locator or not (exact_text or clipped_image_text)):
        raise ValueError('Office source checkpoint cannot establish exact location')
    if image_preview:
        return dict(source_job=source_job,logical_unit=logical_unit,locator=locator,
                    source_confirmable=False,scope='ORIGINAL_IMAGE_ASSET_UNVERIFIED')
    first=text.find(quote)
    if first<0:raise ValueError('Exact quote not found at Office location')
    unique=first==text.rfind(quote)
    limits=list(dict.fromkeys(global_limits+item['limitations']+record.get('limitations',[])))
    confirmable=unique and not item['limitations'] and record['status']!='BLOCK' and backend!='doc'
    return dict(source_job=source_job,logical_unit=logical_unit,locator=locator,text_sha256=hashlib.sha256(text.encode()).hexdigest(),
                quote_start=first,quote_end=first+len(quote),source_confirmable=confirmable,
                location_status='UNIQUE' if unique else 'AMBIGUOUS',limitations=limits,
                scope='DERIVED_UNVERIFIED' if backend=='doc' else 'ORIGINAL_LOGICAL_LOCATION')


def validate_candidate(store,session_id,candidate,*,require_confirmable=True):
    file=store.get_file(candidate['file_id']);verify_originals([file])
    if file['session_id']!=session_id or file['sha256']!=candidate['source_sha256']:raise ValueError('Candidate source changed')
    if candidate.get('source_binding'):
        binding=candidate['source_binding']
        current=office_location(store,session_id,file,binding['source_job'],binding['logical_unit'],candidate['quote'])
        if digest(current)!=digest(binding):raise ValueError('Office location/review basis changed')
        if require_confirmable and not current['source_confirmable']:raise ValueError('Office location has unresolved source limitations')
    return file

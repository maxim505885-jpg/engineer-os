"""Durable page extraction; observed parser output is never accepted evidence."""
from dataclasses import asdict
import importlib.util
import os
from pathlib import Path

from .core_plan import verify_originals

MAX_PAGES=5000
MAX_PAGE_TEXT=20000
MAX_BLOCKS=1000
MAX_TOTAL_TEXT=2000000


def parse_failure_message(error):
    from engineering.document_intelligence.contracts import DocumentParseError
    # Exact internal messages only: arbitrary parser exceptions may contain
    # source text, paths or credentials and must never enter the journal.
    table_errors={
        'table cell is missing, merged or ambiguous',
        'table grid has missing cells',
        'table caption lacks verified table rows',
        'table column header metadata is missing or ambiguous',
        'table column headers are duplicated',
    }
    if isinstance(error,DocumentParseError) and str(error) in table_errors:
        return 'TABLE_STRUCTURE_UNVERIFIED: структура таблицы неоднозначна; требуется сверка с исходной страницей.'
    from .ocr import OCRError
    if isinstance(error,OCRError):return str(error).split(':')[0]+': локальный OCR не выполнен; требуется проверка.'
    return 'PARSE_FAILED: извлечение страницы недоступно; проверьте parser/OCR/таблицы.'


class ExtractionFailure(RuntimeError):
    """Only fixed, non-sensitive messages are raised by this module."""


def docling_parser():
    from engineering.document_intelligence.docling_adapter import DoclingDocumentParser, document_intelligence_enabled
    if not document_intelligence_enabled():raise ExtractionFailure('Docling: Document Intelligence выключен; извлечение не выполнено.')
    if importlib.util.find_spec('docling') is None:raise ExtractionFailure('Docling не установлен; OCR не выполнен.')
    artifacts=os.environ.get('ENGINEER_OS_DOCLING_ARTIFACTS_PATH','')
    if not artifacts or not Path(artifacts).is_dir():raise ExtractionFailure('Docling: укажите локальный каталог моделей; OCR не выполнен.')
    try:
        configured=DoclingDocumentParser(artifacts_path=artifacts)
        converter=configured._converter()
    except Exception:raise ExtractionFailure('Docling: локальные модели/OCR недоступны; извлечение не выполнено.') from None
    return DoclingDocumentParser(lambda:converter,artifacts_path=artifacts)


def native_page(pdf,page):
    blocks=[]
    for index,block in enumerate(pdf[page-1].get_text('blocks'),1):
        if block[6]!=0 or not block[4].strip():continue
        bbox=dict(zip(('left','top','right','bottom'),block[:4]))
        blocks.append(dict(block_id=f'native:page:{page}:block:{index}',kind='text',text=block[4],
                           provenance=[dict(page_no=page,bbox=bbox)]))
    return blocks


def visual_components(page):
    images=page.get_image_info();vectors=page.get_drawings()
    reasons=[]
    if images:reasons.append('IMAGE_CONTENT_UNVERIFIED')
    if vectors:reasons.append('VECTOR_CONTENT_UNVERIFIED')
    return dict(images=len(images),vector_paths=len(vectors),tables='NOT_PARSED',
                image_regions=[dict(zip(('left','top','right','bottom'),i['bbox'])) for i in images[:100]]),reasons


def retain_blocks(blocks,page,budget):
    retained=[];used=0;clipped=False
    for block in blocks:
        if len(retained)>=MAX_BLOCKS:clipped=True;break
        if not isinstance(block,dict) or not isinstance(block.get('text'),str):raise ValueError('Invalid block')
        refs=block.get('provenance')
        if not isinstance(refs,list) or not refs or any(r.get('page_no')!=page for r in refs):raise ValueError('Wrong source page')
        text=block['text']
        available=min(MAX_PAGE_TEXT,budget)-used
        if available<=0:clipped=True;break
        kept=text[:available];clipped=clipped or len(kept)<len(text)
        retained.append(dict(block,text=kept));used+=len(kept)
    return retained,used,clipped


def execute(store,job,stop_event,*,progress=None):
    if Path(store.get_file(job['file_ids'][0])['name']).suffix.lower() in {'.docx','.xlsx','.doc'}:
        from .office import execute as office_execute
        return office_execute(store,job,stop_event,progress=progress)
    import fitz
    file=store.get_file(job['file_ids'][0])
    if file['session_id']!=job['session_id']:raise ValueError('Source isolation failure')
    verify_originals([file])
    backend={'EXTRACT_DOCLING':'docling','EXTRACT_OCR':'ocr'}.get(job['mode'],'native')
    prior=(job['result'] or {}).get('extraction',{})
    from .analysis_identity import parser_identity
    config=parser_identity(backend)
    if prior and (prior.get('source_sha256')!=file['sha256'] or prior.get('parser_identity')!=config):
        raise ExtractionFailure('Идентичность parser/источника изменилась; создайте новое задание.')
    image=Path(file['name']).suffix.lower() in {'.png','.jpg','.jpeg'}
    if image:
        from .files import validate_image
        try:validate_image(Path(file['path']).read_bytes())
        except Exception:raise ExtractionFailure('IMAGE_UNAVAILABLE_OR_PIXEL_LIMIT: оригинал сохранён; OCR недоступен.') from None
        with fitz.open(file['path']) as source:pdf=fitz.open('pdf',source.convert_to_pdf())
    else:pdf=fitz.open(file['path'])
    with pdf:
        if pdf.needs_pass or not 0<len(pdf)<=MAX_PAGES:raise ExtractionFailure('PDF защищён или превышает лимит 5000 страниц.')
        run=dict(file_id=file['id'],name=file['name'],source_sha256=file['sha256'],backend=backend,parser_identity=config,
                 total_pages=len(pdf),processed_pages=0,failed_pages=0,blocked_pages=0,
                 stored_chars=0,current_page=None,cycle_complete=False,budget_exhausted=False,
                 scope='UNVERIFIED_EXTRACTION',completeness='NOT_CHECKED',ocr=prior.get('ocr','NOT_RUN'),acceptance_granted=False)
        result=dict(text='',extraction=run)
        def checkpoint():
            run.update(store.extraction_totals(job['id']))
            result['text']=f"Извлечение {file['name']} · {backend}: обработано {run['processed_pages']}/{run['total_pages']} страниц; BLOCK {run['blocked_pages']}, ошибки {run['failed_pages']}. Полнота не проверена; FINAL AUDIT NOT_RUN."
            store.checkpoint(job['id'],result)
            if progress:progress(run)
        checkpoint()
        parser=docling_parser() if backend=='docling' else None
        if backend=='ocr':
            from .ocr import TesseractOCR
            parser=TesseractOCR()
        for page in range(1,len(pdf)+1):
            if stop_event.is_set():break
            if store.extraction_completed(job['id'],page):continue
            if run['stored_chars']>=MAX_TOTAL_TEXT:
                run['budget_exhausted']=True;break
            run['current_page']=page;checkpoint();verify_originals([file])
            if backend=='ocr' and parser_identity(backend)!=config:raise ExtractionFailure('Идентичность OCR изменилась; создайте новое задание.')
            record=dict(page=page,execution='COMPLETED',status='UNCERTAINTY',blocks=[],stored_chars=0,
                        text_truncated=False,limitations=[],source_sha256=file['sha256'],
                        scope='UNVERIFIED_EXTRACTION',ocr='NOT_RUN',acceptance_granted=False)
            try:
                record['visual_components'],visual_limits=visual_components(pdf[page-1])
                record['limitations'].extend(visual_limits)
                if visual_limits:record['status']='BLOCK'
                if parser is None:blocks=native_page(pdf,page)
                elif backend=='ocr':
                    blocks=parser.page_blocks(pdf[page-1],page)
                    record['ocr_dossier']=parser.last_page_dossier
                    record['ocr']=run['ocr']='EXECUTED_UNVERIFIED'
                    record['limitations'].append('OCR_TEXT_UNVERIFIED')
                    if parser.layout=='regions':record['limitations'].append('OCR_REGION_CANDIDATES_UNMERGED')
                    if any(b['ocr_confidence']<50 for b in blocks):
                        record['limitations'].append('OCR_LOW_CONFIDENCE');record['status']='BLOCK'
                else:
                    run['ocr']='REQUESTED_NOT_VERIFIED'
                    record['ocr']='REQUESTED_NOT_VERIFIED'
                    document=parser.parse(file['path'],page_range=(page,page))
                    if document.source_sha256!=file['sha256']:raise ValueError('Wrong normalized source')
                    blocks=[asdict(b) for b in document.blocks]
                    for b in blocks:b['provenance']=list(b['provenance'])
                kept,used,clipped=retain_blocks(blocks,page,MAX_TOTAL_TEXT-run['stored_chars'])
                record.update(blocks=kept,stored_chars=used,text_truncated=clipped)
                if not kept or clipped:
                    record['status']='BLOCK'
                    record['limitations'].append('TEXT_LIMIT' if clipped else 'NO_NATIVE_TEXT' if backend=='native' else 'NO_CONTENT')
            except Exception as exc:
                record.update(execution='FAILED',status='BLOCK',blocks=[],stored_chars=0,
                              limitations=[parse_failure_message(exc)])
                if backend=='ocr':record['ocr_dossier']=parser.last_page_dossier
            verify_originals([file])
            if backend=='ocr' and parser_identity(backend)!=config:raise ExtractionFailure('Идентичность OCR изменилась; результат страницы не сохранён.')
            store.save_extraction_page(job['id'],record);checkpoint()
        run['current_page']=None
        run['cycle_complete']=run['processed_pages']==run['total_pages']
        if run['stored_chars']>=MAX_TOTAL_TEXT and not run['cycle_complete']:run['budget_exhausted']=True
        checkpoint()
        if run['budget_exhausted']:raise ExtractionFailure('Лимит сохранённого текста достигнут; часть страниц не обработана.')
        return result

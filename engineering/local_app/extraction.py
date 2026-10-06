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
    text=pdf[page-1].get_text()
    return [dict(block_id=f'native:page:{page}',kind='text',text=text,
                 provenance=[dict(page_no=page,bbox=None)])] if text.strip() else []


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


def execute(store,job,stop_event):
    import fitz
    file=store.get_file(job['file_ids'][0])
    if file['session_id']!=job['session_id']:raise ValueError('Source isolation failure')
    verify_originals([file])
    backend='docling' if job['mode']=='EXTRACT_DOCLING' else 'native'
    prior=(job['result'] or {}).get('extraction',{})
    with fitz.open(file['path']) as pdf:
        if pdf.needs_pass or not 0<len(pdf)<=MAX_PAGES:raise ExtractionFailure('PDF защищён или превышает лимит 5000 страниц.')
        run=dict(file_id=file['id'],name=file['name'],source_sha256=file['sha256'],backend=backend,
                 total_pages=len(pdf),processed_pages=0,failed_pages=0,blocked_pages=0,
                 stored_chars=0,current_page=None,cycle_complete=False,budget_exhausted=False,
                 scope='UNVERIFIED_EXTRACTION',completeness='NOT_CHECKED',ocr=prior.get('ocr','NOT_RUN'),acceptance_granted=False)
        result=dict(text='',extraction=run)
        def checkpoint():
            run.update(store.extraction_totals(job['id']))
            result['text']=f"Извлечение {file['name']} · {backend}: обработано {run['processed_pages']}/{run['total_pages']} страниц; BLOCK {run['blocked_pages']}, ошибки {run['failed_pages']}. Полнота не проверена; FINAL AUDIT NOT_RUN."
            store.checkpoint(job['id'],result)
        checkpoint()
        parser=docling_parser() if backend=='docling' else None
        for page in range(1,len(pdf)+1):
            if stop_event.is_set():break
            if store.extraction_completed(job['id'],page):continue
            if run['stored_chars']>=MAX_TOTAL_TEXT:
                run['budget_exhausted']=True;break
            run['current_page']=page;checkpoint();verify_originals([file])
            record=dict(page=page,execution='COMPLETED',status='UNCERTAINTY',blocks=[],stored_chars=0,
                        text_truncated=False,limitations=[],source_sha256=file['sha256'],
                        scope='UNVERIFIED_EXTRACTION',ocr='NOT_RUN',acceptance_granted=False)
            try:
                if parser is None:blocks=native_page(pdf,page)
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
                    record['limitations']=['TEXT_LIMIT' if clipped else 'NO_NATIVE_TEXT' if backend=='native' else 'NO_CONTENT']
            except Exception:
                record.update(execution='FAILED',status='BLOCK',blocks=[],stored_chars=0,
                              limitations=['PARSE_FAILED: извлечение страницы недоступно; проверьте parser/OCR/таблицы.'])
            verify_originals([file])
            store.save_extraction_page(job['id'],record);checkpoint()
        run['current_page']=None
        run['cycle_complete']=run['processed_pages']==run['total_pages']
        if run['stored_chars']>=MAX_TOTAL_TEXT and not run['cycle_complete']:run['budget_exhausted']=True
        checkpoint()
        if run['budget_exhausted']:raise ExtractionFailure('Лимит сохранённого текста достигнут; часть страниц не обработана.')
        return result

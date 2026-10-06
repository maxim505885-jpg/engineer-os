"""Immutable originals with bounded, explicitly unverified text candidates."""
import hashlib
from pathlib import Path
import time
import uuid
from .store import identifier
from .coverage import unknown_coverage

MAX_FILE_BYTES=100*1024*1024
MAX_TEXT=100000


def extract_preview(name,data):
    suffix=Path(name).suffix.lower()
    c=unknown_coverage('EXTRACTION_UNAVAILABLE')
    if suffix in {'.txt','.md'}:
        try:text=data.decode('utf-8-sig')
        except UnicodeDecodeError:return '', 'UNAVAILABLE','Текст не в UTF-8; оригинал сохранён.',False,c
        truncated=len(text)>MAX_TEXT
        c.update(status='RECORDED',method='UTF8',source_chars=len(text),stored_chars=min(len(text),MAX_TEXT),stop_reasons=['CHAR_LIMIT'] if truncated else [])
        return text[:MAX_TEXT],'UNVERIFIED','Текст источника не проверен; не является доказательством.',truncated,c
    try:
        import fitz
        chunks=[];records=[];used=0;has_text=False;reasons=[]
        with fitz.open(stream=data,filetype='pdf') as pdf:
            if pdf.needs_pass:raise ValueError('Encrypted PDF')
            pages=len(pdf)
            for i in range(min(pages,20)):
                if used>=MAX_TEXT:
                    reasons.append('CHAR_LIMIT');break
                native=pdf[i].get_text()
                marker=f'\n[Source page {i+1}]\n'
                piece=(marker+native)[:MAX_TEXT-used]
                stored=max(0,len(piece)-len(marker))
                has_text=has_text or bool(native[:stored].strip())
                partial=stored<len(native)
                records.append(dict(page=i+1,text_chars=len(native),stored_chars=stored,
                                    status='NO_NATIVE_TEXT' if not native.strip() else 'PARTIAL_TEXT' if partial else 'TEXT'))
                chunks.append(piece);used+=len(piece)
                if partial:
                    reasons.append('CHAR_LIMIT');break
            if len(records)==20 and pages>20:reasons.append('PAGE_LIMIT')
            text=''.join(chunks)
        c.update(status='RECORDED',method='NATIVE_PDF',total_pages=pages,
                 attempted_pages=len(records),pages_with_text=sum(r['text_chars']>0 and r['status']!='NO_NATIVE_TEXT' for r in records),
                 pages_without_text=[r['page'] for r in records if r['status']=='NO_NATIVE_TEXT'],
                 unattempted_pages=pages-len(records),page_records=records,
                 stored_chars=len(text),stop_reasons=reasons,page_limit=20,char_limit=MAX_TEXT)
        truncated=bool(reasons)
        note=f"Native-текст: попытка извлечения {len(records)}/{pages} страниц. Native-текст не найден: {len(c['pages_without_text'])}. Таблицы, рисунки и полнота не проверены; OCR не выполнен."
        if not has_text:
            c['stored_chars']=0
            for record in records:record['stored_chars']=0
            return '', 'UNAVAILABLE','В сохранённом preview нет текста. Оригинал сохранён; требуется OCR или визуальная проверка.',truncated,c
        return text,'UNVERIFIED',note,truncated,c
    except Exception:
        return '', 'UNAVAILABLE','Извлечение текста PDF недоступно. Оригинал сохранён; требуется отдельная проверка.',False,c


def candidate_text(name,data):
    # Preserve the existing four-value API for callers outside this module.
    return extract_preview(name,data)[:4]


def preserve_file(store,session_id,name,data,*,source_metadata=None):
    identifier(session_id)
    if not isinstance(name,str) or not name.strip() or len(name)>240 or any(ord(c)<32 for c in name):raise ValueError('Invalid filename')
    if Path(name).suffix.lower() not in {'.txt','.md','.pdf'}:raise ValueError('Supported originals: TXT, MD, PDF')
    if not isinstance(data,bytes) or not data or len(data)>MAX_FILE_BYTES:raise ValueError('Original must contain 1 byte–100 MiB')
    store.snapshot(session_id)
    ident=str(uuid.uuid4());folder=store.root/'files';folder.mkdir(exist_ok=True)
    path=folder/(ident+Path(name).suffix.lower())
    text,status,note,truncated,coverage=extract_preview(name,data)
    path.write_bytes(data)
    record=dict(id=ident,session_id=session_id,name=name,path=str(path),sha256=hashlib.sha256(data).hexdigest(),size=len(data),text=text,extraction_status=status,extraction_note=note,text_truncated=int(truncated),created=time.time())
    record['source_metadata']=source_metadata or {}
    record['extraction_coverage']=coverage
    try:return store.add_file(record)
    except Exception:
        path.unlink(missing_ok=True);raise

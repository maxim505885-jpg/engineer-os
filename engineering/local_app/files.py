"""Immutable originals with bounded, explicitly unverified text candidates."""
import hashlib
from pathlib import Path
import time
import uuid
from .store import identifier

MAX_FILE_BYTES=100*1024*1024
MAX_TEXT=100000


def candidate_text(name,data):
    suffix=Path(name).suffix.lower()
    if suffix in {'.txt','.md'}:
        try:text=data.decode('utf-8-sig')
        except UnicodeDecodeError:return '', 'UNAVAILABLE','Текст не в UTF-8; оригинал сохранён.',False
        return text[:MAX_TEXT],'UNVERIFIED','Текст источника не проверен; не является доказательством.',len(text)>MAX_TEXT
    try:
        import fitz
        chunks=[];truncated=False
        with fitz.open(stream=data,filetype='pdf') as pdf:
            if pdf.needs_pass:raise ValueError('Encrypted PDF')
            pages=len(pdf)
            for i in range(min(pages,20)):
                chunks.append(f'\n[Source page {i+1}]\n'+pdf[i].get_text())
                if sum(map(len,chunks))>MAX_TEXT:
                    truncated=True;break
            text=''.join(chunks);truncated=truncated or pages>20
        # Empty page markers must not be mistaken for an extraction.
        content=''.join(line for line in text.splitlines() if not line.startswith('[Source page'))
        if not content.strip():return '', 'UNAVAILABLE','Текстовый слой не найден. Оригинал сохранён; требуется OCR или визуальная проверка.',truncated
        return text[:MAX_TEXT],'UNVERIFIED',f'Кандидаты текста из первых 20 страниц (всего {pages}). Таблицы, рисунки и полнота не проверены.',truncated
    except Exception:
        # Parser exceptions vary by optional PyMuPDF version. Never lose original.
        return '', 'UNAVAILABLE','Извлечение текста PDF недоступно. Оригинал сохранён; требуется отдельная проверка.',False


def preserve_file(store,session_id,name,data,*,source_metadata=None):
    identifier(session_id)
    if not isinstance(name,str) or not name.strip() or len(name)>240 or any(ord(c)<32 for c in name):raise ValueError('Invalid filename')
    if Path(name).suffix.lower() not in {'.txt','.md','.pdf'}:raise ValueError('Supported originals: TXT, MD, PDF')
    if not isinstance(data,bytes) or not data or len(data)>MAX_FILE_BYTES:raise ValueError('Original must contain 1 byte–100 MiB')
    store.snapshot(session_id)
    ident=str(uuid.uuid4());folder=store.root/'files';folder.mkdir(exist_ok=True)
    path=folder/(ident+Path(name).suffix.lower())
    text,status,note,truncated=candidate_text(name,data)
    path.write_bytes(data)
    record=dict(id=ident,session_id=session_id,name=name,path=str(path),sha256=hashlib.sha256(data).hexdigest(),size=len(data),text=text,extraction_status=status,extraction_note=note,text_truncated=int(truncated),created=time.time())
    record['source_metadata']=source_metadata or {}
    try:return store.add_file(record)
    except Exception:
        path.unlink(missing_ok=True);raise

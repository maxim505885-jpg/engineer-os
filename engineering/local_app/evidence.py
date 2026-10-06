"""User-authored source candidates. Text matches do not establish engineering truth."""
import hashlib
from pathlib import Path
import time
import uuid
from .provenance import locate,unavailable


def register(store,session_id,*,file_id,quote,statement,page=None,data_class='U'):
    for name,value,limit in [('quote',quote,4000),('statement',statement,4000)]:
        if not isinstance(value,str) or not value.strip() or len(value)>limit:raise ValueError(name+' must contain 1–4000 characters')
    if not isinstance(data_class,str) or data_class not in {'P','F','M','T','C','A','I','U'}:raise ValueError('Invalid data class')
    if page is not None and (type(page) is not int or not 1<=page<=100000):raise ValueError('Page must be a positive integer')
    f=store.get_file(file_id)
    if f['session_id']!=session_id:raise ValueError('Original belongs to another conversation')
    if Path(f['name']).suffix.lower() in {'.docx','.xlsx','.doc'}:
        raise ValueError('Office: используйте привязку абзаца/таблицы/ячейки из журнала анализа; реестр этих привязок подключается отдельно.')
    with Path(f['path']).open('rb') as stream:data=stream.read(100*1024*1024+1)
    if len(data)!=f['size'] or hashlib.sha256(data).hexdigest()!=f['sha256']:raise ValueError('Original identity check failed')
    provenance,document_validation=unavailable()
    suffix=Path(f['name']).suffix.lower();text=None;note='Цитата не проверена по оригиналу; требуется ручная проверка.'
    if suffix in {'.txt','.md'}:
        provenance,document_validation=unavailable('NOT_APPLICABLE')
        if page is not None:raise ValueError('TXT/MD do not have PDF page numbers')
        try:text=data.decode('utf-8-sig')
        except UnicodeDecodeError:pass
    else:
        if page is None:raise ValueError('PDF source page required')
        try:
            import fitz
            with fitz.open(stream=data,filetype='pdf') as pdf:
                if not pdf.needs_pass:
                    if page>len(pdf):raise IndexError('Page outside PDF')
                    pdf_page=pdf[page-1];text=pdf_page.get_text() or None
                    if text and quote in text:
                        try:provenance,document_validation=locate(pdf_page,quote,text,f['sha256'],file_id,page)
                        except Exception:provenance,document_validation=unavailable()
        except IndexError:raise ValueError('Page outside PDF') from None
        except Exception:pass
    if text is not None:
        if quote not in text:raise ValueError('Exact quote not found in original text at this location')
        match='MATCH';note='Точное совпадение native текста; содержание, координаты, полнота и инженерная достоверность не подтверждены.'
    else:match='NOT_CHECKED'
    record=dict(id=str(uuid.uuid4()),session_id=session_id,file_id=file_id,name=f['name'],source_sha256=f['sha256'],page=page,quote=quote,statement=statement,data_class=data_class,data_class_verified=False,source_match=match,verification_note=note,status='UNVERIFIED',acceptance_granted=False,final_audit='NOT_RUN',created=time.time(),provenance=provenance,document_validation=document_validation)
    return store.add_evidence(record)

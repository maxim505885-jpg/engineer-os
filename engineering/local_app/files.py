"""Immutable originals with bounded, explicitly unverified text candidates."""
import hashlib
import os
from pathlib import Path
import time
import uuid
from .store import identifier
from .coverage import unknown_coverage

MAX_FILE_BYTES=100*1024*1024
MAX_OFFICE_FILE_BYTES=256*1024*1024
MAX_TEXT=100000
SUPPORTED_SUFFIXES={'.txt','.md','.pdf','.docx','.xlsx','.doc','.lir','.png','.jpg','.jpeg','.json','.csv','.dxf','.dwg','.ald','.cop','.log','.zip'}


def file_limit(name):
    return MAX_OFFICE_FILE_BYTES if Path(name).suffix.lower() in {'.docx','.xlsx'} else MAX_FILE_BYTES


def validate_image(data):
    import io
    from PIL import Image
    with Image.open(io.BytesIO(data)) as image:
        width,height=image.size
        if width*height>16000000:raise ValueError('Image pixel limit')
        image.verify()
    return width,height


def _atomic_write_original(path,data):
    temp=path.with_name(path.name+'.partial-'+uuid.uuid4().hex)
    try:
        with temp.open('xb') as stream:
            stream.write(data);stream.flush();os.fsync(stream.fileno())
        os.replace(temp,path)
    finally:
        temp.unlink(missing_ok=True)


def extract_preview(name,data):
    suffix=Path(name).suffix.lower()
    c=unknown_coverage('EXTRACTION_UNAVAILABLE')
    from engineering.calculation.upload_analysis import analyze_upload, report_note
    calculation = analyze_upload(name, data) if suffix in {'.txt','.log','.ald','.cop','.zip'} else None
    if calculation:
        c.update(status='RECORDED',method='LIRA_SOURCE_OBSERVATIONS',calculation_report=calculation,stop_reasons=list(calculation['reasons']))
        if suffix=='.zip':
            return '', 'UNAVAILABLE',report_note(calculation),False,c
        if calculation['kind']=='UNREADABLE_VENDOR_EXPORT' or 'XML_ENCODING_UNSUPPORTED' in calculation['reasons']:
            return '', 'UNAVAILABLE',report_note(calculation),False,c
        text=data.decode('utf-8-sig')
        truncated=len(text)>MAX_TEXT
        c.update(source_chars=len(text),stored_chars=min(len(text),MAX_TEXT))
        if truncated:c['stop_reasons'].append('CHAR_LIMIT')
        return text[:MAX_TEXT],'UNVERIFIED',report_note(calculation),truncated,c
    if suffix in {'.dxf','.dwg'}:
        c.update(method='CAD_ORIGINAL_ONLY',stop_reasons=['CAD_INVENTORY_REQUIRED','GEOMETRY_NOT_ENGINEERING_VERIFIED'])
        return '', 'UNAVAILABLE','Оригинал CAD сохранён. Выполните инвентаризацию; геометрия и инженерная корректность не проверены. DWG требует отдельного конвертера.',False,c
    if suffix=='.lir':
        from engineering.calculation.native_source import inspect_lir
        metadata=inspect_lir(data)
        c.update(method='LIR_ORIGINAL_ONLY',stop_reasons=metadata['reasons'],model_metadata=metadata)
        header=('Заявленный формат '+metadata['declared_format']+' ver.'+metadata['declared_version']+'. ' if metadata['declared_version'] else 'Заголовок формата не распознан. ')
        return '', 'UNAVAILABLE','Модель LIR сохранена. '+header+'Декодер не подключён; геометрия, нагрузки и результаты не прочитаны. Нужен документированный экспорт; расчёт не выполнен.',False,c
    if suffix in {'.png','.jpg','.jpeg'}:
        try:
            width,height=validate_image(data)
            c.update(method='IMAGE_ORIGINAL',total_pages=1,image_width=width,image_height=height,stop_reasons=['OCR_REQUIRED','IMAGE_CONTENT_UNVERIFIED'])
            return '', 'UNAVAILABLE','Изображение сохранено; текст не распознан. Откройте оригинал или запустите локальный OCR. Содержание требует визуальной сверки.',False,c
        except Exception:
            c.update(method='IMAGE_ORIGINAL',stop_reasons=['IMAGE_UNAVAILABLE_OR_PIXEL_LIMIT'])
            return '', 'UNAVAILABLE','Изображение повреждено или превышает лимит 16 млн пикселей. Оригинал сохранён; просмотр/OCR недоступен.',False,c
    if suffix in {'.docx','.xlsx','.doc'}:
        c.update(method=suffix[1:].upper(),stop_reasons=['BACKGROUND_EXTRACTION_REQUIRED'])
        return '', 'UNAVAILABLE','Оригинал Office сохранён. Текст и таблицы будут обработаны при отправке задания; полнота не проверена.',False,c
    if suffix in {'.txt','.md','.json','.csv'}:
        try:text=data.decode('utf-8-sig')
        except UnicodeDecodeError:return '', 'UNAVAILABLE','Текст не в UTF-8; оригинал сохранён.',False,c
        truncated=len(text)>MAX_TEXT
        c.update(status='RECORDED',method='UTF8',source_chars=len(text),stored_chars=min(len(text),MAX_TEXT),stop_reasons=['CHAR_LIMIT'] if truncated else [])
        if suffix in {'.json','.csv'}:
            c['method']='UNVERIFIED_EXPORT_TEXT'
            c['stop_reasons'].append('CALCULATION_SEMANTICS_NOT_CHECKED')
            if suffix=='.json' and not truncated:
                import json
                try:json.loads(text)
                except (ValueError,RecursionError):c['stop_reasons'].append('INVALID_JSON')
        return text[:MAX_TEXT],'UNVERIFIED','Текст источника не проверен; не является доказательством.',truncated,c
    try:
        import fitz
        chunks=[];records=[];used=0;has_text=False;reasons=[]
        with fitz.open(stream=data,filetype='pdf') as pdf:
            if pdf.needs_pass:
                c.update(method='NATIVE_PDF',stop_reasons=['ENCRYPTED_PDF'])
                return '', 'UNAVAILABLE','PDF защищён паролем. Оригинал сохранён; предоставьте разрешённую незашифрованную копию для обработки.',False,c
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
    except Exception as error:
        c['stop_reasons']=['EXTRACTION_UNAVAILABLE']
        if 'fitz' in locals() and isinstance(error,(fitz.FileDataError,fitz.EmptyFileError)):
            c['stop_reasons'].append('CORRUPT_PDF')
        return '', 'UNAVAILABLE','Извлечение текста PDF недоступно. Оригинал сохранён; требуется отдельная проверка.',False,c


def candidate_text(name,data):
    # Preserve the existing four-value API for callers outside this module.
    return extract_preview(name,data)[:4]


def preserve_file(store,session_id,name,data,*,source_metadata=None):
    identifier(session_id)
    if not isinstance(name,str) or not name.strip() or len(name)>240 or any(ord(c)<32 for c in name):raise ValueError('Invalid filename')
    if Path(name).suffix.lower() not in SUPPORTED_SUFFIXES:raise ValueError('Supported originals: TXT, MD, PDF, DOCX, XLSX, DOC, LIR, PNG, JPG, JPEG, JSON, CSV, DXF, DWG, ALD, COP, LOG, ZIP')
    if not isinstance(data,bytes) or not data or len(data)>file_limit(name):raise ValueError('Original exceeds file limit: '+str(file_limit(name)//1024//1024)+' MiB')
    store.snapshot(session_id)
    ident=str(uuid.uuid4());folder=store.root/'files';folder.mkdir(exist_ok=True)
    path=folder/(ident+Path(name).suffix.lower())
    text,status,note,truncated,coverage=extract_preview(name,data)
    _atomic_write_original(path,data)
    record=dict(id=ident,session_id=session_id,name=name,path=str(path),sha256=hashlib.sha256(data).hexdigest(),size=len(data),text=text,extraction_status=status,extraction_note=note,text_truncated=int(truncated),created=time.time())
    record['source_metadata']=source_metadata or {}
    record['extraction_coverage']=coverage
    try:return store.add_file(record)
    except Exception:
        path.unlink(missing_ok=True);raise

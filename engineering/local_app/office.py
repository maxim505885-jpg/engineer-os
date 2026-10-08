"""Bounded OOXML text candidates, never layout/evidence or formula evaluation."""
import io
import json
import posixpath
import re
import zipfile
from xml.etree import ElementTree as ET

W='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
S='{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
R='{http://schemas.openxmlformats.org/officeDocument/2006/relationships}'
MAX_XML=8*1024*1024
MAX_EXPANDED=32*1024*1024
MAX_ENTRIES=10000
MAX_UNITS=50000


class OfficeError(ValueError):pass


def convert_doc(data):
    from .doc_conversion import convert_doc as convert
    return convert(data)


class Package:
    def __init__(self,data):
        self.zip=zipfile.ZipFile(io.BytesIO(data))
        entries=self.zip.infolist();names=[i.filename for i in entries]
        if (len(entries)>MAX_ENTRIES or len(names)!=len(set(names)) or
                sum(i.file_size for i in entries)>MAX_EXPANDED or
                any(i.flag_bits&1 or i.filename.startswith('/') or '..' in i.filename.split('/') for i in entries)):
            self.zip.close();raise OfficeError('Invalid/bounded package')
        self.names=set(names)

    def close(self):self.zip.close()

    def xml(self,name):
        info=self.zip.getinfo(name)
        if info.file_size>MAX_XML:raise OfficeError('XML size limit')
        data=self.zip.read(name)
        if b'<!DOCTYPE' in data.upper() or b'<!ENTITY' in data.upper():raise OfficeError('XML entities unavailable')
        # UTF16 could hide declarations from the byte scan; reject it rather
        # than accepting a second encoding-dependent attack surface.
        if b'\x00' in data:raise OfficeError('Only UTF8 Office XML is supported')
        return ET.fromstring(data)


def unit(text,locator,limitations=()):
    return dict(text=text,locator=locator,limitations=list(dict.fromkeys(limitations)))


def word_text(element):
    pieces=[]
    for e in element.iter():
        if e.tag==W+'t':pieces.append(e.text or '')
        elif e.tag==W+'tab':pieces.append('\t')
        elif e.tag in {W+'br',W+'cr'}:pieces.append('\n')
        elif e.tag==W+'noBreakHyphen':pieces.append('\u2011')
        elif e.tag==W+'softHyphen':pieces.append('\u00ad')
        elif e.tag==W+'sym':
            # A font-specific code is not a Unicode character. Preserve the
            # source token and block interpretation rather than guessing it.
            pieces.append('[WORD_SYMBOL font='+e.get(W+'font','')+' char='+e.get(W+'char','')+']')
    return ''.join(pieces)


def word_limits(element):
    limits=[];tags={e.tag.rsplit('}',1)[-1] for e in element.iter()}
    if 'sym' in tags:limits.append('SYMBOL_NOT_DECODED')
    for group,reason in [(('drawing','pict'),'DRAWING_NOT_READ'),(('oMath','oMathPara'),'EQUATION_NOT_READ'),
                         (('ins','del','moveFrom','moveTo'),'TRACKED_CHANGES_UNVERIFIED'),(('instrText','fldSimple'),'FIELD_NOT_EVALUATED')]:
        if tags.intersection(group):limits.append(reason)
    return limits


def read_docx(p):
    root=p.xml('word/document.xml');body=root.find(W+'body')
    if body is None:raise OfficeError('Missing Word body')
    out=[];paragraph=0;table=0;limits=['PHYSICAL_PAGES_UNKNOWN','LAYOUT_NOT_VERIFIED']
    if any('/header' in n or '/footer' in n or n.endswith(('footnotes.xml','endnotes.xml')) for n in p.names):limits.append('HEADERS_FOOTNOTES_NOT_READ')
    if any('/embeddings/' in n or 'vbaProject' in n for n in p.names):limits.append('EMBEDDED_CONTENT_NOT_READ')
    for child in body:
        if child.tag==W+'p':
            paragraph+=1;text=word_text(child);warnings=word_limits(child)
            if text or warnings:out.append(unit(text,dict(kind='paragraph',part='word/document.xml',paragraph=paragraph),warnings))
        elif child.tag==W+'tbl':
            table+=1
            for row_index,row in enumerate(child.findall(W+'tr'),1):
                for column,cell in enumerate(row.findall(W+'tc'),1):
                    warnings=word_limits(cell)
                    if any(e.tag in {W+'gridSpan',W+'vMerge',W+'hMerge'} for e in cell.iter()):warnings.append('MERGED_CELL_UNVERIFIED')
                    if cell.find('.//'+W+'tbl') is not None:warnings.append('NESTED_TABLE_UNVERIFIED')
                    text='\n'.join(word_text(e) for e in cell.findall(W+'p'))
                    out.append(unit(text,dict(kind='table_cell',part='word/document.xml',table=table,row=row_index,column=column),warnings))
        elif child.tag!=W+'sectPr':
            out.append(unit(word_text(child),dict(kind='unsupported_body',part='word/document.xml',body_index=list(body).index(child)+1),['BODY_STRUCTURE_UNVERIFIED']))
    return out,limits


def text_runs(element):
    # Phonetic rPh/t annotations are pronunciation hints, not cell content.
    return ''.join(child.text or '' if child.tag==S+'t' else ''.join(e.text or '' for e in child.findall(S+'t'))
                   for child in element if child.tag in {S+'t',S+'r'})


def read_xlsx(p):
    workbook=p.xml('xl/workbook.xml');relations=p.xml('xl/_rels/workbook.xml.rels')
    rels={};limits=['FORMULAS_NOT_EVALUATED','RAW_VALUES_STYLES_NOT_APPLIED','DRAWINGS_CHARTS_NOT_READ']
    for rel in relations:
        ident=rel.get('Id')
        if not ident or ident in rels:raise OfficeError('Ambiguous worksheet relationship')
        rels[ident]=rel
    shared=[]
    if 'xl/sharedStrings.xml' in p.names:shared=[text_runs(e) for e in p.xml('xl/sharedStrings.xml')]
    if any('externalLinks/' in n for n in p.names):limits.append('EXTERNAL_LINKS_NOT_RESOLVED')
    if any('vbaProject' in n for n in p.names):limits.append('MACROS_NOT_EXECUTED')
    out=[];sheet_names=set()
    sheets=workbook.find(S+'sheets')
    if sheets is None:raise OfficeError('Missing sheets')
    for sheet in sheets:
        name=sheet.get('name');rel=rels.get(sheet.get(R+'id'))
        if not name or name in sheet_names or rel is None or rel.get('TargetMode')=='External':raise OfficeError('Invalid sheet identity')
        sheet_names.add(name);target=rel.get('Target','')
        part=posixpath.normpath(target.lstrip('/') if target.startswith('/') else posixpath.join('xl',target))
        if not part.startswith('xl/') or '/..' in part or not rel.get('Type','').endswith('/worksheet'):raise OfficeError('Invalid worksheet target')
        root=p.xml(part);data=root.find(S+'sheetData')
        warnings=['HIDDEN_SHEET'] if sheet.get('state','visible')!='visible' else []
        if root.find(S+'mergeCells') is not None:warnings.append('MERGED_CELLS_UNVERIFIED')
        if root.find(S+'drawing') is not None:warnings.append('DRAWING_NOT_READ')
        if root.find(S+'sheetProtection') is not None:warnings.append('PROTECTED_SHEET_UNVERIFIED')
        seen=set();found=False
        for row in data if data is not None else []:
            for cell in row.findall(S+'c'):
                address=cell.get('r','')
                if not re.fullmatch(r'[A-Z]{1,3}[1-9][0-9]{0,6}',address) or address in seen:raise OfficeError('Invalid/duplicate cell address')
                seen.add(address);found=True;kind=cell.get('t','n');value=cell.find(S+'v');formula=cell.find(S+'f');inline=cell.find(S+'is')
                raw=value.text if value is not None else None;reasons=list(warnings)
                if kind=='s':
                    if raw is None or not raw.isdigit() or int(raw)>=len(shared):raise OfficeError('Invalid shared string')
                    stored=shared[int(raw)]
                elif kind=='inlineStr':stored=text_runs(inline) if inline is not None else ''
                elif kind in {'n','b','e','str','d'}:stored=raw
                else:raise OfficeError('Unsupported cell type')
                field=dict(sheet=name,cell=address,stored_value=stored,value_type=kind,style=cell.get('s'),formula=formula.text if formula is not None else None,cache_present=raw is not None)
                if formula is not None:
                    if raw is None:reasons.append('FORMULA_CACHE_MISSING')
                    if formula.get('t'):reasons.append('SPECIAL_FORMULA_UNVERIFIED');field['formula_metadata']=dict(formula.attrib)
                if kind=='e':reasons.append('CELL_ERROR_VALUE')
                if row.get('hidden')=='1':reasons.append('HIDDEN_ROW')
                out.append(unit(json.dumps(field,ensure_ascii=False),dict(kind='cell',part=part,sheet=name,cell=address),reasons))
        if not found:out.append(unit('',dict(kind='sheet',part=part,sheet=name),warnings+['EMPTY_SHEET']))
    return out,limits


def read(data,backend):
    p=Package(data)
    try:
        units,limits=read_docx(p) if backend=='docx' else read_xlsx(p) if backend=='xlsx' else (_ for _ in ()).throw(OfficeError('Unsupported format'))
        if not units or len(units)>MAX_UNITS:raise OfficeError('Document unit limit/empty document')
        return units,limits
    finally:p.close()


def execute(store,job,stop,*,progress=None):
    from .analysis_identity import parser_identity
    from .core_plan import verify_originals
    from .extraction import ExtractionFailure,MAX_PAGE_TEXT,MAX_TOTAL_TEXT
    from pathlib import Path
    file=store.get_file(job['file_ids'][0]);backend=Path(file['name']).suffix.lower()[1:]
    if file['session_id']!=job['session_id']:raise ValueError('Source isolation failure')
    verify_originals([file]);config=parser_identity(backend)
    prior=(job['result'] or {}).get('extraction',{})
    if prior and (prior.get('source_sha256')!=file['sha256'] or prior.get('parser_identity')!=config):raise ExtractionFailure('Идентичность Office/источника изменилась; создайте новое задание.')
    conversion=None
    try:
        data=Path(file['path']).read_bytes()
        if backend=='doc':
            import hashlib
            folder=store.root/'derived';folder.mkdir(exist_ok=True);target=folder/(job['id']+'.docx')
            saved=prior.get('conversion')
            if saved:
                if not target.is_file():raise OfficeError('Derived checkpoint missing')
                data=target.read_bytes();conversion=saved
            else:data,conversion=convert_doc(data)
            if conversion['original_sha256']!=file['sha256'] or conversion['derived_sha256']!=hashlib.sha256(data).hexdigest():raise OfficeError('Conversion identity mismatch')
            verify_originals([file])
            if not saved:target.write_bytes(data)
        units,limits=read(data,'docx' if backend=='doc' else backend)
        if conversion:
            limits.append('DOC_CONVERSION_LAYOUT_UNVERIFIED')
            for item in units:item['locator'].update(scope='DERIVED_DOCX_LOCATION',derived_sha256=conversion['derived_sha256'])
    except Exception:raise ExtractionFailure('Office: содержимое недоступно или превышает лимиты; оригинал сохранён, анализ не выполнен.') from None
    run=dict(file_id=file['id'],name=file['name'],source_sha256=file['sha256'],backend=backend,parser_identity=config,
             total_pages=len(units),processed_pages=0,failed_pages=0,blocked_pages=0,stored_chars=0,current_page=None,
             total_units=len(units),unit_label='абзацы/ячейки' if backend in {'docx','doc'} else 'ячейки/листы',physical_pages=None,
             limitations=limits,cycle_complete=False,budget_exhausted=False,scope='UNVERIFIED_EXTRACTION',completeness='NOT_CHECKED',ocr='NOT_APPLICABLE',acceptance_granted=False)
    sheets={};tables={}
    for index,item in enumerate(units,1):
        locator=item['locator']
        key=locator.get('sheet')
        if key is not None:sheets.setdefault(key,[]).append(index)
        key=locator.get('table')
        if key is not None:tables.setdefault(str(key),[]).append(index)
    manifest=dict(scope='PARSED_LOGICAL_UNITS',declared_units=len(units),processed_units=0,unprocessed_units=len(units),
                  sheets=[dict(name=k,units=len(v)) for k,v in sheets.items()],
                  tables=[dict(table=k,cells=len(v)) for k,v in tables.items()],
                  physical_pages=None,limitations=limits,acceptance_granted=False)
    run['coverage_manifest']=manifest
    result=dict(text='',extraction=run)
    if conversion:run['conversion']=conversion
    def checkpoint():
        run.update(store.extraction_totals(job['id']));run['processed_units']=run['processed_pages']
        manifest.update(processed_units=run['processed_units'],unprocessed_units=len(units)-run['processed_units'])
        result['text']=f"Извлечение {file['name']} · {run['processed_units']}/{run['total_units']} логических элементов. Физические страницы неизвестны; полнота не проверена."
        store.checkpoint(job['id'],result)
        if progress:progress(run)
    checkpoint()
    for index,item in enumerate(units,1):
        if stop.is_set():break
        if store.extraction_completed(job['id'],index):continue
        if run['stored_chars']>=MAX_TOTAL_TEXT:run['budget_exhausted']=True;break
        original=item['text'];text=original[:min(MAX_PAGE_TEXT,MAX_TOTAL_TEXT-run['stored_chars'])];clipped=len(text)<len(original)
        reasons=list(item['limitations'])+(['TEXT_LIMIT'] if clipped else [])
        blocks=[dict(block_id='office:'+str(index),kind=item['locator']['kind'],text=text,locator=item['locator'],provenance=[])] if text else []
        if not blocks:reasons.append('NO_TEXT')
        verify_originals([file])
        store.save_extraction_page(job['id'],dict(page=index,logical_unit=index,execution='COMPLETED',status='BLOCK' if reasons else 'UNCERTAINTY',
            blocks=blocks,stored_chars=len(text),text_truncated=clipped,limitations=reasons,locator=item['locator'],source_sha256=file['sha256'],
            scope='UNVERIFIED_EXTRACTION',ocr='NOT_APPLICABLE',acceptance_granted=False))
        checkpoint()
    run['cycle_complete']=run['processed_pages']==len(units);checkpoint()
    if run['budget_exhausted']:raise ExtractionFailure('Лимит сохранённого текста достигнут; часть элементов Office не обработана.')
    return result

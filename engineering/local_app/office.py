"""Bounded OOXML text candidates, never layout/evidence or formula evaluation."""
import io
import copy
import hashlib
import json
import posixpath
import re
import zipfile
from xml.etree import ElementTree as ET

W='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
M='{http://schemas.openxmlformats.org/officeDocument/2006/math}'
S='{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
R='{http://schemas.openxmlformats.org/officeDocument/2006/relationships}'
MAX_XML=16*1024*1024
MAX_EXPANDED=32*1024*1024
MAX_PACKAGE_EXPANDED=512*1024*1024
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
                sum(i.file_size for i in entries)>MAX_PACKAGE_EXPANDED or
                sum(i.file_size for i in entries if i.filename.endswith(('.xml','.rels')))>MAX_EXPANDED or
                any(i.flag_bits&1 or i.filename.startswith('/') or '..' in i.filename.split('/') for i in entries)):
            self.zip.close();raise OfficeError('Invalid/bounded package')
        self.names=set(names);self.xml_bytes=0

    def close(self):self.zip.close()

    def xml(self,name):
        info=self.zip.getinfo(name)
        if info.file_size>MAX_XML:raise OfficeError('XML size limit')
        if self.xml_bytes+info.file_size>MAX_EXPANDED:raise OfficeError('XML aggregate read limit')
        self.xml_bytes+=info.file_size
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


def equation_units(element,locator):
    """Preserve source syntax; tokens are not a linearized/rendered equation."""
    out=[];pending=[element]
    while pending:
        current=pending.pop()
        if current.tag!=M+'oMath':
            pending.extend(reversed(list(current)));continue
        fragment=copy.copy(current);fragment.tail=None
        payload=dict(scope='NORMALIZED_OMML_UNINTERPRETED',literal_tokens=[e.text or '' for e in current.iter(M+'t')],
                     normalized_omml=ET.tostring(fragment,encoding='unicode'),evaluated=False,layout_verified=False)
        parent=dict(locator);parent.update(kind='equation',parent_kind=locator['kind'],equation=len(out)+1)
        out.append(unit(json.dumps(payload,ensure_ascii=False),parent,word_limits(current)+['EQUATION_NOT_READ']))
        # Do not separately serialize nested equations, which duplicates syntax.
    return out


def read_docx(p):
    root=p.xml('word/document.xml');body=root.find(W+'body')
    if body is None:raise OfficeError('Missing Word body')
    out=[];paragraph=0;table=0;limits=['PHYSICAL_PAGES_UNKNOWN','LAYOUT_NOT_VERIFIED']
    if any('/header' in n or '/footer' in n or n.endswith(('footnotes.xml','endnotes.xml')) for n in p.names):limits.append('HEADERS_FOOTNOTES_NOT_READ')
    if any('/embeddings/' in n or 'vbaProject' in n for n in p.names):limits.append('EMBEDDED_CONTENT_NOT_READ')
    for child in body:
        if child.tag==W+'p':
            paragraph+=1;text=word_text(child);warnings=word_limits(child)
            locator=dict(kind='paragraph',part='word/document.xml',paragraph=paragraph)
            if text or warnings:out.append(unit(text,locator,warnings))
            out.extend(equation_units(child,locator))
        elif child.tag==W+'tbl':
            table+=1
            for row_index,row in enumerate(child.findall(W+'tr'),1):
                for column,cell in enumerate(row.findall(W+'tc'),1):
                    warnings=word_limits(cell)
                    if any(e.tag in {W+'gridSpan',W+'vMerge',W+'hMerge'} for e in cell.iter()):warnings.append('MERGED_CELL_UNVERIFIED')
                    if cell.find('.//'+W+'tbl') is not None:warnings.append('NESTED_TABLE_UNVERIFIED')
                    text='\n'.join(word_text(e) for e in cell.findall(W+'p'))
                    locator=dict(kind='table_cell',part='word/document.xml',table=table,row=row_index,column=column)
                    properties=cell.find(W+'tcPr');merge={}
                    if properties is not None:
                        for name in ('gridSpan','vMerge','hMerge'):
                            found=properties.find(W+name)
                            if found is not None:merge[name]=dict(found.attrib)
                    if merge:
                        locator['declared_merge']=merge
                        text+='\n'+json.dumps(dict(scope='DECLARED_CELL_STRUCTURE_UNVERIFIED',column_kind='XML_CELL_ORDINAL',declared_merge=merge),ensure_ascii=False)
                    out.append(unit(text,locator,warnings))
                    out.extend(equation_units(cell,locator))
        elif child.tag!=W+'sectPr':
            locator=dict(kind='unsupported_body',part='word/document.xml',body_index=list(body).index(child)+1)
            out.append(unit(word_text(child),locator,['BODY_STRUCTURE_UNVERIFIED']))
            out.extend(equation_units(child,locator))
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
                field=dict(sheet=name,cell=address,stored_value=stored,value_type=kind,style=cell.get('s'),formula=formula.text if formula is not None else None,formula_present=formula is not None,cache_present=raw is not None)
                if formula is not None:
                    if raw is None:reasons.append('FORMULA_CACHE_MISSING')
                    if formula.get('t'):reasons.append('SPECIAL_FORMULA_UNVERIFIED');field['formula_metadata']=dict(formula.attrib)
                if kind=='e':reasons.append('CELL_ERROR_VALUE')
                if row.get('hidden')=='1':reasons.append('HIDDEN_ROW')
                out.append(unit(json.dumps(field,ensure_ascii=False),dict(kind='cell',part=part,sheet=name,cell=address),reasons))
        if not found:out.append(unit('',dict(kind='sheet',part=part,sheet=name),warnings+['EMPTY_SHEET']))
        merges=root.find(S+'mergeCells')
        if merges is not None:
            for index,merged in enumerate(merges.findall(S+'mergeCell'),1):
                ref=merged.get('ref')
                if not ref or not re.fullmatch(r'[A-Z]{1,3}[1-9][0-9]{0,6}(?::[A-Z]{1,3}[1-9][0-9]{0,6})?',ref):raise OfficeError('Invalid merged range')
                payload=dict(scope='DECLARED_MERGED_RANGE_UNVERIFIED',range=ref,values_propagated=False,layout_verified=False)
                out.append(unit(json.dumps(payload,ensure_ascii=False),dict(kind='merged_range',part=part,sheet=name,range=ref,merge_index=index),warnings+['MERGED_CELLS_UNVERIFIED']))
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
    source_path=Path(file['path'])
    def fingerprint():
        stat=source_path.stat()
        return stat.st_dev,stat.st_ino,stat.st_size,stat.st_mtime_ns,stat.st_ctime_ns
    source_fingerprint=fingerprint()
    prior=(job['result'] or {}).get('extraction',{})
    if prior and (prior.get('source_sha256')!=file['sha256'] or prior.get('parser_identity')!=config):raise ExtractionFailure('Идентичность Office/источника изменилась; создайте новое задание.')
    conversion=None
    try:
        data=Path(file['path']).read_bytes()
        if hashlib.sha256(data).hexdigest()!=file['sha256'] or fingerprint()!=source_fingerprint:raise OfficeError('Original identity changed')
        if backend=='doc':
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
        if key is not None and locator['kind']=='table_cell':tables.setdefault(str(key),[]).append(index)
    manifest=dict(scope='PARSED_LOGICAL_UNITS',declared_units=len(units),processed_units=0,unprocessed_units=len(units),
                  sheets=[dict(name=k,units=len(v)) for k,v in sheets.items()],
                  tables=[dict(table=k,cells=len(v)) for k,v in tables.items()],
                  physical_pages=None,limitations=limits,acceptance_granted=False)
    run['coverage_manifest']=manifest
    manifest['source_components']=dict(scope='DECLARED_STRUCTURE_NOT_COMPLETE_DOCUMENT',
        equations=sum(u['locator']['kind']=='equation' for u in units),
        word_cells_with_merge_declarations=sum(bool(u['locator'].get('declared_merge')) and u['locator']['kind']=='table_cell' for u in units),
        xlsx_merged_ranges=sum(u['locator']['kind']=='merged_range' for u in units),
        xlsx_formula_cells=sum(u['locator']['kind']=='cell' and json.loads(u['text']).get('formula_present',False) for u in units),
        formulas_evaluated=False,layout_verified=False)
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
        if fingerprint()!=source_fingerprint:raise ExtractionFailure('Office original changed during extraction')
        store.save_extraction_page(job['id'],dict(page=index,logical_unit=index,execution='COMPLETED',status='BLOCK' if reasons else 'UNCERTAINTY',
            blocks=blocks,stored_chars=len(text),text_truncated=clipped,limitations=reasons,locator=item['locator'],source_sha256=file['sha256'],
            scope='UNVERIFIED_EXTRACTION',ocr='NOT_APPLICABLE',acceptance_granted=False))
        checkpoint()
    verify_originals([file])
    if fingerprint()!=source_fingerprint:raise ExtractionFailure('Office original changed during extraction')
    run['cycle_complete']=run['processed_pages']==len(units);checkpoint()
    if run['budget_exhausted']:raise ExtractionFailure('Лимит сохранённого текста достигнут; часть элементов Office не обработана.')
    return result

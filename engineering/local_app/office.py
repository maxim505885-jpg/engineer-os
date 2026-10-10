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
MAX_TABLE_GRID_COLUMNS=1024
MAX_AUXILIARY_PARTS=128
MAX_IMAGE_BYTES=32*1024*1024
MAX_IMAGE_TOTAL_BYTES=256*1024*1024
MAX_IMAGE_REFERENCES=4096


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
        parent.pop('images',None);parent.pop('declared_drawing_labels',None)
        out.append(unit(json.dumps(payload,ensure_ascii=False),parent,word_limits(current)+['EQUATION_NOT_READ']))
        # Do not separately serialize nested equations, which duplicates syntax.
    return out


def word_table_grid(table):
    """Resolve declared source-column intervals only; never infer rendered cells."""
    grids=table.findall(W+'tblGrid');base=[]
    count=len(grids[0].findall(W+'gridCol')) if len(grids)==1 else 0
    if len(grids)!=1 or not count:base.append('TABLE_GRID_MISSING_OR_DUPLICATE')
    if count>MAX_TABLE_GRID_COLUMNS:base.append('TABLE_GRID_LIMIT')
    if grids and grids[0].find(W+'tblGridChange') is not None:base.append('TABLE_GRID_REVISION_UNVERIFIED')
    if any(child.tag not in {W+'tblPr',W+'tblGrid',W+'tr',W+'bookmarkStart',W+'bookmarkEnd'} for child in table):base.append('TABLE_STRUCTURE_UNVERIFIED')
    result={};active={}
    def number(parent,name,default,minimum,issues):
        found=parent.findall(W+name) if parent is not None else []
        if not found:return default
        raw=found[0].get(W+'val','')
        if len(found)!=1 or not re.fullmatch(r'\+?[0-9]{1,6}',raw) or not minimum<=int(raw)<=MAX_TABLE_GRID_COLUMNS:
            issues.append('INVALID_'+name.upper());return None
        return int(raw)
    for row_index,row in enumerate(table.findall(W+'tr'),1):
        row_issues=list(base);props=row.findall(W+'trPr')
        if len(props)>1:row_issues.append('DUPLICATE_ROW_PROPERTIES')
        props=props[0] if props else None
        if props is not None and any(e.tag in {W+'trPrChange',W+'ins',W+'del'} for e in props.iter()):row_issues.append('ROW_GRID_REVISION_UNVERIFIED')
        if any(child.tag not in {W+'trPr',W+'tc',W+'bookmarkStart',W+'bookmarkEnd'} for child in row):row_issues.append('ROW_STRUCTURE_UNVERIFIED')
        before=number(props,'gridBefore',0,0,row_issues);after=number(props,'gridAfter',0,0,row_issues)
        start=before+1 if before is not None else None;records=[]
        for column,cell in enumerate(row.findall(W+'tc'),1):
            issues=[];properties=cell.findall(W+'tcPr')
            if len(properties)>1:issues.append('DUPLICATE_CELL_PROPERTIES')
            properties=properties[0] if properties else None
            if properties is not None and any(e.tag in {W+'tcPrChange',W+'cellMerge',W+'cellIns',W+'cellDel'} for e in properties.iter()):issues.append('CELL_GRID_REVISION_UNVERIFIED')
            span=number(properties,'gridSpan',1,1,issues)
            interval=(start,start+span-1) if start is not None and span is not None else None
            if interval and interval[1]>MAX_TABLE_GRID_COLUMNS:issues.append('TABLE_GRID_LIMIT')
            merge=properties.findall(W+'vMerge') if properties is not None else []
            mode=merge[0].get(W+'val','continue') if merge else None
            if len(merge)>1 or mode not in {None,'restart','continue'}:issues.append('INVALID_VERTICAL_MERGE')
            if properties is not None and properties.find(W+'hMerge') is not None:issues.append('LEGACY_HORIZONTAL_MERGE_UNRESOLVED')
            anchor=None
            if mode=='restart':anchor=dict(row=row_index,column=column)
            elif mode=='continue':
                anchor=active.get(interval) if interval else None
                if anchor is None:issues.append('ORPHAN_VERTICAL_CONTINUE')
            records.append((column,interval,mode,anchor,issues))
            start=interval[1]+1 if interval else None
        width=start-1+after if start is not None and after is not None else None
        if width!=count:row_issues.append('ROW_GRID_WIDTH_MISMATCH')
        next_active={}
        for column,interval,mode,anchor,issues in records:
            combined=list(dict.fromkeys(row_issues+issues));valid=not combined
            grid=dict(scope='DECLARED_WORD_TABLE_GRID',status='CONSISTENT_SOURCE_STRUCTURE' if valid else 'UNRESOLVED_SOURCE_STRUCTURE',
                      declared_columns=count,row_grid_columns=width,grid_columns=list(interval) if interval else None,
                      vertical_merge=mode,vertical_anchor=anchor if valid else None,issues=combined,
                      values_propagated=False,layout_verified=False)
            result[(row_index,column)]=grid
            if valid and mode in {'restart','continue'}:next_active[interval]=anchor
        active=next_active
    return result


def word_container_units(body,part,package=None):
    out=[];paragraph=0;table=0
    def append(text,locator,warnings,element):
        if package is not None:
            from .word_images import bind_images
            images=bind_images(package,element,locator)
            if images:
                # Full descriptors belong to the source locator. Repeating record
                # geometry here can exhaust Store's text budget before the tail.
                compact=[]
                for image in images:
                    compact.append({k:image[k] for k in ('image','status','part','sha256','reason') if k in image})
                    for record in image.get('native_emf',{}).get('text_records',[]):
                        if record.get('text') is not None:
                            text+='\n[EMF '+str(image['image'])+'@'+str(record['record_offset'])+'] '+record['text']
                text+='\n'+json.dumps(dict(scope='PACKAGE_IMAGE_REFERENCES_UNVERIFIED',images=compact,
                                           details='SOURCE_LOCATOR',layout_verified=False,content_verified=False),ensure_ascii=False)
                warnings=list(warnings)+['IMAGE_CONTENT_NOT_VERIFIED','IMAGE_TRANSFORMS_NOT_APPLIED']
                if any(i['status']=='UNAVAILABLE' for i in images):warnings.append('IMAGE_REFERENCE_UNAVAILABLE')
                if any('native_emf' in i for i in images):
                    warnings+=['EMF_TEXT_PLACEMENT_UNVERIFIED','EMF_GRAPHICS_NOT_RENDERED']
                    if any(i.get('native_emf',{}).get('status')=='UNAVAILABLE' for i in images):warnings.append('EMF_NATIVE_TEXT_UNAVAILABLE')
        out.append(unit(text,locator,warnings))
    for child in body:
        if child.tag==W+'p':
            paragraph+=1;text=word_text(child);warnings=word_limits(child)
            locator=dict(kind='paragraph',part=part,paragraph=paragraph)
            # Image-only Word paragraphs have no w:t, but still carry source evidence.
            # Keep their logical unit so bind_images can preserve exact media refs.
            has_graphic=any(e.tag in {W+'drawing',W+'pict',W+'object'} for e in child.iter())
            if text or warnings or has_graphic:append(text,locator,warnings,child)
            out.extend(equation_units(child,locator))
        elif child.tag==W+'tbl':
            table+=1;grid=word_table_grid(child)
            for row_index,row in enumerate(child.findall(W+'tr'),1):
                for column,cell in enumerate(row.findall(W+'tc'),1):
                    warnings=word_limits(cell)
                    if any(e.tag in {W+'gridSpan',W+'vMerge',W+'hMerge'} for e in cell.iter()):warnings.append('MERGED_CELL_UNVERIFIED')
                    if cell.find('.//'+W+'tbl') is not None:warnings.append('NESTED_TABLE_UNVERIFIED')
                    text='\n'.join(word_text(e) for e in cell.findall(W+'p'))
                    locator=dict(kind='table_cell',part=part,table=table,row=row_index,column=column,source_grid=grid[(row_index,column)])
                    properties=cell.find(W+'tcPr');merge={}
                    if properties is not None:
                        for name in ('gridSpan','vMerge','hMerge'):
                            found=properties.find(W+name)
                            if found is not None:merge[name]=dict(found.attrib)
                    if locator['source_grid']['issues'] and (merge or child.find(W+'tblGrid') is not None):warnings.append('TABLE_GRID_UNRESOLVED')
                    if merge:
                        locator['declared_merge']=merge
                        text+='\n'+json.dumps(dict(scope='DECLARED_CELL_STRUCTURE_UNVERIFIED',column_kind='XML_CELL_ORDINAL',declared_merge=merge),ensure_ascii=False)
                    append(text,locator,warnings,cell)
                    out.extend(equation_units(cell,locator))
        elif child.tag!=W+'sectPr':
            locator=dict(kind='unsupported_body',part=part,body_index=list(body).index(child)+1)
            append(word_text(child),locator,['BODY_STRUCTURE_UNVERIFIED'],child)
            out.extend(equation_units(child,locator))
    return out


def read_docx(p):
    root=p.xml('word/document.xml');body=root.find(W+'body')
    if body is None:raise OfficeError('Missing Word body')
    out=word_container_units(body,'word/document.xml',p)
    limits=['PHYSICAL_PAGES_UNKNOWN','LAYOUT_NOT_VERIFIED']
    if any('/embeddings/' in n or 'vbaProject' in n for n in p.names):limits.append('EMBEDDED_CONTENT_NOT_READ')
    parts={n:('header' if n.startswith('word/header') else 'footer' if n.startswith('word/footer') else 'footnote' if n=='word/footnotes.xml' else 'endnote')
           for n in p.names if re.fullmatch(r'word/(?:header[^/]*|footer[^/]*|footnotes|endnotes)\.xml',n)}
    relations='word/_rels/document.xml.rels'
    if relations in p.names:
        from urllib.parse import unquote,urlsplit
        rel=p.xml(relations);namespace='{http://schemas.openxmlformats.org/package/2006/relationships}'
        if rel.tag!=namespace+'Relationships':raise OfficeError('Invalid Word relationships')
        count=0;identities=set()
        for relation in rel:
            kind=relation.get('Type','').rsplit('/',1)[-1]
            if kind not in {'header','footer','footnotes','endnotes'}:continue
            count+=1
            if count>MAX_AUXILIARY_PARTS:raise OfficeError('Auxiliary relationship limit')
            identity=relation.get('Id','')
            if not identity or identity in identities:raise OfficeError('Duplicate/missing auxiliary relationship ID')
            identities.add(identity)
            if relation.tag!=namespace+'Relationship' or relation.get('Type')!=R[1:-1]+'/'+kind:
                limits.append('HEADERS_FOOTNOTES_NOT_READ');continue
            target=relation.get('Target','');mode=relation.get('TargetMode','Internal')
            if mode=='External':limits.append('HEADERS_FOOTNOTES_NOT_READ');continue
            if mode!='Internal' or not target or len(target)>1024:raise OfficeError('Invalid auxiliary relationship target')
            target=unquote(target,encoding='utf-8',errors='strict');url=urlsplit(target)
            if url.scheme or url.netloc or url.query or url.fragment or '\\' in target or '\x00' in target:
                raise OfficeError('Invalid auxiliary relationship path')
            path=posixpath.normpath(target.lstrip('/') if target.startswith('/') else posixpath.join('word',target))
            if path in {'.','..'} or path.startswith('../'):raise OfficeError('Auxiliary path escapes package')
            if path not in p.names:limits.append('HEADERS_FOOTNOTES_NOT_READ');continue
            component={'footnotes':'footnote','endnotes':'endnote'}.get(kind,kind)
            if path in parts and parts[path]!=component:raise OfficeError('Conflicting auxiliary component identity')
            parts[path]=component
    if len(parts)>MAX_AUXILIARY_PARTS or any(len(n)>1024 for n in parts):raise OfficeError('Auxiliary Word part limit')
    if parts:limits.append('AUXILIARY_PLACEMENT_UNVERIFIED')
    for part,component in sorted(parts.items()):
        root=p.xml(part);expected={'header':'hdr','footer':'ftr','footnote':'footnotes','endnote':'endnotes'}[component]
        if root.tag!=W+expected:raise OfficeError('Invalid auxiliary Word root')
        containers=[(root,{})]
        if component in {'footnote','endnote'}:
            containers=[];seen=set()
            for note in root:
                note_id=note.get(W+'id','')
                if note.tag!=W+component or not re.fullmatch(r'-?[0-9]{1,10}',note_id) or int(note_id) in seen:
                    raise OfficeError('Invalid/duplicate Word note identity')
                seen.add(int(note_id))
                containers.append((note,dict(note_id=note_id,note_type=note.get(W+'type','normal'))))
        for container,identity in containers or [(root,{})]:
            items=word_container_units(container,part,p)
            if not items:items=[unit('',dict(kind='auxiliary_empty',part=part),['NO_TEXT'])]
            for item in items:
                item['locator'].update(component=component,scope='PACKAGE_PART_PLACEMENT_UNVERIFIED',**identity)
                item['limitations']=list(dict.fromkeys(item['limitations']+['AUXILIARY_PLACEMENT_UNVERIFIED']))
            out.extend(items)
            if len(out)>MAX_UNITS:raise OfficeError('Document unit limit')
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
        if key is not None and locator['kind']=='table_cell':tables.setdefault((locator['part'],locator.get('note_id'),str(key)),[]).append(index)
    manifest=dict(scope='PARSED_LOGICAL_UNITS',declared_units=len(units),processed_units=0,unprocessed_units=len(units),
                  sheets=[dict(name=k,units=len(v)) for k,v in sheets.items()],
                  tables=[dict(part=k[0],note_id=k[1],table=k[2],cells=len(v)) for k,v in tables.items()],
                  physical_pages=None,limitations=limits,acceptance_granted=False)
    run['coverage_manifest']=manifest
    manifest['source_components']=dict(scope='DECLARED_STRUCTURE_NOT_COMPLETE_DOCUMENT',
        equations=sum(u['locator']['kind']=='equation' for u in units),
        auxiliary_parts=sorted({u['locator']['part'] for u in units if u['locator'].get('component')}),
        auxiliary_units=sum(bool(u['locator'].get('component')) for u in units),
        auxiliary_placement_verified=False,
        image_references=sum(len(u['locator'].get('images',[])) for u in units),
        bound_image_references=sum(i['status']=='BOUND_PACKAGE_IMAGE' for u in units for i in u['locator'].get('images',[])),
        unavailable_image_references=sum(i['status']=='UNAVAILABLE' for u in units for i in u['locator'].get('images',[])),
        emf_text_records=sum(len(i.get('native_emf',{}).get('text_records',[])) for u in units for i in u['locator'].get('images',[])),
        emf_bitmap_records=sum(len(i.get('native_emf',{}).get('bitmap_records',[])) for u in units for i in u['locator'].get('images',[])),
        available_emf_bitmap_records=sum(b['status']=='AVAILABLE' for u in units for i in u['locator'].get('images',[]) for b in i.get('native_emf',{}).get('bitmap_records',[])),
        unavailable_emf_text_references=sum(i.get('native_emf',{}).get('status')=='UNAVAILABLE' for u in units for i in u['locator'].get('images',[])),
        image_content_verified=False,image_transforms_applied=False,
        word_cells_with_merge_declarations=sum(bool(u['locator'].get('declared_merge')) and u['locator']['kind']=='table_cell' for u in units),
        word_grid_consistent_cells=sum(u['locator']['kind']=='table_cell' and u['locator']['source_grid']['status']=='CONSISTENT_SOURCE_STRUCTURE' for u in units),
        word_grid_unresolved_cells=sum(u['locator']['kind']=='table_cell' and u['locator']['source_grid']['status']=='UNRESOLVED_SOURCE_STRUCTURE' for u in units),
        word_vertical_continuations_resolved=sum(u['locator']['kind']=='table_cell' and u['locator']['source_grid']['vertical_merge']=='continue' and u['locator']['source_grid']['vertical_anchor'] is not None for u in units),
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

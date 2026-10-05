"""Normalize an archived Docling export with explicitly mapped source grids.

No extraction/engineering completeness acceptance follows from table recovery.
"""
import argparse
import copy
import hashlib
import json
import math
import sys
from dataclasses import asdict
from pathlib import Path

if __package__ in (None,''):
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

from engineering.document_intelligence.docling_adapter import DoclingDocumentParser
from engineering.document_intelligence.contracts import DocumentParseError
from scripts.verify_pdf_recovery import recover, normalize


def table_digest(table):
    return hashlib.sha256(json.dumps(table,sort_keys=True,ensure_ascii=False,
                                    separators=(',',':'),allow_nan=False).encode()).hexdigest()


def verify_vector_replacement(source,grid,target):
    """Re-detect original vector cells; no image/text or engineering acceptance."""
    import fitz
    with fitz.open(source) as pdf:
        page=pdf[grid['source_page']-1]
        clip=grid.get('source_detection_clip')
        if (not isinstance(clip,list) or len(clip)!=4
                or any(type(v) not in (int,float) or not math.isfinite(v) for v in clip)
                or not 0<=clip[0]<clip[2]<=page.rect.width
                or not 0<=clip[1]<clip[3]<=page.rect.height):
            raise ValueError('invalid source grid detection clip')
        boxes={tuple(round(v,5) for v in c['source_fragment']['bbox']) for c in grid['cells']}
        detected=page.find_tables(clip=fitz.Rect(clip)).tables
        matches=[t for t in detected if {tuple(round(v,5) for v in b) for b in t.cells if b is not None}==boxes]
        if len(matches)!=1:raise ValueError('declared cells do not match original vector grid')
        box=fitz.Rect(grid['x_boundaries'][0],grid['y_boundaries'][0],grid['x_boundaries'][-1],grid['y_boundaries'][-1])
        b=target['prov'][0]['bbox']
        if any(type(b.get(k)) not in (int,float) or not 0<=b[k]<=limit
               for k,limit in [('l',page.rect.width),('r',page.rect.width),('t',page.rect.height),('b',page.rect.height)]):
            raise ValueError('target bbox outside original page')
        if b.get('coord_origin')=='BOTTOMLEFT':
            target_box=fitz.Rect(b['l'],page.rect.height-b['t'],b['r'],page.rect.height-b['b'])
        elif b.get('coord_origin')=='TOPLEFT':target_box=fitz.Rect(b['l'],b['t'],b['r'],b['b'])
        else:raise ValueError('invalid target coordinate origin')
        intersection=(box&target_box).get_area()
        union=box.get_area()+target_box.get_area()-intersection
        if union<=0 or intersection/union<.95:
            raise ValueError('target/source table regions differ')
        if any((fitz.Rect(image['bbox'])&box).get_area()>0 for image in page.get_image_info()):
            raise ValueError('source table contains unverified image content')
        for cell in grid['cells']:
            f=cell['source_fragment']
            if f['text'].strip():continue
            inner=fitz.Rect(f['bbox']);inner=fitz.Rect(inner.x0+1.5,inner.y0+1.5,inner.x1-1.5,inner.y1-1.5)
            if inner.is_empty:raise ValueError('empty cell too small for source blank verification')
            pix=page.get_pixmap(matrix=fitz.Matrix(2,2),clip=inner,colorspace=fitz.csGRAY,alpha=False)
            if any(v<220 for v in pix.samples):
                raise ValueError('native-empty source cell contains visible ink')


def preserve_source_context(source, grid, target, source_sha256):
    """Keep source pixels and outside words when neural bounds merge regions.

    This alternative does not certify the neural table or whole-page coverage.
    The physical grid is independently checked with its own exact boundaries.
    """
    import base64
    import fitz
    with fitz.open(source) as pdf:
        page=pdf[grid['source_page']-1]
        if page.rotation or page.cropbox.x0 or page.cropbox.y0:
            raise ValueError('context capture requires unrotated, zero-offset source')
        b=target['prov'][0]['bbox']
        if any(type(b.get(k)) not in (int,float) or not math.isfinite(b[k]) or not 0<=b[k]<=limit
               for k,limit in [('l',page.rect.width),('r',page.rect.width),('t',page.rect.height),('b',page.rect.height)]):
            raise ValueError('target bbox outside original page')
        if b.get('coord_origin')=='BOTTOMLEFT':
            target_box=fitz.Rect(b['l'],page.rect.height-b['t'],b['r'],page.rect.height-b['b'])
        elif b.get('coord_origin')=='TOPLEFT':target_box=fitz.Rect(b['l'],b['t'],b['r'],b['b'])
        else:raise ValueError('invalid target coordinate origin')
        box=fitz.Rect(grid['x_boundaries'][0],grid['y_boundaries'][0],grid['x_boundaries'][-1],grid['y_boundaries'][-1])
        intersection=(box&target_box).get_area()
        if target_box.is_empty or intersection<=0:
            raise ValueError('target does not intersect source grid')
        if max(intersection/box.get_area(),intersection/target_box.get_area())<.95:
            raise ValueError('target and source grid lack substantial containment')
        exact=dict(prov=[dict(page_no=grid['source_page'],bbox=dict(l=box.x0,t=box.y0,r=box.x1,b=box.y1,coord_origin='TOPLEFT'))])
        verify_vector_replacement(source,grid,exact)
        # Preserve the entire bounding union, including symbols, pictures and
        # ink that the text layer cannot describe. Never call outside words blank.
        union=box|target_box
        words=page.get_text('words',sort=True)
        outside=[w for w in words if (union&fitz.Rect(w[:4])).get_area()>0 and not box.contains(fitz.Rect(w[:4]))]
        if union.get_area()*4>40000000:
            raise ValueError('source context exceeds bounded render size')
        pix=page.get_pixmap(matrix=fitz.Matrix(2,2),clip=union,alpha=False)
        data=pix.tobytes('png')
        return dict(block_id='source-context:'+grid['table_id'],kind='source_context',text=' '.join(w[4] for w in outside),
                    source_sha256=source_sha256,table_id=grid['table_id'],original_target_sha256=table_digest(target),
                    original_target_bbox=dict(b),source_grid_bbox=list(box),
                    provenance=[dict(page_no=grid['source_page'],bbox=dict(left=union.x0,top=union.y0,right=union.x1,bottom=union.y1))],
                    native_words=[dict(text=w[4],bbox=list(w[:4])) for w in outside],
                    source_visual=dict(sha256=hashlib.sha256(data).hexdigest(),png_base64=base64.b64encode(data).decode('ascii'),
                        mime_type='image/png',source_page=grid['source_page'],bbox=list(union),coordinate_origin='TOPLEFT',render_scale=2,
                        rendered_pixel_origin=[pix.x,pix.y],width_px=pix.width,height_px=pix.height,annotations_rendered=True),
                    source_capture_status='PASS',interpretation_status='UNCERTAINTY',evidentiary_status='NOT_EVIDENCE',
                    complete_page=False,acceptance_granted=False)


def recover_export(source, raw, manifest, *, project_id, document_id):
    manifest=manifest if isinstance(manifest,dict) else {}
    result=dict(parser='docling_source_grid_recovery',project_id=project_id,
                document_id=document_id,source_sha256=manifest.get('source_sha256'),
                status='BLOCK',document_status='BLOCK',complete_page=False,
                complete_document=False,evidentiary_status='NOT_EVIDENCE',
                acceptance_granted=False,blocks=[],table_recovery=dict(
                    resolved_table_indices=[],unresolved_tables=[]))
    try:
        import fitz
        if not isinstance(raw,dict):raise ValueError('raw export must be an object')
        if manifest.get('schema_version')!=2:
            raise ValueError('explicit schema2 grids required')
        with fitz.open(source) as pdf:
            sizes={i+1:(p.rect.width,p.rect.height) for i,p in enumerate(pdf)}
            def read_text(page,box):
                return ' '.join(w[4] for w in pdf[page-1].get_text('words',sort=True)
                    if box[0]<=(w[0]+w[2])/2<box[2] and box[1]<=(w[1]+w[3])/2<box[3])
            checked=recover(Path(source),manifest,project_id=project_id,
                document_id=document_id,page_sizes=sizes,read_text=read_text)
        tables=raw.get('tables') or []
        if not isinstance(tables,list):raise ValueError('invalid raw tables')
        mappings={}
        contexts=[]
        for grid in checked['tables']:
            index=grid.get('docling_table_index')
            if type(index) is not int or not 0<=index<len(tables) or index in mappings:
                raise ValueError('missing, duplicate or invalid target table index')
            target=tables[index]
            if grid.get('docling_table_sha256')!=table_digest(target):
                raise ValueError('target table digest mismatch')
            prov=target.get('prov') or []
            if len(prov)!=1 or prov[0].get('page_no')!=grid['source_page']:
                raise ValueError('target source page mismatch')
            data=target.get('data') or {}
            mode=grid.get('replacement_mode','MATCH_MODEL_GRID')
            if mode=='SOURCE_VECTOR_CONTEXT':
                contexts.append(preserve_source_context(source,grid,target,manifest['source_sha256']))
                mappings[index]=grid['table_id']
                continue
            if mode=='SOURCE_VECTOR_GRID':
                verify_vector_replacement(source,grid,target)
                mappings[index]=grid['table_id']
                continue
            if mode!='MATCH_MODEL_GRID':raise ValueError('unsupported source replacement mode')
            if any(type(data.get(k)) is not int for k in ('num_rows','num_cols')):
                raise ValueError('invalid model dimensions')
            if data.get('num_rows')!=len(grid['y_boundaries'])-1 or data.get('num_cols')!=len(grid['x_boundaries'])-1:
                raise ValueError('source/model grid dimensions differ')
            def model_cells():
                return sorted((c['start_row_offset_idx'],c['end_row_offset_idx'],c['start_col_offset_idx'],c['end_col_offset_idx'],normalize(c['text'])) for c in data['table_cells'])
            source_cells=sorted((c['row_start'],c['row_end'],c['col_start'],c['col_end'],normalize(c['source_fragment']['text'])) for c in grid['cells'])
            if model_cells()!=source_cells:raise ValueError('source/model cell coverage or text differs')
            mappings[index]=grid['table_id']
        normalization_input=copy.deepcopy(raw)
        normalization_input['pages']={str(p):dict(size=dict(width=w,height=h)) for p,(w,h) in sizes.items()}
        result['blocks']=[dict(asdict(b),source_binding_status='UNCHECKED')
                          for b in DoclingDocumentParser._normalize(normalization_input)]
        for block in result['blocks']:
            for ref in block['provenance']:
                page=ref['page_no'];box=ref['bbox']
                if page not in sizes or box is None:
                    raise ValueError('raw block has invalid source location')
                width,height=sizes[page]
                if box['right']>width or box['bottom']>height:
                    raise ValueError('raw block outside source page')
        for index,table in enumerate(tables):
            if index in mappings:
                result['blocks'].extend(dict(b,source_binding_status='PASS') for b in checked['blocks'] if b.get('table_id')==mappings[index])
                result['table_recovery']['resolved_table_indices'].append(index)
                continue
            try:
                rows=DoclingDocumentParser._table_rows({'tables':[table]})
                for b in rows:
                    if any(ref.page_no not in sizes for ref in b.provenance):
                        raise ValueError('raw table row source page outside PDF')
                    block=asdict(b);block['block_id']=f'raw-table:{index}:'+block['block_id']
                    block['source_binding_status']='UNCHECKED'
                    result['blocks'].append(block)
            except DocumentParseError as exc:
                result['table_recovery']['unresolved_tables'].append(dict(table_index=index,reason=str(exc)))
        result['blocks'].extend(contexts)
        if contexts:
            result['table_recovery']['preserved_context_indices']=[g['docling_table_index'] for g in checked['tables'] if g.get('replacement_mode')=='SOURCE_VECTOR_CONTEXT']
        if not tables or not result['blocks']:
            raise ValueError('no tables or extracted content for recovery')
        # Captions and body extraction outside these table regions are not
        # certified by this operation. UNCERTAINTY concerns table normalization.
        if not result['table_recovery']['unresolved_tables']:
            result['status']='UNCERTAINTY'
        result['source_binding_audit']=checked['source_binding_audit']
        result['scope']='Mapped table normalization only; page/document completeness and semantics unverified'
    except (ImportError,OSError,ValueError,KeyError,TypeError,AttributeError,OverflowError,RuntimeError,DocumentParseError) as exc:
        result.update(status='BLOCK',blocks=[],reason=str(exc))
        result['table_recovery']['resolved_table_indices']=[]
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source',type=Path)
    parser.add_argument('raw_export',type=Path)
    parser.add_argument('manifest',type=Path)
    parser.add_argument('--project-id',required=True)
    parser.add_argument('--document-id',required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if any(args.output.resolve()==p.resolve() or
           (args.output.exists() and p.exists() and args.output.samefile(p))
           for p in (args.source,args.raw_export,args.manifest)):
        parser.error('output must not overwrite source inputs')
    try:
        raw=json.loads(args.raw_export.read_text(encoding='utf-8'))
        if isinstance(raw,dict):raw=raw.get('raw_docling',raw)
        manifest=json.loads(args.manifest.read_text(encoding='utf-8'))
        result=recover_export(args.source,raw,manifest,project_id=args.project_id,document_id=args.document_id)
    except (OSError,UnicodeError,ValueError) as exc:
        result=dict(status='BLOCK',document_status='BLOCK',complete_page=False,complete_document=False,
                    acceptance_granted=False,evidentiary_status='NOT_EVIDENCE',blocks=[],reason=str(exc))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(result['status'])
    return 2 if result['status']=='BLOCK' else 0


if __name__=='__main__':
    raise SystemExit(main())

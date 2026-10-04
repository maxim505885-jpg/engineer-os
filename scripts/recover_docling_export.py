"""Normalize an archived Docling export with explicitly mapped source grids.

No extraction/engineering completeness acceptance follows from table recovery.
"""
import argparse
import copy
import hashlib
import json
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
        if not tables or not result['blocks']:
            raise ValueError('no tables or extracted content for recovery')
        # Captions and body extraction outside these table regions are not
        # certified by this operation. UNCERTAINTY concerns table normalization.
        if not result['table_recovery']['unresolved_tables']:
            result['status']='UNCERTAINTY'
        result['source_binding_audit']=checked['source_binding_audit']
        result['scope']='Mapped table normalization only; page/document completeness and semantics unverified'
    except (ImportError,OSError,ValueError,KeyError,TypeError,AttributeError,RuntimeError,DocumentParseError) as exc:
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

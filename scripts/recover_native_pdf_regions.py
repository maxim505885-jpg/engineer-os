"""Recover declared native PDF grids independently of neural table detection.

This exports selected physical regions, not a replacement for a full Docling
page, an OCR certificate, a semantic header interpretation or accepted evidence.
"""
import argparse
import json
import sys
from pathlib import Path

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.recover_docling_export import verify_vector_replacement
from scripts.verify_pdf_recovery import recover


def blocked(reason, *, project_id, document_id):
    return dict(parser='native_pdf_vector_regions',status='BLOCK',document_status='BLOCK',
                project_id=project_id,document_id=document_id,blocks=[],complete_page=False,
                complete_document=False,acceptance_granted=False,evidentiary_status='NOT_EVIDENCE',
                replacement_of_docling_export=False,reason=reason)


def recover_native_regions(source, manifest, *, project_id, document_id):
    try:
        import fitz
        if not isinstance(manifest,dict) or manifest.get('schema_version') != 2:
            raise ValueError('explicit schema2 source grids required')
        with fitz.open(source) as pdf:
            sizes = {i+1:(p.rect.width,p.rect.height) for i,p in enumerate(pdf)}
            def read_text(number,box):
                return ' '.join(w[4] for w in pdf[number-1].get_text('words',sort=True)
                    if box[0] <= (w[0]+w[2])/2 < box[2] and box[1] <= (w[1]+w[3])/2 < box[3])
            result = recover(Path(source),manifest,project_id=project_id,
                             document_id=document_id,page_sizes=sizes,read_text=read_text)
        for grid in result['tables']:
            # There is no neural table to replace. The independent route's
            # region is the declared original grid itself; the shared checker
            # re-detects its exact cells and rejects images/nonblank empty cells.
            region = dict(prov=[dict(page_no=grid['source_page'],bbox=dict(
                l=grid['x_boundaries'][0],r=grid['x_boundaries'][-1],
                t=grid['y_boundaries'][0],b=grid['y_boundaries'][-1],coord_origin='TOPLEFT'))])
            verify_vector_replacement(source,grid,region)
        result.update(parser='native_pdf_vector_regions',complete_page=False,
                      replacement_of_docling_export=False,
                      scope='Declared native vector regions only; surrounding content, semantic relationships, OCR and page/document completeness unverified')
        result['source_binding_audit']['physical_grid_status']='PASS'
        result['source_binding_audit']['scope']='Declared original vector cells, native text and native-empty cell ink checks only'
        for block in result['blocks']:
            block['source_binding_status']='PASS'
        return result
    except (ImportError,OSError,ValueError,KeyError,TypeError,AttributeError,OverflowError,RuntimeError) as exc:
        return blocked(str(exc),project_id=project_id,document_id=document_id)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source',type=Path)
    parser.add_argument('manifest',type=Path)
    parser.add_argument('--project-id',required=True)
    parser.add_argument('--document-id',required=True)
    parser.add_argument('--output',required=True,type=Path)
    args = parser.parse_args()
    if any(args.output.resolve()==p.resolve() or (args.output.exists() and p.exists() and args.output.samefile(p))
           for p in (args.source,args.manifest)):
        parser.error('output must not overwrite source inputs')
    try:
        manifest = json.loads(args.manifest.read_text(encoding='utf-8'))
        result = recover_native_regions(args.source,manifest,project_id=args.project_id,document_id=args.document_id)
    except (OSError,UnicodeError,ValueError) as exc:
        result = blocked(str(exc),project_id=args.project_id,document_id=args.document_id)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(result['status'])
    return 2 if result['status']=='BLOCK' else 0


if __name__ == '__main__':
    raise SystemExit(main())

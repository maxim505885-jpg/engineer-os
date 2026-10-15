"""Preserve declared mixed PDF grid cells as source-bound visual assets.

Native text is only a text-layer transcription. An empty native string never
means an image/signature/diagram cell is visually blank. No OCR interpretation,
page completeness or evidence acceptance follows from this capture.
"""
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

if __package__ in (None,''):
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

from scripts.verify_pdf_recovery import recover
from scripts.recover_native_pdf_regions import blocked


def capture_grid_assets(source,manifest,output_dir,*,project_id,document_id,protected_inputs=()):
    source,output_dir=Path(source),Path(output_dir)
    try:
        import fitz
        if not isinstance(manifest,dict) or manifest.get('schema_version')!=2:
            raise ValueError('explicit schema2 source grids required')
        with fitz.open(source) as pdf:
            sizes={i+1:(p.rect.width,p.rect.height) for i,p in enumerate(pdf)}
            def read_text(number,box):
                return ' '.join(w[4] for w in pdf[number-1].get_text('words',sort=True)
                    if box[0]<=(w[0]+w[2])/2<box[2] and box[1]<=(w[1]+w[3])/2<box[3])
            result=recover(source,manifest,project_id=project_id,document_id=document_id,
                           page_sizes=sizes,read_text=read_text)
            # Validate every physical grid before writing any visual assets.
            for grid in result['tables']:
                page=pdf[grid['source_page']-1]
                if page.rotation or page.cropbox.x0 or page.cropbox.y0:
                    raise ValueError('rotated or offset-crop pages need a separate transform')
                clip=grid.get('source_detection_clip')
                if (not isinstance(clip,list) or len(clip)!=4
                        or any(type(v) not in (int,float) or not math.isfinite(v) for v in clip)
                        or not 0<=clip[0]<clip[2]<=page.rect.width
                        or not 0<=clip[1]<clip[3]<=page.rect.height):
                    raise ValueError('invalid original grid detection clip')
                boxes={tuple(round(v,5) for v in c['source_fragment']['bbox']) for c in grid['cells']}
                matches=[t for t in page.find_tables(clip=fitz.Rect(clip)).tables
                    if {tuple(round(v,5) for v in b) for b in t.cells if b is not None}==boxes]
                if len(matches)!=1:
                    raise ValueError('declared cells do not match original vector grid')
            count=0
            for ti,grid in enumerate(result['tables']):
                page=pdf[grid['source_page']-1]
                images=page.get_image_info()
                for ci,cell in enumerate(grid['cells']):
                    box=fitz.Rect(cell['source_fragment']['bbox'])
                    path=output_dir/f'table-{ti:05d}-cell-{ci:05d}.png'
                    if path.resolve()==source.resolve() or (path.exists() and path.samefile(source)):
                        raise ValueError('visual asset must not overwrite original source')
                    if any(path.resolve()==Path(p).resolve() or (path.exists() and Path(p).exists() and path.samefile(p))
                           for p in protected_inputs):
                        raise ValueError('visual asset must not overwrite input manifest')
                    pix=page.get_pixmap(matrix=fitz.Matrix(2,2),clip=box,alpha=False)
                    data=pix.tobytes('png')
                    output_dir.mkdir(parents=True,exist_ok=True)
                    path.write_bytes(data)
                    cell['visual_asset']=dict(path=path.name,sha256=hashlib.sha256(data).hexdigest(),
                        source_sha256=result['source_sha256'],source_page=grid['source_page'],
                        bbox=list(box),coordinate_origin='TOPLEFT',render_scale=2,
                        rendered_pixel_origin=[pix.x,pix.y],width_px=pix.width,height_px=pix.height,
                        contains_source_image=any((box&fitz.Rect(i['bbox'])).get_area()>0 for i in images),
                        native_empty_is_visual_blank=False,annotations_rendered=True,
                        source_capture_status='PASS',interpretation_status='UNCERTAINTY',
                        visual_review_status='NOT_RUN',evidentiary_status='NOT_EVIDENCE')
                    count+=1
            if hashlib.sha256(source.read_bytes()).hexdigest()!=result['source_sha256']:
                raise ValueError('original source changed during capture')
        assets={(g['table_id'],c['cell_id']):c['visual_asset'] for g in result['tables'] for c in g['cells']}
        for block in result['blocks']:
            if block.get('kind')=='table_cell':
                block['visual_asset']=assets[(block['table_id'],block['cell_id'])]
                block['content_interpretation_status']='UNCERTAINTY'
        result.update(parser='pdf_grid_visual_capture',complete_page=False,
                      visual_asset_count=count,replacement_of_docling_export=False,
                      scope='Selected original physical grid cells with native text and rendered visual assets; visual/semantic interpretation, OCR and page/document completeness unverified')
        result['source_binding_audit'].update(physical_grid_status='PASS',
            scope='Declared original physical grid, native text-layer binding and rendered source-asset identity only')
        return result
    except (ImportError,OSError,ValueError,KeyError,TypeError,AttributeError,OverflowError,RuntimeError) as exc:
        result=blocked(str(exc),project_id=project_id,document_id=document_id)
        result.update(parser='pdf_grid_visual_capture',visual_asset_count=0)
        return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source',type=Path)
    parser.add_argument('manifest',type=Path)
    parser.add_argument('--project-id',required=True)
    parser.add_argument('--document-id',required=True)
    parser.add_argument('--output-dir',required=True,type=Path)
    args=parser.parse_args()
    result_path=args.output_dir/'capture.json'
    if any(result_path.resolve()==p.resolve() or (result_path.exists() and p.exists() and result_path.samefile(p))
           for p in (args.source,args.manifest)):
        parser.error('output must not overwrite source inputs')
    try:
        manifest=json.loads(args.manifest.read_text(encoding='utf-8'))
        result=capture_grid_assets(args.source,manifest,args.output_dir,
                                   project_id=args.project_id,document_id=args.document_id,
                                   protected_inputs=[args.manifest])
    except (OSError,UnicodeError,ValueError) as exc:
        result=blocked(str(exc),project_id=args.project_id,document_id=args.document_id)
    args.output_dir.mkdir(parents=True,exist_ok=True)
    result_path.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(result['status'])
    return 2 if result['status']=='BLOCK' else 0


if __name__=='__main__':
    raise SystemExit(main())

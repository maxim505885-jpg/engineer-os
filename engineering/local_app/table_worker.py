"""Isolated, network-denied optional raster table adapter. Invoke with -m."""
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import sys
from .table_readback import MAX_SOURCE_BYTES, MAX_OUTPUT_BYTES, MAX_PIXELS, MAX_TABLES, MAX_CELLS, unavailable


def geometry(box, raster, selected):
    values = [float(v) for v in box]
    if len(values) != 4 or not all(math.isfinite(v) for v in values):
        raise ValueError('INVALID_TABLE_GEOMETRY')
    left, top, right, bottom = values
    if not 0 <= left < right <= raster['width'] or not 0 <= top < bottom <= raster['height']:
        raise ValueError('TABLE_GEOMETRY_OUTSIDE_RASTER')
    origin = raster['pixel_origin']; scale = raster['scale']
    mapped = [(left+origin[0])/scale, (top+origin[1])/scale,
              (right+origin[0])/scale, (bottom+origin[1])/scale]
    clipped = [max(mapped[0], selected[0]), max(mapped[1], selected[1]),
               min(mapped[2], selected[2]), min(mapped[3], selected[3])]
    if clipped[0] >= clipped[2] or clipped[1] >= clipped[3]:
        raise ValueError('TABLE_GEOMETRY_OUTSIDE_SELECTION')
    return dict(pixel_bbox=values, source_bbox=clipped,
                source_bbox_before_selection_clip=mapped, selection_boundary_clipped=mapped != clipped)


def img_tables(png, language):
    if importlib.metadata.version('img2table') != '1.4.2':
        raise ValueError('IMG2TABLE_VERSION_MISMATCH')
    from img2table.document import Image
    from img2table.ocr import TesseractOCR
    import shutil
    import subprocess
    binary = shutil.which('tesseract')
    if not binary:
        return None, 'TESSERACT_UNAVAILABLE'
    languages = subprocess.run([binary, '--list-langs'], capture_output=True, text=True, timeout=10)
    if any(part not in languages.stdout.splitlines() for part in language.split('+')):
        return None, 'TESSERACT_LANGUAGE_UNAVAILABLE'
    tables = Image(src=png, detect_rotation=False).extract_tables(
        ocr=TesseractOCR(n_threads=1, lang=language), implicit_rows=False,
        implicit_columns=False, borderless_tables=False)
    result=[]
    for table in tables:
        if len(result) >= MAX_TABLES:
            raise ValueError('TABLE_COUNT_LIMIT')
        unique={}
        count=0
        for row, entries in table.content.items():
            for column, cell in enumerate(entries):
                count+=1
                if count > MAX_CELLS:
                    raise ValueError('TABLE_CELL_LIMIT')
                box=cell.bbox
                key=(box.x1, box.y1, box.x2, box.y2)
                item=unique.setdefault(key, dict(text=cell.value, bbox=list(key), positions=[]))
                item['positions'].append((int(row), column))
        cells=[]
        for cell in unique.values():
            positions=cell.pop('positions'); rows=[p[0] for p in positions]; cols=[p[1] for p in positions]
            cell.update(row=min(rows), column=min(cols), row_span=max(rows)-min(rows)+1,
                        column_span=max(cols)-min(cols)+1, confidence=None,
                        span_basis='REPEATED_CELL_GEOMETRY')
            cells.append(cell)
        box=table.bbox
        result.append(dict(bbox=[box.x1,box.y1,box.x2,box.y2], cells=cells, confidence=None))
    return result, None


def paddle_tables(png, language):
    # Never instantiate Paddle's auto-resolving default pipeline. All six models
    # used by this profile must be existing explicit local directories.
    config_path=os.environ.get('ENGINEER_OS_PADDLE_MODELS_MANIFEST')
    if not config_path or not Path(config_path).is_file():
        return None, 'PADDLE_LOCAL_MODELS_NOT_CONFIGURED'
    manifest=Path(config_path)
    if manifest.stat().st_size > 65536:
        return None, 'PADDLE_MANIFEST_SIZE_LIMIT'
    config=json.loads(manifest.read_text())
    keys=('layout_detection_model_dir','text_detection_model_dir','text_recognition_model_dir',
          'table_classification_model_dir','wired_table_structure_recognition_model_dir',
          'wireless_table_structure_recognition_model_dir','wired_table_cells_detection_model_dir',
          'wireless_table_cells_detection_model_dir')
    if set(config) != set(keys) or any(not isinstance(config[k], str) or not Path(config[k]).is_absolute()
                                     or not Path(config[k]).is_dir() for k in keys):
        return None, 'PADDLE_LOCAL_MODELS_INCOMPLETE'
    if importlib.metadata.version('paddleocr') != '3.2.0':
        return None, 'PADDLE_VERSION_MISMATCH'
    if any(not (Path(config[k]) / 'inference.pdiparams').is_file() or
           not any((Path(config[k]) / name).is_file() for name in ('inference.json','inference.pdmodel')) for k in keys):
        return None, 'PADDLE_LOCAL_WEIGHTS_INCOMPLETE'
    from paddleocr import PPStructureV3
    import numpy as np
    from PIL import Image
    import io
    pipeline=PPStructureV3(**config, device='cpu', use_doc_orientation_classify=False,
        use_doc_unwarping=False, use_textline_orientation=False, use_formula_recognition=False,
        use_chart_recognition=False, use_seal_recognition=False)
    result=[]
    for prediction in pipeline.predict(np.array(Image.open(io.BytesIO(png)).convert('RGB'))):
        payload=prediction.json
        if callable(payload): payload=payload()
        if isinstance(payload,str): payload=json.loads(payload)
        payload=payload.get('res',payload)
        for table in payload.get('table_res_list',[]):
            if len(result) >= MAX_TABLES:
                raise ValueError('TABLE_COUNT_LIMIT')
            # Geometry and structure are separate Paddle outputs. Never invent a
            # cell-to-HTML association when the pipeline has not supplied one.
            boxes=table.get('cell_box_list',[])
            if len(boxes)>MAX_CELLS:
                raise ValueError('TABLE_CELL_LIMIT')
            cells=[]
            for box in boxes:
                points=np.array(box).reshape(-1,2)
                cells.append(dict(bbox=[float(points[:,0].min()),float(points[:,1].min()),
                    float(points[:,0].max()),float(points[:,1].max())], text=None, row=None,
                    column=None,row_span=None,column_span=None, confidence=None,
                    span_basis='NOT_SUPPLIED'))
            if not cells:
                continue
            extent=[min(c['bbox'][0] for c in cells),min(c['bbox'][1] for c in cells),
                    max(c['bbox'][2] for c in cells),max(c['bbox'][3] for c in cells)]
            result.append(dict(bbox=extent, geometry_basis='CELL_GEOMETRY_ENVELOPE', cells=cells, confidence=None,
                               structure_html=table.get('pred_html'), structure_cell_mapping='UNVERIFIED'))
    return result,None


def execute(request):
    import fitz
    backend=request['backend']; path=Path(request['source'])
    if path.stat().st_size > MAX_SOURCE_BYTES:
        raise ValueError('SOURCE_SIZE_LIMIT')
    raw=path.read_bytes(); sha=hashlib.sha256(raw).hexdigest()
    if sha != request['source_sha256']:
        raise ValueError('SOURCE_SHA256_MISMATCH')
    with fitz.open(stream=raw,filetype='pdf') as document:
        if document.needs_pass: raise ValueError('PDF_PASSWORD_REQUIRED')
        if len(document)>5000: raise ValueError('PAGE_COUNT_LIMIT')
        number=request['page']
        if type(number) is not int or not 1<=number<=len(document): raise ValueError('INVALID_PAGE')
        page=document[number-1]; rotation=page.rotation; cropbox=list(page.cropbox); page.set_rotation(0)
        selected=request['bbox']; left,top,right,bottom=selected
        if not 0<=left<right<=page.rect.width or not 0<=top<bottom<=page.rect.height:
            raise ValueError('INVALID_REGION')
        clip=fitz.Rect(selected); scale=min(4.0,3000/max(clip.width,clip.height))
        if (math.ceil(clip.width*scale)+2)*(math.ceil(clip.height*scale)+2)>MAX_PIXELS:
            raise ValueError('TABLE_PIXEL_LIMIT')
        pixels=page.get_pixmap(matrix=fitz.Matrix(scale,scale),clip=clip,colorspace=fitz.csRGB,alpha=False)
        if pixels.width*pixels.height>MAX_PIXELS: raise ValueError('TABLE_PIXEL_LIMIT')
        png=pixels.tobytes('png')
        raster=dict(width=pixels.width,height=pixels.height,scale=scale,pixel_origin=[pixels.x,pixels.y],
            pixel_sha256=hashlib.sha256(pixels.samples).hexdigest(),png_sha256=hashlib.sha256(png).hexdigest(),
            colorspace='RGB',source_bbox=selected,rendered_input_equivalence='EXACT_BACKEND_INPUT_PNG',
            mapping='source_point=(raster_pixel+pixel_origin)/scale; clipped to selection')
        language=os.environ.get('ENGINEER_OS_TABLE_LANG','eng')
        if not language or len(language)>64 or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_+' for c in language):
            raise ValueError('INVALID_TABLE_LANGUAGE')
        try:
            if request.get('unavailable_reason'):
                tables, reason = None, request['unavailable_reason']
            else:
                tables, reason=(img_tables if backend=='img2table' else paddle_tables)(png,language)
        except (ImportError,importlib.metadata.PackageNotFoundError):
            tables,reason=None,'TABLE_DEPENDENCIES_UNAVAILABLE'
        result=dict(status='UNCERTAINTY',backend=backend,source_sha256=sha,page_no=number,
            source_bbox=selected,coordinate_space='UNROTATED_CROP_RELATIVE',source_page=dict(
            rotation=rotation,cropbox=cropbox,width=page.rect.width,height=page.rect.height),
            raster=raster,language=language,language_application='TESSERACT_LANG' if backend=='img2table' else 'LOCAL_RECOGNITION_MODEL_LANGUAGE_UNVERIFIED',tables=[],acceptance_granted=False,quality_verified=False,
            process_isolated=True,network_denied=not request.get('sandbox_unavailable',False),
            network_isolation='NOT_ENFORCED' if request.get('sandbox_unavailable',False) else 'LINUX_SECCOMP_DENY',limitations=['SELECTED_REGION_ONLY',
            'TABLE_STRUCTURE_AND_TEXT_UNVERIFIED','SOURCE_REVIEW_REQUIRED','NO_ENGINEERING_ACCEPTANCE'])
        if reason:
            result.update(status='UNAVAILABLE',reason=reason)
            return result
        if len(tables)>MAX_TABLES or sum(len(t['cells']) for t in tables)>MAX_CELLS:
            raise ValueError('TABLE_COUNT_OR_CELL_LIMIT')
        for index,table in enumerate(tables):
            table.update(geometry(table.pop('bbox'),raster,selected),candidate_id=f'table:{number}:{index}',
                         status='UNCERTAINTY',acceptance_granted=False)
            for cell in table['cells']:
                cell.update(geometry(cell.pop('bbox'),raster,selected))
        result['tables']=tables
        result['table_count']=len(tables)
        result['backend_version']=importlib.metadata.version('img2table' if backend=='img2table' else 'paddleocr')
        result['engine_identity']=dict(backend=backend,version=result['backend_version'],language=language)
        if backend=='paddleocr':
            manifest=Path(os.environ['ENGINEER_OS_PADDLE_MODELS_MANIFEST'])
            result['engine_identity']['local_models_manifest_sha256']=hashlib.sha256(manifest.read_bytes()).hexdigest()
        return result


def main():
    try:
        sandbox_unavailable = sys.platform != 'linux'
        if not sandbox_unavailable:
            import resource
            from .doc_sandbox import apply
            try:
                apply()
                resource.setrlimit(resource.RLIMIT_FSIZE,(MAX_OUTPUT_BYTES,MAX_OUTPUT_BYTES))
            except RuntimeError:
                sandbox_unavailable = True
        raw=sys.stdin.buffer.read(65537)
        if len(raw)>65536: raise ValueError('TABLE_REQUEST_LIMIT')
        request=json.loads(raw)
        if sandbox_unavailable:
            request.update(sandbox_unavailable=True)
        # Backend packages print diagnostics; isolate them from protocol stdout.
        protocol=os.dup(sys.stdout.fileno())
        os.dup2(sys.stderr.fileno(),sys.stdout.fileno())
        try: result=execute(request)
        finally:
            sys.stdout.flush(); os.dup2(protocol,sys.stdout.fileno()); os.close(protocol)
    except Exception as exc:
        result=dict(status='ERROR',reason=str(exc)[:200] if isinstance(exc,ValueError) else 'TABLE_WORKER_FAILED',
                    tables=[],acceptance_granted=False,quality_verified=False)
    output=json.dumps(result,ensure_ascii=False,allow_nan=False).encode()
    if len(output)>MAX_OUTPUT_BYTES:
        output=b'{"status":"ERROR","reason":"TABLE_OUTPUT_LIMIT","tables":[],"acceptance_granted":false}'
    sys.stdout.buffer.write(output)


if __name__=='__main__': main()

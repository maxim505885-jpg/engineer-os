"""Render every source PDF page and expose native/OCR gaps; never certify content."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from engineering.local_app.extraction import MAX_PAGES
from engineering.local_app.files import MAX_FILE_BYTES


def audit(source,output,*,ocr_gaps=False):
    import fitz
    source=Path(source).resolve();output=Path(output).resolve()
    if not source.is_file() or source.suffix.lower()!='.pdf':raise ValueError('PDF original required')
    if output==source or (output.exists() and (not output.is_dir() or any(output.iterdir()))):
        raise ValueError('A new empty audit directory is required')
    if not 0<source.stat().st_size<=MAX_FILE_BYTES:raise ValueError('Source byte limit')
    with source.open('rb') as stream:raw=stream.read(MAX_FILE_BYTES+1)
    if not 0<len(raw)<=MAX_FILE_BYTES:raise ValueError('Source byte limit')
    sha=hashlib.sha256(raw).hexdigest()
    document=fitz.open(stream=raw,filetype='pdf')
    try:
        if document.is_encrypted or not 0<len(document)<=MAX_PAGES:raise ValueError('PDF extent/encryption unsupported')
        output.mkdir(parents=True,exist_ok=True)
        report=dict(schema='ENGINEER_OS_PDF_VISUAL_INVENTORY_V1',source_sha256=sha,source_bytes=len(raw),
            page_count=len(document),renderer='PyMuPDF '+fitz.VersionBind,render_long_side=1200,
            audit_implementation_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            scope='SOURCE_RENDER_AND_UNVERIFIED_TEXT_CANDIDATES',status='RECORDED_UNVERIFIED',
            render_cycle_complete=False,content_completeness_verified=False,tables_verified=False,
            formulas_verified=False,graphics_semantics_verified=False,acceptance_granted=False,
            native_text_missing_pages=[],ocr_requested=bool(ocr_gaps),pages=[],errors=[])
        def save():
            temporary=output/'manifest.json.tmp'
            temporary.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
            temporary.replace(output/'manifest.json')
        save()
        reader=None
        if ocr_gaps:
            from engineering.local_app.ocr import TesseractOCR,identity
            report['ocr_identity']=identity()
            try:reader=TesseractOCR()
            except ValueError:report['errors'].append('OCR_ENGINE_OR_LANGUAGE_MODELS_UNAVAILABLE')
        for number,page in enumerate(document,1):
            record=dict(page=number,source_sha256=sha,render_status='NOT_RUN',ocr_status='NOT_RUN',
                        content_verified=False,table_structure_verified=False)
            try:
                box=list(page.rect)
                if any(not math.isfinite(v) for v in box) or page.rect.width<=0 or page.rect.height<=0:
                    raise ValueError('Invalid page geometry')
                record['page_bbox']=box;scale=1200/max(page.rect.width,page.rect.height)
                pix=page.get_pixmap(matrix=fitz.Matrix(scale,scale),colorspace=fitz.csRGB,alpha=False)
                if pix.width*pix.height>1500000:raise ValueError('Render pixel limit')
                png=pix.tobytes('png');name=f'page-{number:05d}.png';(output/name).write_bytes(png)
                text=page.get_text();record.update(render_status='COMPLETED',render_file=name,
                    render_size=[pix.width,pix.height],render_sha256=hashlib.sha256(png).hexdigest(),
                    native_chars=len(text),native_text_sha256=hashlib.sha256(text.encode()).hexdigest())
                if not text.strip():
                    report['native_text_missing_pages'].append(number)
                    if ocr_gaps and reader is not None:
                        try:
                            blocks=reader.page_blocks(page,number)
                            detail=dict(page=number,source_sha256=sha,scope='UNVERIFIED_OCR_CANDIDATES',
                                        blocks=blocks,dossier=reader.last_page_dossier,acceptance_granted=False)
                            detail_raw=json.dumps(detail,ensure_ascii=False,indent=2).encode()
                            detail_name=f'page-{number:05d}-ocr.json';(output/detail_name).write_bytes(detail_raw)
                            record.update(ocr_status='CANDIDATES_RECORDED',ocr_chars=sum(len(b['text']) for b in blocks),
                                ocr_blocks=len(blocks),ocr_low_confidence_blocks=sum(b['ocr_confidence']<60 for b in blocks),
                                ocr_file=detail_name,ocr_sha256=hashlib.sha256(detail_raw).hexdigest())
                        except ValueError:
                            record['ocr_status']='FAILED';report['errors'].append('OCR_PAGE_FAILED:'+str(number))
                    elif ocr_gaps:record['ocr_status']='UNAVAILABLE'
            except Exception:
                record['render_status']='FAILED';report['errors'].append('PAGE_AUDIT_FAILED:'+str(number))
            report['pages'].append(record)
            if number%10==0:save()
        report['render_cycle_complete']=all(p['render_status']=='COMPLETED' for p in report['pages'])
        try:
            with source.open('rb') as stream:final_sha=hashlib.file_digest(stream,'sha256').hexdigest()
            if final_sha!=sha:
                report['errors'].append('SOURCE_IDENTITY_CHANGED');report['render_cycle_complete']=False
        except OSError:
            report['errors'].append('SOURCE_IDENTITY_UNAVAILABLE');report['render_cycle_complete']=False
        save();return report
    finally:document.close()


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('source',type=Path);parser.add_argument('output',type=Path)
    parser.add_argument('--ocr-native-gaps',action='store_true');args=parser.parse_args()
    result=audit(args.source,args.output,ocr_gaps=args.ocr_native_gaps)
    print(json.dumps({k:v for k,v in result.items() if k not in {'pages','ocr_identity'}},ensure_ascii=False))
    return 1 if result['errors'] else 0


if __name__=='__main__':raise SystemExit(main())

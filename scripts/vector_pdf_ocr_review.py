"""Produce source-bound, UNVERIFIED OCR candidates from vector-only PDF sheets.

Requires local pytesseract/Tesseract; no network or paid API.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
from engineering.document_intelligence.vector_ocr_review_routing import route_candidates


def collect(source, pages, dpi=90, min_confidence=35, languages='Cyrillic+eng'):
    import fitz
    import pytesseract
    from PIL import Image
    if dpi<50 or dpi>150:
        raise ValueError('DPI out of bounded range')
    source=Path(source)
    with source.open('rb') as stream:
        digest=hashlib.file_digest(stream,'sha256').hexdigest()
    pdf=fitz.open(source)
    try:
        records=[]
        for number in pages:
            if number<1 or number>len(pdf):
                raise ValueError('Invalid page number')
            page=pdf[number-1]
            if page.get_text('text').strip() or page.get_images(full=True):
                raise ValueError('Expected vector-only page without native text/raster references')
            paths=len(page.get_cdrawings())
            if paths==0:
                raise ValueError('No PDF vector paths found')
            # Use bounded tiles: large engineering sheets make full-page PSM11 stall.
            bounds=page.rect
            tiles=[]
            for row in range(2):
                for col in range(2):
                    tiles.append(fitz.Rect(bounds.x0+col*bounds.width/2,
                                           bounds.y0+row*bounds.height/2,
                                           bounds.x0+(col+1)*bounds.width/2,
                                           bounds.y0+(row+1)*bounds.height/2))
            items=[]
            failures=[]
            rendered=[]
            for tile_index,clip in enumerate(tiles):
                pix=page.get_pixmap(matrix=fitz.Matrix(dpi/72,dpi/72),clip=clip,alpha=False)
                if pix.width*pix.height>4000000:
                    failures.append(dict(tile=tile_index,reason='OCR_PIXEL_BUDGET'))
                    continue
                rendered.append([pix.width,pix.height])
                image=Image.open(io.BytesIO(pix.tobytes('png')))
                try:
                    data=pytesseract.image_to_data(image,lang=languages,config='--psm 11',
                                                   output_type=pytesseract.Output.DICT,timeout=12)
                except RuntimeError:
                    # Retry only the failed tile as four smaller crops. Never
                    # certify a tile if even one subtile still fails.
                    recovery_errors=[]
                    recovery_count=0
                    for subrow in range(2):
                        for subcol in range(2):
                            subclip=fitz.Rect(
                                clip.x0+subcol*clip.width/2,
                                clip.y0+subrow*clip.height/2,
                                clip.x0+(subcol+1)*clip.width/2,
                                clip.y0+(subrow+1)*clip.height/2)
                            reduced_dpi=min(dpi,45)
                            try:
                                subpix=page.get_pixmap(matrix=fitz.Matrix(reduced_dpi/72,reduced_dpi/72),
                                                       clip=subclip,alpha=False)
                                subimage=Image.open(io.BytesIO(subpix.tobytes('png')))
                                subdata=pytesseract.image_to_data(
                                    subimage,lang=languages,config='--psm 6',
                                    output_type=pytesseract.Output.DICT,timeout=4)
                            except RuntimeError:
                                recovery_errors.append([subrow,subcol])
                                continue
                            for j,raw_sub in enumerate(subdata['text']):
                                subword=(raw_sub or '').strip()
                                try:
                                    conf=float(subdata['conf'][j])
                                except (ValueError,TypeError):
                                    continue
                                if not subword or conf<min_confidence:
                                    continue
                                x=int(subdata['left'][j]); y=int(subdata['top'][j])
                                w=int(subdata['width'][j]); h=int(subdata['height'][j])
                                items.append(dict(text=subword,confidence=conf,tile=tile_index,
                                    fallback_subtile=[subrow,subcol],
                                    bbox_pdf=[round(subclip.x0+x*72/reduced_dpi,2),
                                              round(subclip.y0+y*72/reduced_dpi,2),
                                              round(subclip.x0+(x+w)*72/reduced_dpi,2),
                                              round(subclip.y0+(y+h)*72/reduced_dpi,2)],
                                    status='OCR_CANDIDATE_UNVERIFIED'))
                                recovery_count+=1
                    if recovery_errors:
                        failures.append(dict(tile=tile_index,reason='FALLBACK_SUBTILES_FAILED',
                                             failed_subtiles=recovery_errors,
                                             recovered_candidates=recovery_count))
                    continue
                for idx,raw in enumerate(data['text']):
                    value=(raw or '').strip()
                    try:
                        confidence=float(data['conf'][idx])
                    except (ValueError,TypeError):
                        continue
                    if not value or confidence<min_confidence:
                        continue
                    x=int(data['left'][idx]); y=int(data['top'][idx])
                    w=int(data['width'][idx]); h=int(data['height'][idx])
                    # Absolute PDF coordinates survive tile-based processing.
                    bbox_pdf=[round(clip.x0+x*72/dpi,2),round(clip.y0+y*72/dpi,2),
                              round(clip.x0+(x+w)*72/dpi,2),round(clip.y0+(y+h)*72/dpi,2)]
                    items.append(dict(text=value,confidence=confidence,tile=tile_index,
                                      bbox_pdf=bbox_pdf,status='OCR_CANDIDATE_UNVERIFIED'))
            items,review_counts=route_candidates(items)
            records.append(dict(page=number,vector_paths=paths,
                                rendered_tile_pixels=rendered,ocr_failures=failures,
                                candidates=items,review_route_counts=review_counts,visual_verified=False,
                                native_text_available=False))
        with source.open('rb') as stream:
            if hashlib.file_digest(stream,'sha256').hexdigest()!=digest:
                raise ValueError('PDF changed during OCR')
        return dict(schema='ENGINEER_OS_VECTOR_OCR_CANDIDATES_V1',source_sha256=digest,
                    source_pages=len(pdf),dpi=dpi,languages=languages,
                    quality_status='VISUAL_REVIEW_REQUIRED',records=records)
    finally:
        pdf.close()


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('source',type=Path)
    parser.add_argument('output',type=Path)
    parser.add_argument('--page',type=int,action='append',required=True)
    parser.add_argument('--dpi',type=int,default=90)
    args=parser.parse_args()
    args.output.write_text(json.dumps(collect(args.source,args.page,args.dpi),
                                      ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

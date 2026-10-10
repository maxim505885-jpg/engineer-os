"""Produce source-bound, UNVERIFIED OCR candidates from vector-only PDF sheets.

Requires local pytesseract/Tesseract; no network or paid API.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path


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
            pix=page.get_pixmap(matrix=fitz.Matrix(dpi/72,dpi/72),alpha=False)
            if pix.width*pix.height>12000000:
                raise ValueError('Rendered page exceeds OCR pixel budget')
            image=Image.open(io.BytesIO(pix.tobytes('png')))
            data=pytesseract.image_to_data(image,lang=languages,config='--psm 11',
                                           output_type=pytesseract.Output.DICT,timeout=45)
            items=[]
            for idx,raw in enumerate(data['text']):
                value=(raw or '').strip()
                try:
                    confidence=float(data['conf'][idx])
                except (ValueError,TypeError):
                    continue
                if not value or confidence<min_confidence:
                    continue
                items.append(dict(text=value,confidence=confidence,
                                  bbox_pixels=[int(data[k][idx]) for k in ('left','top','width','height')],
                                  status='OCR_CANDIDATE_UNVERIFIED'))
            records.append(dict(page=number,vector_paths=paths,
                                rendered_pixels=[pix.width,pix.height],
                                candidates=items,visual_verified=False,
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

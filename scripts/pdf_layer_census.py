"""Full PDF page-layer census: coverage, NOT content or OCR qualification."""
import argparse
import hashlib
import json
from pathlib import Path

def inventory(source):
    import fitz
    source=Path(source)
    with source.open('rb') as stream:
        digest=hashlib.file_digest(stream,'sha256').hexdigest()
    doc=fitz.open(source)
    try:
        rows=[]
        for index,page in enumerate(doc):
            native=page.get_text('text')
            image_refs=page.get_images(full=True)
            rows.append(dict(page=index+1,native_text_chars=len(native.strip()),
                             native_text_sha256=hashlib.sha256(native.encode()).hexdigest(),
                             embedded_image_refs=len(image_refs),
                             requires_ocr_review=not bool(native.strip()),
                             requires_image_review=bool(image_refs)))
        with source.open('rb') as stream:
            if hashlib.file_digest(stream,'sha256').hexdigest()!=digest:
                raise ValueError('PDF source changed during census')
        return dict(schema='ENGINEER_OS_PDF_LAYER_INVENTORY_V1',sha256=digest,
                    size_bytes=source.stat().st_size,page_count=len(doc),
                    native_empty_pages=[r['page'] for r in rows if r['requires_ocr_review']],
                    pages_with_embedded_images=sum(r['embedded_image_refs']>0 for r in rows),
                    visual_content_verified=False,pages=rows)
    finally:
        doc.close()

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('source',type=Path)
    parser.add_argument('output',type=Path)
    args=parser.parse_args()
    args.output.write_text(json.dumps(inventory(args.source),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

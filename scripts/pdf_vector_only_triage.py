"""Identify vector-only PDF pages: source structure is not semantic verification."""
import argparse
import hashlib
import json
from pathlib import Path


def triage(source, first=1, last=None):
    import fitz
    source=Path(source)
    with source.open('rb') as stream:
        sha=hashlib.file_digest(stream,'sha256').hexdigest()
    document=fitz.open(source)
    try:
        stop=len(document) if last is None else last
        if first<1 or stop<first or stop>len(document):
            raise ValueError('Invalid inclusive page range')
        rows=[]
        for page_number in range(first,stop+1):
            page=document[page_number-1]
            chars=len(page.get_text('text').strip())
            raster=len(page.get_images(full=True))
            # C drawings return native PDF vector paths without unnecessary coordinate conversions.
            vectors=len(page.get_cdrawings()) if not chars else None
            rows.append(dict(page=page_number,native_text_chars=chars,
                             embedded_image_references=raster,vector_paths=vectors,
                             vector_only_no_native_text=bool(not chars and not raster and vectors),
                             semantic_content_verified=False))
        return dict(schema='ENGINEER_OS_VECTOR_ONLY_PDF_TRIAGE_V1',source_sha256=sha,
                    source_size=source.stat().st_size,pdf_pages=len(document),
                    start_page=first,end_page=stop,rows=rows,
                    vector_only_pages=[r['page'] for r in rows if r['vector_only_no_native_text']],
                    visual_ocr_and_drawing_semantics_verified=False)
    finally:
        document.close()


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('source',type=Path)
    parser.add_argument('output',type=Path)
    parser.add_argument('--first',type=int,default=1)
    parser.add_argument('--last',type=int)
    args=parser.parse_args()
    args.output.write_text(json.dumps(triage(args.source,args.first,args.last),
                                      indent=2,ensure_ascii=False)+'\n',encoding='utf8')

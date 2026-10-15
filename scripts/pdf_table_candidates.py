"""Source-bound PDF table candidates; frames are not certified table cells."""
import argparse
import hashlib
import json
from pathlib import Path


def classify(table, page_rect):
    x0,y0,x1,y1=table.bbox
    area=(x1-x0)*(y1-y0)
    page_area=page_rect.width*page_rect.height
    coverage=area/page_area if page_area>0 else 0
    # Large CAD-style sheet frames must remain review candidates, not tables.
    reasons=[]
    if coverage>=.7 and table.col_count>=6:
        reasons.append('PAGE_FRAME_OR_TITLE_BLOCK_CANDIDATE')
    cells=table.extract()
    filled=sum(bool(isinstance(value,str) and value.strip()) for row in cells for value in row)
    return dict(bbox=[round(float(v),3) for v in table.bbox],
                rows=table.row_count,columns=table.col_count,
                nonempty_cells=filled,extent_ratio=round(coverage,5),
                review_status='FRAME_SUSPECT_REVIEW_REQUIRED' if reasons else 'TABLE_CANDIDATE_UNVERIFIED',
                reasons=reasons,content_verified=False,cell_geometry_verified=False,
                extracted_cells=cells)


def audit(source,output,pages):
    import fitz
    source=Path(source)
    if not source.is_file() or source.suffix.lower()!='.pdf':
        raise ValueError('Original PDF required')
    digest=hashlib.file_digest(source.open('rb'),'sha256').hexdigest()
    document=fitz.open(source)
    try:
        output_record=dict(schema='ENGINEER_OS_PDF_TABLE_CANDIDATES_V1',
                           source_sha256=digest,source_size=source.stat().st_size,
                           page_count=len(document),qualified_verified=False,
                           pages=[])
        for page_number in pages:
            if page_number<1 or page_number>len(document):
                raise ValueError('Page outside source')
            page=document[page_number-1]
            candidates=[classify(table,page.rect) for table in page.find_tables().tables]
            output_record['pages'].append(dict(page=page_number,candidates=candidates,
                                               count=len(candidates),qualified_verified=False))
        with source.open('rb') as stream:
            if hashlib.file_digest(stream,'sha256').hexdigest()!=digest:
                raise ValueError('Source changed during audit')
        Path(output).write_text(json.dumps(output_record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        return output_record
    finally:
        document.close()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source',type=Path)
    parser.add_argument('output',type=Path)
    parser.add_argument('--page',type=int,action='append',required=True)
    args=parser.parse_args()
    audit(args.source,args.output,args.page)


if __name__=='__main__':
    main()

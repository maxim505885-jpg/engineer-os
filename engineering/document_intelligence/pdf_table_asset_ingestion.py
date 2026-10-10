"""PDF table-cell candidates with exact content hashes and page coordinates.

PyMuPDF table detection may include page frames; nothing is auto-verified.
"""
import hashlib
import json
from pathlib import Path
from .asset_provenance import DocumentAssetEvidence


def pdf_table_candidates(pdf_path, page_numbers):
    import fitz
    path=Path(pdf_path)
    with path.open('rb') as f:
        source_hash=hashlib.file_digest(f,'sha256').hexdigest()
    results=[]
    with fitz.open(path) as pdf:
        for page_number in page_numbers:
            if not 1<=page_number<=len(pdf):
                raise ValueError('INVALID_PAGE_NUMBER')
            page=pdf[page_number-1]
            for index,table in enumerate(page.find_tables().tables):
                cells=table.extract()
                payload=json.dumps(cells,ensure_ascii=False,separators=(',',':')).encode('utf-8')
                bbox=','.join(f'{v:.3f}' for v in table.bbox)
                item=DocumentAssetEvidence(
                    source_sha256=source_hash,
                    asset_sha256=hashlib.sha256(payload).hexdigest(),
                    asset_kind='table_cells',
                    location=f'pdf:page={page_number}:candidate={index}:bbox={bbox}',
                    page_number=page_number)
                results.append((item,payload))
    return tuple(results)

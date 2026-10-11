"""PDF table-cell candidates with exact content hashes and page coordinates.

PyMuPDF table detection may include page frames; nothing is auto-verified.
"""
import hashlib
import json
import math
from pathlib import Path
from .asset_provenance import DocumentAssetEvidence


def _rectangle(value):
    if value is None:
        return None
    result=list(value)
    if (len(result)!=4 or any(not math.isfinite(v) for v in result)
            or result[0]>=result[2] or result[1]>=result[3]):
        raise ValueError('INVALID_TABLE_CELL_GEOMETRY')
    return result


def _table_payload(table, page, original_rotation, original_rect):
    """Retain detector output; null slots do not prove a merged-cell relation."""
    values=table.extract()
    rows=table.rows
    if len(values)!=table.row_count or len(rows)!=table.row_count:
        raise ValueError('TABLE_CELL_MAPPING_MISMATCH')
    cells=[]
    for row_index,(texts,row) in enumerate(zip(values,rows),1):
        if len(texts)!=table.col_count or len(row.cells)!=table.col_count:
            raise ValueError('TABLE_CELL_MAPPING_MISMATCH')
        for column,(text,rect) in enumerate(zip(texts,row.cells),1):
            cells.append(dict(row=row_index,column=column,bbox=_rectangle(rect),text=text,
                geometry_status='UNRESOLVED_SLOT' if rect is None else 'DETECTED_UNVERIFIED'))
    limitations=['TABLE_DETECTION_UNVERIFIED','NATIVE_TEXT_ONLY_RASTER_CONTENT_NOT_READ']
    if any(c['bbox'] is None for c in cells):
        limitations.append('MERGED_OR_MISSING_CELL_RELATION_UNVERIFIED')
    header=table.header
    data=dict(schema='ENGINEER_OS_PDF_TABLE_CELLS_V2',values=values,cells=cells,
        row_count=table.row_count,column_count=table.col_count,bbox=_rectangle(table.bbox),
        coordinate_system='PYMUPDF_UNROTATED_PAGE_TOPLEFT_POINTS',page_rotation=original_rotation,
        page_rect=original_rect,page_cropbox=list(page.cropbox),
        header=dict(external=header.external,bbox=_rectangle(header.bbox),
                    names=header.names,cells=[_rectangle(c) for c in header.cells]),
        content_verified=False,limitations=limitations)
    return json.dumps(data,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode('utf-8')


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
            rotation,rect=page.rotation,list(page.rect)
            # find_tables otherwise rotates content into display space. Normalize
            # only this in-memory page, keeping the immutable original untouched.
            page.set_rotation(0)
            try:
                for index,table in enumerate(page.find_tables().tables):
                    payload=_table_payload(table,page,rotation,rect)
                    bbox=','.join(f'{v:.3f}' for v in table.bbox)
                    item=DocumentAssetEvidence(
                        source_sha256=source_hash,
                        asset_sha256=hashlib.sha256(payload).hexdigest(),
                        asset_kind='table_cells',
                        location=f'pdf:page={page_number}:candidate={index}:bbox={bbox}',
                        page_number=page_number)
                    results.append((item,payload))
            finally:
                page.set_rotation(rotation)
    with path.open('rb') as f:
        if hashlib.file_digest(f,'sha256').hexdigest()!=source_hash:
            raise ValueError('SOURCE_IDENTITY_CHANGED_DURING_EXTRACTION')
    return tuple(results)

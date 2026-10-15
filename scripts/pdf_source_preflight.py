"""Inventory PDF source quality before OCR; no extraction or evidence acceptance."""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
from pathlib import Path


def inspect_source(source: Path, *, expected_sha256: str | None = None,
                   pages: list[int] | None = None) -> dict:
    source = Path(source)
    with source.open('rb') as handle:
        sha = hashlib.file_digest(handle, 'sha256').hexdigest()
    if expected_sha256 is not None and sha != expected_sha256.lower():
        raise ValueError('source checksum mismatch')
    import fitz
    results = []
    with fitz.open(source) as pdf:
        selected = list(range(1, len(pdf) + 1)) if pages is None else pages
        if (not selected or any(type(p) is not int or not 1 <= p <= len(pdf) for p in selected)
                or len(set(selected)) != len(selected)):
            raise ValueError('invalid source pages')
        for number in selected:
            page = pdf[number - 1]
            # Text, image and drawing geometry is unrotated in PyMuPDF.
            rect = page.rect * page.derotation_matrix
            # This window is only a routing heuristic: margins remain unverified.
            body = fitz.Rect(rect.width * .06, rect.height * .02,
                             rect.width, rect.height * .90)
            words = page.get_text('words')
            body_words = sum(body.contains(fitz.Point((w[0]+w[2])/2, (w[1]+w[3])/2))
                             for w in words)
            images = []
            for item in page.get_image_info():
                box = fitz.Rect(item['bbox'])
                if box.is_empty or box.is_infinite:
                    continue
                # All images are inventoried, even when too small to affect routing.
                significant = (box & body).get_area() >= body.get_area() * .10
                transform = item['transform']
                width_pt = (transform[0]**2 + transform[1]**2)**.5
                height_pt = (transform[2]**2 + transform[3]**2)**.5
                dpi_x = item['width'] * 72 / width_pt if width_pt else None
                dpi_y = item['height'] * 72 / height_pt if height_pt else None
                low = significant and (dpi_x is None or dpi_y is None or min(dpi_x, dpi_y) < 120)
                images.append(dict(bbox=list(box),width_px=item['width'],height_px=item['height'],
                                   dpi_x=dpi_x,dpi_y=dpi_y,significant_body_image=significant,
                                   low_resolution_warning=low))
            major = any(i['significant_body_image'] for i in images)
            drawings = len(page.get_drawings()) if not body_words and not major else None
            if major:
                kind = 'MIXED_TEXT_AND_RASTER' if body_words else 'RASTER'
                route = 'REGIONAL_OCR_AND_VISUAL_REVIEW'
            elif body_words:
                kind, route = 'NATIVE_TEXT', 'NATIVE_TEXT_AND_TABLE_REVIEW'
            elif drawings:
                kind, route = 'VECTOR_WITHOUT_NATIVE_TEXT', 'VECTOR_VISUAL_REVIEW'
            elif images:
                kind, route = 'IMAGE_CONTENT', 'REGIONAL_OCR_AND_VISUAL_REVIEW'
            else:
                kind, route = 'NO_CONTENT_DETECTED', 'VISUAL_REVIEW_REQUIRED'
            results.append(dict(source_page=number,source_sha256=sha,source_kind=kind,
                                recommended_route=route,native_words=len(words),
                                native_body_words=body_words,body_window=list(body),
                                coordinate_origin='TOPLEFT_UNROTATED',
                                body_window_is_heuristic=True,images=images,vector_paths=drawings,
                                low_resolution_images=sum(i['low_resolution_warning'] for i in images),
                                complete_page=False,acceptance_granted=False))
        page_count = len(pdf)
    with source.open('rb') as handle:
        if hashlib.file_digest(handle, 'sha256').hexdigest() != sha:
            raise ValueError('source changed during inspection')
    return dict(source_sha256=sha,page_count=page_count,inspected_pages=len(results),
                status='UNCERTAINTY',document_status='BLOCK',evidentiary_status='NOT_EVIDENCE',
                complete_document=False,acceptance_granted=False,low_resolution_warning_dpi=120,
                scope='Source routing and image-resolution heuristics only. No text, table, '
                      'blank-page, visual legibility or engineering acceptance.',
                source_kinds=dict(collections.Counter(p['source_kind'] for p in results)),pages=results)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--sha256')
    parser.add_argument('--pages', type=int, nargs='+', help='Original 1-based PDF page numbers')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if (args.output.resolve() == args.source.resolve() or
            (args.output.exists() and args.source.exists() and args.output.samefile(args.source))):
        parser.error('output must not overwrite source')
    try:
        result = inspect_source(args.source, expected_sha256=args.sha256, pages=args.pages)
    except (ImportError, OSError, ValueError, RuntimeError) as exc:
        result = dict(status='BLOCK',document_status='BLOCK',acceptance_granted=False,
                      complete_document=False,pages=[],reason=str(exc))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2), encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k != 'pages'},ensure_ascii=False))
    return 2 if result['status'] == 'BLOCK' else 0


if __name__ == '__main__':
    raise SystemExit(main())

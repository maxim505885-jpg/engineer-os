"""Read a selected PDF region locally; output is never accepted engineering evidence.

Run with python -m scripts.local_ocr_region SOURCE --page N --bbox L T R B
--sha256 EXPECTED --output NEW_JSON. Coordinates are unrotated crop-relative points.
"""
import argparse
import hashlib
import json
from pathlib import Path
import fitz
from engineering.local_app.ocr import TesseractOCR,identity


def recognize_region(source,page_no,bbox,expected_sha):
    source=Path(source)
    # Open the exact hashed bytes, rather than a path which could change mid-read.
    raw=source.read_bytes();sha=hashlib.sha256(raw).hexdigest()
    if sha!=expected_sha:raise ValueError('SOURCE_SHA256_MISMATCH')
    if isinstance(page_no,bool) or not isinstance(page_no,int) or page_no<1:raise ValueError('INVALID_PAGE')
    engine_identity=identity();engine_identity.update(layout='selected_region',render_scale=6.0,psm=6)
    parser=TesseractOCR()
    with fitz.open(stream=raw,filetype='pdf') as document:
        if page_no>len(document):raise ValueError('INVALID_PAGE')
        blocks=parser.page_blocks(document[page_no-1],page_no,bbox=bbox)
    if hashlib.sha256(source.read_bytes()).hexdigest()!=sha:raise ValueError('SOURCE_CHANGED')
    return dict(scope='SELECTED_REGION_OCR_UNVERIFIED',source_sha256=sha,page_no=page_no,
        source_bbox=bbox,engine_identity=engine_identity,ocr_dossier=parser.last_page_dossier,
        blocks=blocks,page_complete=False,document_complete=False,quality_verified=False,
        acceptance_granted=False,limitations=['OCR_CANDIDATES_REQUIRE_SOURCE_REVIEW','SELECTED_REGION_ONLY'])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source',type=Path);parser.add_argument('--page',type=int,required=True)
    parser.add_argument('--bbox',type=float,nargs=4,required=True)
    parser.add_argument('--sha256',required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists() or args.output.is_symlink():raise ValueError('OUTPUT_ALREADY_EXISTS')
    result=recognize_region(args.source,args.page,args.bbox,args.sha256)
    # Exclusive creation also protects against aliases/races after the preflight.
    with args.output.open('x',encoding='utf-8') as stream:json.dump(result,stream,ensure_ascii=False,indent=2)


if __name__=='__main__':main()

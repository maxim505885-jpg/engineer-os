"""Bounded local PDF region readback. Every returned item is an unverified candidate.

Coordinates are PDF points relative to the unrotated CropBox. No file is written,
no selection is expanded and neither OCR agreement nor native text grants acceptance.
"""
import base64
import hashlib
import json
import math
import os
from pathlib import Path
import re
import stat
import time
import unicodedata

import fitz
from .ocr import TesseractOCR, identity

MAX_SOURCE_BYTES=128*1024*1024
MAX_PAGES=5000
MAX_PIXELS=9000000
MAX_WORDS=20000
MAX_CONFLICT_PAIRS=500000
MAX_OUTPUT_BYTES=4*1024*1024
MAX_PNG_BYTES=2*1024*1024
TIMEOUT=90
COORDINATE_SPACE='UNROTATED_CROP_RELATIVE'


class RegionReadbackError(ValueError):
    """Stable readback rejection; no partial success is returned."""


def _check_deadline(deadline):
    if time.monotonic()>=deadline:raise RegionReadbackError('REGION_TIMEOUT')


def _snapshot(source,deadline):
    path=Path(source).absolute()
    if any(part.is_symlink() for part in (path,*path.parents)):
        raise RegionReadbackError('UNSAFE_SOURCE')
    try:
        descriptor=os.open(path,os.O_RDONLY|getattr(os,'O_NOFOLLOW',0)|getattr(os,'O_NONBLOCK',0))
        with os.fdopen(descriptor,'rb') as stream:
            info=os.fstat(stream.fileno())
            if not stat.S_ISREG(info.st_mode):raise RegionReadbackError('UNSAFE_SOURCE')
            if not 0<info.st_size<=MAX_SOURCE_BYTES:raise RegionReadbackError('SOURCE_SIZE_LIMIT')
            chunks=[];size=0
            while True:
                _check_deadline(deadline)
                chunk=stream.read(min(1024*1024,MAX_SOURCE_BYTES-size+1))
                if not chunk:break
                size+=len(chunk)
                if size>MAX_SOURCE_BYTES:raise RegionReadbackError('SOURCE_SIZE_LIMIT')
                chunks.append(chunk)
            after=os.fstat(stream.fileno())
        if _file_identity(info)!=_file_identity(after):raise RegionReadbackError('SOURCE_CHANGED')
        raw=b''.join(chunks)
        return raw,hashlib.sha256(raw).hexdigest(),_file_identity(info)
    except OSError as exc:raise RegionReadbackError('UNSAFE_SOURCE') from exc


def _file_identity(info):
    return (info.st_dev,info.st_ino,info.st_size,info.st_mtime_ns,info.st_ctime_ns)


def _box(rect):
    return dict(zip(('left','top','right','bottom'),list(rect)))


def _rect(box):
    return fitz.Rect([box[key] for key in ('left','top','right','bottom')])


def _render(page,clip,deadline):
    scale=min(6.0,3000/max(clip.width,clip.height))
    if (math.ceil(clip.width*scale)+2)*(math.ceil(clip.height*scale)+2)>MAX_PIXELS:
        raise RegionReadbackError('REGION_PIXEL_LIMIT')
    _check_deadline(deadline)
    pixels=page.get_pixmap(matrix=fitz.Matrix(scale,scale),clip=clip,colorspace=fitz.csRGB,alpha=False)
    if pixels.width*pixels.height>MAX_PIXELS:raise RegionReadbackError('REGION_PIXEL_LIMIT')
    png=pixels.tobytes('png')
    if len(png)>MAX_PNG_BYTES:raise RegionReadbackError('REGION_OUTPUT_LIMIT')
    _check_deadline(deadline)
    return dict(png_base64=base64.b64encode(png).decode('ascii'),png_sha256=hashlib.sha256(png).hexdigest(),
        width=pixels.width,height=pixels.height,scale=scale,pixel_origin=[pixels.x,pixels.y],
        source_bbox=list(clip),coordinate_space=COORDINATE_SPACE,colorspace='RGB',
        purpose='SOURCE_REGION_REVIEW_RENDER',ocr_input_equivalence='NOT_ASSERTED')


def _native(page,clip,page_no,deadline):
    words=[];groups={};boundary=0
    # Crop before native extraction; fully contained words only. Do not include
    # neighbouring page blocks merely because a block intersects the selection.
    for entry in page.get_text('words',clip=clip,sort=True):
        _check_deadline(deadline)
        if len(words)>=MAX_WORDS:raise RegionReadbackError('REGION_WORD_LIMIT')
        rect=fitz.Rect(entry[:4])
        if not all(math.isfinite(n) for n in rect):raise RegionReadbackError('INVALID_NATIVE_GEOMETRY')
        if not clip.contains(rect):boundary+=1;continue
        word=dict(text=entry[4],bbox=_box(rect),block_no=entry[5],line_no=entry[6],word_no=entry[7])
        words.append(word)
        groups.setdefault((entry[5],entry[6]),[]).append(word)
    blocks=[]
    for index,group in enumerate(groups.values(),1):
        rect=_rect(group[0]['bbox'])
        for word in group[1:]:rect|=_rect(word['bbox'])
        blocks.append(dict(block_id=f'native:page:{page_no}:line:{index}',kind='native_text',
            text=' '.join(word['text'] for word in group),provenance=[dict(page_no=page_no,bbox=_box(rect))],
            scope='UNVERIFIED_NATIVE_CANDIDATE'))
    return words,blocks,boundary


def _normalize(text):
    return re.sub(r'\s+',' ',unicodedata.normalize('NFKC',text)).strip().casefold()


def _conflicts(native,recognized,deadline):
    conflicts=[];comparisons=0
    for first in native:
        rect=_rect(first['provenance'][0]['bbox'])
        overlapping=[]
        for other in recognized:
            comparisons+=1
            if comparisons>MAX_CONFLICT_PAIRS:raise RegionReadbackError('REGION_CONFLICT_LIMIT')
            _check_deadline(deadline)
            if rect.intersects(_rect(other['provenance'][0]['bbox'])):overlapping.append(other)
        if not overlapping:continue
        text=' '.join(other['text'] for other in overlapping)
        if _normalize(first['text'])!=_normalize(text):
            conflicts.append(dict(kind='NATIVE_OCR_CONFLICT_CANDIDATE',native_block_id=first['block_id'],
                ocr_block_ids=[other['block_id'] for other in overlapping],native_text=first['text'],ocr_text=text,
                native_normalized=_normalize(first['text']),ocr_normalized=_normalize(text),
                acceptance_granted=False,resolution='SOURCE_REVIEW_REQUIRED'))
    return conflicts


def recognize(source_path,page_no,bbox,expected_sha,ocr_enabled=False,ocr_psm=6):
    """Read a 1-based source PDF page selection, preserving exact source bytes.

    Return JSON-compatible native/render/OCR candidates. Raise RegionReadbackError
    on invalid, stale, changed, oversized or timed-out input; never return a partial
    successful result. A checked deadline bounds progress; parsing/render calls are
    native library calls and require process isolation for a hard wall-clock kill.
    """
    deadline=time.monotonic()+TIMEOUT
    if type(ocr_psm)!=int or ocr_psm not in (6,11):raise RegionReadbackError('INVALID_OCR_PROFILE')
    if isinstance(page_no,bool) or not isinstance(page_no,int) or page_no<1:raise RegionReadbackError('INVALID_PAGE')
    if type(ocr_enabled) is not bool:raise RegionReadbackError('INVALID_OCR_FLAG')
    if not isinstance(expected_sha,str) or re.fullmatch(r'[0-9a-fA-F]{64}',expected_sha) is None:
        raise RegionReadbackError('INVALID_SOURCE_SHA256')
    if not isinstance(bbox,(list,tuple)) or len(bbox)!=4 or any(isinstance(n,bool) or not isinstance(n,(int,float)) or not math.isfinite(n) for n in bbox):
        raise RegionReadbackError('INVALID_REGION')
    selected=list(bbox)
    raw,sha,source_identity=_snapshot(source_path,deadline)
    if sha!=expected_sha.lower():raise RegionReadbackError('SOURCE_SHA256_MISMATCH')
    try:document=fitz.open(stream=raw,filetype='pdf')
    except (RuntimeError,ValueError) as exc:raise RegionReadbackError('INVALID_PDF') from exc
    with document:
        if document.needs_pass:raise RegionReadbackError('PDF_PASSWORD_REQUIRED')
        if len(document)>MAX_PAGES:raise RegionReadbackError('PAGE_COUNT_LIMIT')
        if page_no>len(document):raise RegionReadbackError('INVALID_PAGE')
        page=document[page_no-1];rotation=page.rotation;cropbox=list(page.cropbox)
        page.set_rotation(0)
        width,height=page.rect.width,page.rect.height
        if not all(math.isfinite(n) and 0<n<=20000 for n in (width,height)):raise RegionReadbackError('INVALID_PAGE_GEOMETRY')
        left,top,right,bottom=selected
        if not (0<=left<right<=width and 0<=top<bottom<=height):raise RegionReadbackError('INVALID_REGION')
        clip=fitz.Rect(selected)
        words,native,boundary=_native(page,clip,page_no,deadline)
        rendered=_render(page,clip,deadline)
        rendered.update(source_sha256=sha,page_no=page_no)
        recognized=[];dossier=None;engine=None
        if ocr_enabled:
            _check_deadline(deadline)
            parser=TesseractOCR();recognized=parser.page_blocks(page,page_no,bbox=selected,selected_psm=ocr_psm)
            dossier=parser.last_page_dossier;engine=identity()
            engine.update(layout='selected_region',render_scale=rendered['scale'],psm=ocr_psm)
            # Raster rounding may add less than one pixel around the requested clip.
            # Retain original geometry explicitly rather than silently widening scope.
            for block in recognized:
                original=block['provenance'][0]['bbox'];rect=_rect(original)
                if not clip.contains(rect):
                    clipped=rect&clip
                    if clipped.is_empty:raise RegionReadbackError('OCR_OUTSIDE_REGION')
                    block['provenance'][0]['raster_bbox_before_selection_clip']=dict(original)
                    block['provenance'][0]['bbox']=_box(clipped)
                    block['selection_boundary_clipped']=True
            if len(words)+sum(b.get('ocr_word_count',0) for b in recognized)>MAX_WORDS:raise RegionReadbackError('REGION_WORD_LIMIT')
        result=dict(scope='SELECTED_REGION_READBACK_UNVERIFIED',source_sha256=sha,source_bytes=len(raw),
            page_no=page_no,source_bbox=selected,coordinate_space=COORDINATE_SPACE,
            source_page=dict(rotation=rotation,cropbox=cropbox,width=width,height=height),
            native_words=words,native_blocks=native,ocr_blocks=recognized,blocks=native+recognized,
            rendered_region=rendered,ocr_dossier=dossier,engine_identity=engine,conflicts=_conflicts(native,recognized,deadline),
            boundary_words_excluded=boundary,page_complete=False,document_complete=False,
            quality_verified=False,acceptance_granted=False,
            limitations=['SELECTED_REGION_ONLY','CANDIDATES_REQUIRE_SOURCE_REVIEW','BOUNDARY_TEXT_MAY_BE_INCOMPLETE',
                'NATIVE_RENDER_CALLS_REQUIRE_PROCESS_ISOLATION_FOR_HARD_DEADLINE'])
        _check_deadline(deadline)
        if len(json.dumps(result,ensure_ascii=False,allow_nan=False).encode('utf-8'))>MAX_OUTPUT_BYTES:
            raise RegionReadbackError('REGION_OUTPUT_LIMIT')
    post,post_sha,post_identity=_snapshot(source_path,deadline)
    if post_sha!=sha or post_identity!=source_identity or post!=raw:raise RegionReadbackError('SOURCE_CHANGED')
    _check_deadline(deadline)
    return result

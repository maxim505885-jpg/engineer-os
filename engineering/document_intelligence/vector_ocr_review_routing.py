"""Conservative OCR review routing. Never drop source candidates or mark them verified."""
import re
from collections import Counter

NOISE_PATTERN=re.compile(r'^[^\wА-Яа-яЁё]+$',re.UNICODE)
REPETITIVE=re.compile(r'^(.)\1{2,}$',re.UNICODE)


def route(token):
    word=str(token.get('text','')).strip()
    bbox=token.get('bbox_pdf') or []
    if len(bbox)!=4 or not all(isinstance(v,(int,float)) for v in bbox):
        return 'GEOMETRY_REVIEW_REQUIRED'
    width=bbox[2]-bbox[0]
    height=bbox[3]-bbox[1]
    if width<=0 or height<=0:
        return 'GEOMETRY_REVIEW_REQUIRED'
    if not word or NOISE_PATTERN.fullmatch(word) or REPETITIVE.fullmatch(word):
        return 'PROBABLE_GRAPHIC_NOISE'
    if height<2 or width/height>35:
        return 'PROBABLE_GRAPHIC_NOISE'
    if len(word)==1 and not word.isdigit():
        return 'AMBIGUOUS_SINGLE_GLYPH'
    return 'TEXT_CANDIDATE_VISUAL_REVIEW'


def route_candidates(candidates):
    routed=[dict(token,review_route=route(token),verified=False) for token in candidates]
    return routed,dict(Counter(token['review_route'] for token in routed))

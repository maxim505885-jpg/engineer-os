"""Partial native quote geometry and existing DI source-binding validation only."""
import hashlib
import math
from engineering.document_intelligence.contracts import BoundingBox,PageRef,DocumentBlock,NormalizedDocument
from engineering.document_intelligence.evidence_bridge import evidence_candidates
from engineering.document_intelligence.evidence_validation import validate_evidence_candidate


def unavailable(status='NOT_LOCATED'):
    return dict(status=status,regions=[],coordinate_system=None),dict(status='BLOCK',scope='SOURCE_BINDING_ONLY',candidate_id=None,reasons=['NO_UNAMBIGUOUS_PAGE_GEOMETRY'])


def locate(pdf_page,quote,text,sha256,file_id,page):
    occurrences=0;offset=0
    while True:
        found=text.find(quote,offset)
        if found<0:break
        occurrences+=1;offset=found+1
    rects=pdf_page.search_for(quote)
    regions=[dict(left=r.x0,top=r.y0,right=r.x1,bottom=r.y1) for r in rects[:100]
        if all(math.isfinite(v) for v in r) and r.x0<r.x1 and r.y0<r.y1]
    unique=(occurrences==1 and len(rects)==1 and len(regions)==1 and '\n' not in quote and '\r' not in quote
        and pdf_page.get_textbox(rects[0]).rstrip(' \t')==quote.rstrip(' \t'))
    status='UNIQUE' if unique else ('AMBIGUOUS' if regions else 'NOT_LOCATED')
    provenance=dict(status=status,regions=regions,regions_total=len(rects),regions_truncated=len(rects)>100,
        coordinate_system='unrotated_page_points_top_left',page_rotation=pdf_page.rotation,
        page_width=pdf_page.cropbox.width,page_height=pdf_page.cropbox.height,exact_occurrences=occurrences)
    if not unique:return provenance,unavailable()[1]
    box=BoundingBox(**regions[0]);block=DocumentBlock('native-quote:'+hashlib.sha256(quote.encode()).hexdigest(),'text',quote,(PageRef(page,box),))
    document=NormalizedDocument('local-original:'+file_id,'native-quote-partial', (block,),sha256)
    candidate=evidence_candidates(document)[0];validation=validate_evidence_candidate(document,candidate)
    return provenance,dict(status=validation.status.value,scope='SOURCE_BINDING_ONLY',candidate_id=candidate.evidence_id,reasons=list(validation.reasons))

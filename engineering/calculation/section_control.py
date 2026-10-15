"""Centroidal geometric properties of a solid, axis-aligned rectangle in SI."""
from dataclasses import dataclass, asdict
import hashlib
import json
from .planar_control import finite, provenance_valid

@dataclass(frozen=True)
class RectangleInput:
    width_m: float
    height_m: float
    source_sha256: str
    evidence_ids: tuple[str,...]
    units: str = 'N_m_Pa'

def calculate_rectangle(inputs):
    base=dict(status='BLOCK',data_class='CALCULATED',scope='SOLID_RECTANGLE_CENTROIDAL_GEOMETRY',acceptance_granted=False,actual_structure_verified=False,normative_verification='NOT_RUN')
    if not isinstance(inputs,RectangleInput):return dict(base,reasons=['TYPED_INPUT_REQUIRED'])
    if inputs.units!='N_m_Pa':return dict(base,reasons=['EXPLICIT_SI_UNITS_REQUIRED'])
    if not provenance_valid(inputs.source_sha256,inputs.evidence_ids):return dict(base,reasons=['SOURCE_AND_EVIDENCE_REFERENCES_REQUIRED'])
    if not all(finite(v) and v>0 for v in (inputs.width_m,inputs.height_m)):return dict(base,reasons=['POSITIVE_FINITE_DIMENSIONS_REQUIRED'])
    b,h=inputs.width_m,inputs.height_m
    result=dict(area_m2=b*h,iy_m4=h*b**3/12,iz_m4=b*h**3/12,wy_m3=h*b**2/6,wz_m3=b*h**2/6,centroid_y_m=h/2,centroid_z_m=b/2)
    if not all(finite(v) and v>0 for v in result.values()):return dict(base,reasons=['RESULT_OUT_OF_RANGE'])
    raw=json.dumps(asdict(inputs),sort_keys=True,separators=(',',':'),allow_nan=False)
    return dict(base,status='PASS',reasons=[],results=result,inputs=asdict(inputs),source_sha256=inputs.source_sha256,evidence_ids=list(inputs.evidence_ids),input_sha256=hashlib.sha256(raw.encode()).hexdigest(),assumptions=['SOLID_RECTANGLE_NO_HOLES','WIDTH_ALONG_Z_HEIGHT_ALONG_Y_CENTROIDAL_AXES','NO_TORSION_CONSTANT_OR_STRENGTH_CHECK','EVIDENCE_REFERENCES_NOT_INDEPENDENTLY_VERIFIED'])


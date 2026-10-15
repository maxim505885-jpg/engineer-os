"""Bounded IFC declaration inventory. No geometry/solver/acceptance inference."""
import hashlib
import json
import math
import re
from pathlib import Path

SUPPORTED=('IfcBeam','IfcColumn','IfcWall','IfcSlab')


def _valid_length_unit(unit,depth=0):
    if depth>8 or getattr(unit,'UnitType',None)!='LENGTHUNIT':return False
    if unit.is_a('IfcSIUnit'):
        return unit.Name=='METRE' and unit.Prefix in (None,'EXA','PETA','TERA','GIGA','MEGA',
            'KILO','HECTO','DECA','DECI','CENTI','MILLI','MICRO','NANO','PICO','FEMTO','ATTO')
    if unit.is_a()=='IfcConversionBasedUnit':
        dimensions=unit.Dimensions
        exponents=tuple(getattr(dimensions,name) for name in ('LengthExponent','MassExponent',
            'TimeExponent','ElectricCurrentExponent','ThermodynamicTemperatureExponent',
            'AmountOfSubstanceExponent','LuminousIntensityExponent'))
        factor=unit.ConversionFactor;value=factor.ValueComponent.wrappedValue
        return (exponents==(1,0,0,0,0,0,0) and type(value) in (int,float)
                and math.isfinite(value) and value>0 and _valid_length_unit(factor.UnitComponent,depth+1))
    return False


def _hash(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def _bounded(value,depth=0):
    if depth>8:raise ValueError('IFC_PROPERTY_LIMIT')
    if value is None or type(value) in (bool,int):return value
    if isinstance(value,float):
        if not math.isfinite(value):raise ValueError('IFC_NONFINITE_PROPERTY')
        return value
    if isinstance(value,str):
        if len(value)>4000:raise ValueError('IFC_PROPERTY_LIMIT')
        return value
    if isinstance(value,dict) and len(value)<=1000:
        return {str(k):_bounded(v,depth+1) for k,v in value.items() if k!='id'}
    if isinstance(value,(tuple,list)) and len(value)<=1000:
        return [_bounded(v,depth+1) for v in value]
    raise ValueError('IFC_PROPERTY_UNSUPPORTED_OR_LIMIT')


def inspect_ifc(path,*,expected_sha256,max_entities=100000):
    base=dict(status='BLOCK',scope='IFC_DECLARED_DATA_ONLY',data_class='PROJECT',
              acceptance_granted=False,calculation_model_verified=False,
              evidence_registered=False,reasons=[],elements=[],storeys=[])
    try:
        path=Path(path)
        if not isinstance(expected_sha256,str) or not re.fullmatch('[0-9a-f]{64}',expected_sha256):
            return dict(base,reasons=['IFC_SOURCE_IDENTITY_MISMATCH'])
        if not path.is_file() or not 0<path.stat().st_size<=50*1024*1024:
            return dict(base,reasons=['IFC_SOURCE_UNAVAILABLE_OR_SIZE_LIMIT'])
        sha=_hash(path)
        if sha!=expected_sha256:return dict(base,reasons=['IFC_SOURCE_IDENTITY_MISMATCH'])
        with path.open('rb') as stream:
            if not stream.read(64).lstrip().startswith(b'ISO-10303-21;'):
                return dict(base,reasons=['IFC_STEP_SIGNATURE_REQUIRED'])
        if type(max_entities) is not int or not 1<=max_entities<=100000:
            return dict(base,reasons=['IFC_ENTITY_LIMIT'])
        import ifcopenshell
        from ifcopenshell.util.element import get_container,get_materials,get_psets
        from ifcopenshell.util.unit import calculate_unit_scale
        model=ifcopenshell.open(str(path))
        for count,_ in enumerate(model,1):
            if count>max_entities:return dict(base,reasons=['IFC_ENTITY_LIMIT'])
        if model.schema not in ('IFC2X3','IFC4','IFC4X3','IFC4X3_ADD2'):
            return dict(base,reasons=['IFC_SCHEMA_UNSUPPORTED'])
        projects=model.by_type('IfcProject');reasons=[];scale=None
        if len(projects)!=1:reasons.append('IFC_SINGLE_PROJECT_REQUIRED')
        units=projects[0].UnitsInContext if len(projects)==1 else None
        length=[u for u in units.Units if getattr(u,'UnitType',None)=='LENGTHUNIT'] if units else []
        if len(length)!=1:reasons.append('IFC_LENGTH_UNIT_REQUIRED')
        elif not _valid_length_unit(length[0]):reasons.append('IFC_LENGTH_UNIT_INVALID')
        else:
            scale=calculate_unit_scale(model)
            if not math.isfinite(scale) or scale<=0:reasons.append('IFC_LENGTH_UNIT_INVALID')
        guids=set()
        for entity in model.by_type('IfcRoot'):
            guid=entity.GlobalId
            if not isinstance(guid,str) or not re.fullmatch('[0-3][0-9A-Za-z_$]{21}',guid):
                reasons.append('IFC_GUID_INVALID')
            elif guid in guids:reasons.append('IFC_DUPLICATE_GUID')
            guids.add(guid)
        spatial=[]
        for kind in ('IfcProject','IfcSite','IfcBuilding','IfcBuildingStorey'):
            for entity in model.by_type(kind):
                parents=[rel.RelatingObject.GlobalId for rel in getattr(entity,'Decomposes',())]
                spatial.append(dict(guid=entity.GlobalId,type=entity.is_a(),name=entity.Name,parent_guids=parents))
        rows=[]
        for kind in SUPPORTED:
            for entity in model.by_type(kind):
                containers=list(getattr(entity,'ContainedInStructure',()))
                container=get_container(entity)
                if len(containers)!=1 or container is None or not container.is_a('IfcBuildingStorey'):
                    reasons.append('IFC_STOREY_RELATION_UNVERIFIED')
                rows.append(dict(guid=entity.GlobalId,type=entity.is_a(),name=entity.Name,
                    storey_guid=container.GlobalId if container else None,
                    materials=[m.Name for m in get_materials(entity)],
                    properties=_bounded(get_psets(entity)),locator='ifc:guid:'+entity.GlobalId,
                    data_class='PROJECT',geometry_verified=False))
        if _hash(path)!=sha:return dict(base,reasons=['IFC_SOURCE_CHANGED_DURING_READ'])
        result=dict(base,status='BLOCK' if reasons else 'UNCERTAINTY',
            source_sha256=sha,schema=model.schema,length_to_m=scale,
            structure=_bounded(spatial),storeys=[x for x in spatial if x['type']=='IfcBuildingStorey'],
            elements=_bounded(rows),reasons=sorted(set(reasons)),
            limitations=['GEOMETRY_NOT_EVALUATED','MODEL_DECLARATIONS_NOT_ACTUAL_EVIDENCE',
                         'FORMAL_REQUIREMENTS_NOT_EVALUATED','NON_TARGET_ELEMENT_TYPES_NOT_INVENTORIED'])
        if len(json.dumps(result,allow_nan=False))>8*1024*1024:
            return dict(base,reasons=['IFC_REPORT_SIZE_LIMIT'])
        return result
    except ImportError:return dict(base,reasons=['IFC_DEPENDENCY_UNAVAILABLE'])
    except Exception:return dict(base,reasons=['IFC_PARSE_OR_PROPERTY_VALIDATION_FAILED'])


def compare_ifc(source,output,*,source_sha256):
    before=inspect_ifc(source,expected_sha256=source_sha256)
    try:after=inspect_ifc(output,expected_sha256=_hash(output))
    except OSError:after=dict(status='BLOCK')
    base=dict(status='BLOCK',acceptance_granted=False,geometry_equivalence_verified=False)
    if before['status']=='BLOCK' or after['status']=='BLOCK':
        return dict(base,reasons=['IFC_COMPARISON_INPUT_BLOCKED'])
    old={x['guid']:x for x in before['elements']};new={x['guid']:x for x in after['elements']}
    return dict(base,status='UNCERTAINTY',scope='IFC_DECLARED_TARGET_ELEMENTS_ONLY',
                source_sha256=before['source_sha256'],output_sha256=after['source_sha256'],
                added_guids=sorted(set(new)-set(old)),removed_guids=sorted(set(old)-set(new)),
                changed_guids=sorted(g for g in set(old)&set(new) if old[g]!=new[g]),
                length_units_changed=before['length_to_m']!=after['length_to_m'])

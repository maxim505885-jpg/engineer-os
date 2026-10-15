"""Explicit user-declared scalar requirements, not IDS/normative certification."""
import math
from .ifc_adapter import inspect_ifc, SUPPORTED, _hash


def check_requirements(path, *, expected_sha256, requirements):
    base=dict(status='BLOCK',scope='DECLARED_IFC_PROPERTY_REQUIREMENTS',acceptance_granted=False,
              calculation_model_verified=False,checks=[],reasons=[])
    if not isinstance(requirements,list) or not 1<=len(requirements)<=1000:
        return dict(base,reasons=['IFC_REQUIREMENT_CONTRACT_INVALID'])
    ids=set()
    for req in requirements:
        if not isinstance(req,dict) or set(req)!={'id','source','ifc_type','pset','property','equals','unit'}:
            return dict(base,reasons=['IFC_REQUIREMENT_CONTRACT_INVALID'])
        if any(not isinstance(req[k],str) or not req[k].strip() or len(req[k])>4000
               for k in ('id','source','ifc_type','pset','property','unit')):
            return dict(base,reasons=['IFC_REQUIREMENT_CONTRACT_INVALID'])
        value=req['equals']
        if (req['id'] in ids or req['ifc_type'] not in SUPPORTED or
            type(value) not in (str,int,float,bool) or
            (type(value) is float and not math.isfinite(value)) or
            (isinstance(value,str) and len(value)>4000) or
            req['unit'] not in ('project_length','unitless','text','boolean')):
            return dict(base,reasons=['IFC_REQUIREMENT_CONTRACT_INVALID'])
        if ((req['unit'] in ('project_length','unitless') and type(value) not in (int,float)) or
            (req['unit']=='text' and type(value) is not str) or
            (req['unit']=='boolean' and type(value) is not bool)):
            return dict(base,reasons=['IFC_REQUIREMENT_UNIT_TYPE_INVALID'])
        ids.add(req['id'])
    inventory=inspect_ifc(path,expected_sha256=expected_sha256)
    if inventory['status']=='BLOCK':return dict(base,reasons=inventory['reasons'])
    import ifcopenshell
    try:
        model=ifcopenshell.open(str(path))
        if _hash(path)!=expected_sha256:
            return dict(base,reasons=['IFC_SOURCE_CHANGED_DURING_READ'])
    except Exception:
        return dict(base,reasons=['IFC_REQUIREMENT_SOURCE_NOT_VERIFIED'])
    checks=[]
    for req in requirements:
        elements=[e for e in inventory['elements'] if e['type']==req['ifc_type']]
        if not elements:
            checks.append(dict(requirement=req,status='UNCERTAINTY',reason='NO_APPLICABLE_ELEMENT'))
        for entity in elements:
            value=entity['properties'].get(req['pset'],{}).get(req['property'])
            product=model.by_guid(entity['guid'])
            definitions=[rel.RelatingPropertyDefinition for rel in product.IsDefinedBy
                         if rel.is_a('IfcRelDefinesByProperties')]
            matching=[d for d in definitions if d.Name==req['pset']]
            quantities=[q for d in matching if d.is_a('IfcElementQuantity')
                        for q in d.Quantities if q.Name==req['property']]
            properties=[p for d in matching if d.is_a('IfcPropertySet')
                        for p in d.HasProperties if p.Name==req['property']]
            fields=quantities+properties
            unit_verified=False
            if len(fields)==1:
                field=fields[0]
                explicit=getattr(field,'Unit',None)
                nominal=getattr(field,'NominalValue',None)
                if req['unit']=='project_length':
                    unit_verified=(field.is_a('IfcQuantityLength') and explicit is None)
                elif req['unit']=='unitless':
                    unit_verified=(explicit is None and
                        (field.is_a('IfcQuantityCount') or
                         (field.is_a('IfcPropertySingleValue') and nominal is not None
                          and nominal.is_a() in ('IfcReal','IfcInteger','IfcCountMeasure','IfcRatioMeasure','IfcPositiveRatioMeasure','IfcNormalisedRatioMeasure'))))
                elif req['unit']=='text':
                    unit_verified=(nominal is not None and nominal.is_a() in ('IfcLabel','IfcText','IfcIdentifier'))
                elif req['unit']=='boolean':
                    unit_verified=(nominal is not None and nominal.is_a()=='IfcBoolean')
            if value is None or not unit_verified:
                status='UNCERTAINTY'
            else:
                same_type=(type(value) is type(req['equals']) or
                           type(value) in (int,float) and type(req['equals']) in (int,float))
                status='PASS' if same_type and value==req['equals'] else 'ERROR'
            checks.append(dict(requirement=req,status=status,actual=value,unit=req['unit'],
                length_to_m=inventory['length_to_m'] if req['unit']=='project_length' else None,
                source_sha256=expected_sha256,guid=entity['guid'],locator=entity['locator'],data_class='PROJECT'))
    if _hash(path)!=expected_sha256:return dict(base,reasons=['IFC_SOURCE_CHANGED_DURING_READ'])
    return dict(base,status='UNCERTAINTY',source_sha256=expected_sha256,checks=checks,
                limitations=['USER_REQUIREMENTS_ONLY','NO_NORMATIVE_OR_ACTUAL_CONFORMITY_CLAIM'])

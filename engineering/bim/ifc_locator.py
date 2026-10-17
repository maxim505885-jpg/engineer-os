"""Exact declared IFC scalar location. No measured value or unit qualification."""
import json
import math
from .ifc_adapter import inspect_ifc,_hash


def locate_declared_value(path,*,expected_sha256,guid,property_path):
    inventory=inspect_ifc(path,expected_sha256=expected_sha256)
    if inventory['status']=='BLOCK' or any(r in inventory['reasons'] for r in ('IFC_DUPLICATE_GUID','IFC_GUID_INVALID')):
        raise ValueError('IFC_LOCATOR_MODEL_NOT_VERIFIED')
    matches=[row for row in inventory['elements'] if row['guid']==guid]
    if len(matches)!=1:raise ValueError('IFC_GUID_NOT_UNIQUE')
    row=matches[0];measure='IFC_ATTRIBUTE';explicit_unit=None
    if len(property_path)==1 and property_path[0] in ('name','type','storey_guid'):
        value=row[property_path[0]]
    elif len(property_path)==3 and property_path[0]=='properties':
        import ifcopenshell
        model=ifcopenshell.open(str(path));product=model.by_guid(guid)
        definitions=[r.RelatingPropertyDefinition for r in product.IsDefinedBy if r.is_a('IfcRelDefinesByProperties')]
        definitions=[d for d in definitions if d.Name==property_path[1]]
        if len(definitions)!=1:raise ValueError('IFC_PROPERTY_SET_NOT_UNIQUE')
        definition=definitions[0]
        fields=getattr(definition,'HasProperties',None) or getattr(definition,'Quantities',())
        fields=[f for f in fields if f.Name==property_path[2]]
        if len(fields)!=1:raise ValueError('IFC_PROPERTY_NOT_UNIQUE')
        field=fields[0];nominal=getattr(field,'NominalValue',None)
        measure=nominal.is_a() if nominal is not None else field.is_a()
        unit=getattr(field,'Unit',None)
        if unit is not None:explicit_unit=dict(type=unit.is_a(),name=getattr(unit,'Name',None),prefix=getattr(unit,'Prefix',None))
        value=row['properties'][property_path[1]][property_path[2]]
    else:raise ValueError('IFC_PROPERTY_PATH_NOT_SUPPORTED')
    if type(value) not in (str,bool,int,float,type(None)) or (type(value) is float and not math.isfinite(value)):
        raise ValueError('IFC_SCALAR_VALUE_REQUIRED')
    quote=json.dumps(dict(value=value,measure_type=measure,explicit_unit=explicit_unit,
        model_length_to_m=inventory['length_to_m'],unit_interpretation='NOT_QUALIFIED'),
        ensure_ascii=False,allow_nan=False,sort_keys=True,separators=(',',':'))
    if len(quote)>4000:raise ValueError('IFC_QUOTE_LIMIT')
    if _hash(path)!=expected_sha256:raise ValueError('IFC_SOURCE_CHANGED_DURING_READ')
    return dict(status='UNCERTAINTY',quote=quote,data_class='PROJECT',acceptance_granted=False,
        scope='EXACT_IFC_DECLARED_SCALAR_ONLY',source_sha256=expected_sha256)

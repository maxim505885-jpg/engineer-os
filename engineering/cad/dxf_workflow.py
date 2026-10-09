"""Strict annotation-only derived DXF workflow. No repair, conversion or unit inference."""
import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from .intake import inspect_cad
SUPPORTED={'LINE','CIRCLE','ARC','LWPOLYLINE','TEXT'}
LAYER='ENGINEER_OS_DERIVED'
MAX_ENTITIES=10000
MAX_INVENTORY_ENTITIES=50000

def _reader():
    try:import ezdxf
    except ImportError:raise ValueError('CAD_DEPENDENCY_UNAVAILABLE: install requirements-cad.txt') from None
    return ezdxf

def _load(path,sha=None,*,inventory=False):
    identity=inspect_cad(path,sha)
    if identity['status']=='BLOCK':raise ValueError(','.join(identity['reasons']))
    doc=_reader().readfile(path)
    limit=MAX_INVENTORY_ENTITIES if inventory else MAX_ENTITIES
    if sum(len(block) for block in doc.blocks)>limit:
        raise ValueError('CAD_INVENTORY_ENTITY_LIMIT' if inventory else 'CAD_ENTITY_LIMIT')
    return doc,identity

def _tags(entity):
    from ezdxf.lldxf.tagwriter import TagCollector
    return [(tag.code,str(tag.value)) for tag in TagCollector.dxftags(entity)]

def _geometry(doc):
    return {entity.dxf.handle:_tags(entity) for block in doc.blocks for entity in block}

def _layers(doc):return {layer.dxf.name:_tags(layer) for layer in doc.layers}

# Writer metadata is the only permitted source-resource mutation. Geometry,
# font/style, linetype, block, layout and header settings remain exact.
VOLATILE_HEADERS={'$HANDSEED','$VERSIONGUID','$TDCREATE','$TDUCREATE','$TDUPDATE','$TDUUPDATE','$TDINDWG','$TDUSRTIMER'}

def _resources(doc):
    tables={table.name:{e.dxf.handle:_tags(e) for e in table} for table in doc.tables.tables() if table.name!='LAYER'}
    blocks={block.name:(_tags(block.block),_tags(block.endblk)) for block in doc.blocks}
    headers={name:str(doc.header[name]) for name in doc.header.varnames() if name not in VOLATILE_HEADERS}
    headers['CUSTOM_PROPERTIES']=str(doc.header.custom_vars.properties)
    writer_handle=None
    metadata=doc.rootdict.get('EZDXF_META')
    if metadata is not None and metadata.dxftype()=='DICTIONARY':
        writer=metadata.get('WRITTEN_BY_EZDXF')
        if writer is not None and writer.dxftype()=='DICTIONARYVAR':writer_handle=writer.dxf.handle
    objects={e.dxf.handle:[tag for tag in _tags(e) if not (e.dxf.handle==writer_handle and tag[0]==1)] for e in doc.objects}
    return tables,blocks,headers,objects

def inventory_dxf(path,expected_sha256=None):
    identity=inspect_cad(path,expected_sha256)
    if identity['status']=='BLOCK':return identity
    try:doc,identity=_load(path,expected_sha256,inventory=True)
    except (ValueError,ImportError) as exc:return dict(identity,status='BLOCK',reasons=[str(exc)])
    except Exception:return dict(identity,status='BLOCK',reasons=['DXF_PARSE_FAILED'])
    entities=[e for block in doc.blocks for e in block]
    reasons=[]
    if len(entities)>MAX_ENTITIES:reasons.append('CAD_ENTITY_LIMIT')
    if doc.units==0 or not 1<=doc.units<=24:reasons.append('DECLARED_UNITS_REQUIRED')
    if any(e.dxftype() not in SUPPORTED for e in entities):reasons.append('UNSUPPORTED_ENTITY_FOR_EDIT')
    from ezdxf.lldxf.tagwriter import TagCollector
    for entity in entities:
        for tag in TagCollector.dxftags(entity):
            values=tuple(tag.value) if hasattr(tag.value,'x') else (tag.value,)
            if any(isinstance(v,float) and not math.isfinite(v) for v in values):
                reasons.append('NONFINITE_SOURCE_GEOMETRY');break
    for entity in entities:
        if entity.dxftype() not in SUPPORTED:continue
        attrs=entity.dxf.all_existing_dxf_attribs()
        if any(hasattr(v,'z') and (v.z!=0 if k!='extrusion' else tuple(v)!=(0,0,1)) for k,v in attrs.items()) or attrs.get('elevation',0)!=0 or attrs.get('thickness',0)!=0:
            reasons.append('OUT_OF_PLANE_SOURCE_FOR_EDIT')
    tables_complete=len(doc.layers)<=100 and len(doc.blocks)<=100 and len(doc.layouts)<=100
    if not tables_complete:reasons.append('INVENTORY_TABLE_LIMIT')
    if any(not block.name.startswith('*') for block in doc.blocks):reasons.append('CUSTOM_BLOCK_FOR_EDIT')
    if any(len(layout) for layout in doc.layouts if layout.name!='Model'):reasons.append('PAPERSPACE_FOR_EDIT')
    # Audit can repair an in-memory document. Audit a second load, never the editing copy.
    audit=_reader().readfile(path).audit()
    if audit.has_errors or audit.has_fixes:reasons.append('DXF_AUDIT_ERRORS_OR_REPAIRS')
    if LAYER in doc.layers:reasons.append('DERIVED_LAYER_ALREADY_EXISTS')
    from ezdxf.units import unit_name
    return dict(identity,status='BLOCK' if reasons else 'REVIEW_REQUIRED',version=doc.dxfversion,units=doc.units,unit_name=unit_name(doc.units),entity_total=len(entities),inventory_read_complete=True,inventory_read_limit=MAX_INVENTORY_ENTITIES,edit_entity_limit=MAX_ENTITIES,entity_counts=dict(Counter(e.dxftype() for e in entities)),layers=[e.dxf.name[:250] for e in doc.layers][:100],blocks=[b.name[:250] for b in doc.blocks][:100],layouts=[l.name[:250] for l in doc.layouts][:100],texts=[dict(handle=e.dxf.handle,text=e.dxf.text[:2000],layer=e.dxf.layer) for e in entities if e.dxftype()=='TEXT'][:100],reasons=list(dict.fromkeys(reasons)),inventory_complete=tables_complete,texts_truncated=sum(e.dxftype()=='TEXT' for e in entities)>100 or any(len(e.dxf.text)>2000 for e in entities if e.dxftype()=='TEXT'),human_review='REQUIRED',engineering_acceptance='NOT_VERIFIED')

def _request(request):
    fields={'source_sha256','text','insert','height','reason','evidence_ids','units_acknowledged'}
    if not isinstance(request,dict) or set(request)!=fields:raise ValueError('Exact annotation request fields required')
    for key,limit in [('text',500),('reason',1000),('source_sha256',64)]:
        if not isinstance(request[key],str) or not request[key].strip() or len(request[key])>limit or any(ord(c)<32 for c in request[key]):raise ValueError('Invalid annotation '+key)
    if len(request['source_sha256'])!=64 or any(c not in '0123456789abcdef' for c in request['source_sha256']):raise ValueError('Invalid source hash')
    if not isinstance(request['insert'],list) or len(request['insert'])!=2:raise ValueError('Annotation requires [x,y]')
    for value in request['insert']+[request['height']]:
        if type(value) not in {int,float} or not math.isfinite(value) or abs(value)>1e9:raise ValueError('Invalid annotation coordinate/height')
    if request['height']<=0:raise ValueError('Annotation height must be positive')
    if type(request['units_acknowledged']) is not int:raise ValueError('Declared units acknowledgment required')
    refs=request['evidence_ids']
    if not isinstance(refs,list) or not 1<=len(refs)<=20 or any(not isinstance(x,str) or not 1<=len(x)<=100 for x in refs) or len(set(refs))!=len(refs):raise ValueError('Bounded distinct evidence references required')
    return json.loads(json.dumps(request,allow_nan=False))

def derive_annotation(source,destination,request):
    request=_request(request);source=Path(source);destination=Path(destination)
    if source.resolve()==destination.resolve() or destination.exists():raise ValueError('Derived output must be a new file')
    report=inventory_dxf(source,request['source_sha256'])
    if report['status']=='BLOCK':raise ValueError(','.join(report['reasons']))
    if request['units_acknowledged']!=report['units']:raise ValueError('Unit acknowledgment mismatch')
    doc,_=_load(source,request['source_sha256']);doc.layers.new(LAYER)
    entity=doc.modelspace().add_text('DERIVED: '+request['text'],dxfattribs={'insert':request['insert'],'height':request['height'],'layer':LAYER})
    manifest=dict(source_sha256=request['source_sha256'],request=request,added_handle=entity.dxf.handle,human_review='REQUIRED',engineering_acceptance='NOT_VERIFIED')
    # Exclusive reservation prevents replacing an existing original or derivative.
    with destination.open('xb') as stream:pass
    try:
        doc.saveas(destination)
        manifest['output_sha256']=hashlib.sha256(destination.read_bytes()).hexdigest()
        manifest['verification']=verify_export(source,destination,manifest)
        if manifest['verification']['status']!='PASS':raise ValueError('CAD export verification failed: '+','.join(manifest['verification'].get('reasons',[])))
        return manifest
    except Exception:
        destination.unlink(missing_ok=True);raise

def verify_export(source,output,manifest):
    try:
        request=_request(manifest['request'])
        if request['source_sha256']!=manifest['source_sha256']:raise ValueError('Request source hash mismatch')
        before,_=_load(source,manifest['source_sha256']);after,identity=_load(output)
        if identity['source_sha256']!=manifest['output_sha256']:raise ValueError('Output hash mismatch')
        old=_geometry(before);new=_geometry(after);handle=manifest['added_handle']
        if set(new)-set(old)!={handle} or any(new.get(h)!=tags for h,tags in old.items()):raise ValueError('Original entity geometry/data changed')
        old_layers=_layers(before);new_layers=_layers(after)
        if set(new_layers)-set(old_layers)!={LAYER} or any(new_layers.get(h)!=tags for h,tags in old_layers.items()):raise ValueError('Original layers changed')
        entity=after.entitydb[handle]
        if entity.dxftype()!='TEXT' or entity.dxf.layer!=LAYER or entity.dxf.text!='DERIVED: '+request['text'] or list(entity.dxf.insert)[:2]!=request['insert'] or entity.dxf.height!=request['height']:raise ValueError('Annotation mismatch')
        old_resources=_resources(before);new_resources=_resources(after)
        if old_resources[0]!=new_resources[0]:raise ValueError('Original table resources changed')
        if old_resources[1]!=new_resources[1]:raise ValueError('Original block resources changed')
        if old_resources[2]!=new_resources[2]:raise ValueError('Original header settings changed')
        if old_resources[3]!=new_resources[3]:raise ValueError('Original object/layout resources changed')
        if after.units!=before.units or after.dxfversion!=before.dxfversion:raise ValueError('Units/version changed')
        # Generate the exact requested annotation only after source resources have
        # been compared. Canonical tags bind 3D insertion, owner/modelspace,
        # style, rotation, extrusion, XDATA and every other serialized attribute.
        expected_layer=before.layers.new(LAYER)
        expected=before.modelspace().add_text('DERIVED: '+request['text'],dxfattribs={'insert':request['insert'],'height':request['height'],'layer':LAYER})
        if expected.dxf.handle!=handle or _tags(entity)!=_tags(expected):raise ValueError('Annotation canonical data mismatch')
        if _tags(after.layers.get(LAYER))!=_tags(expected_layer):raise ValueError('Annotation layer canonical data mismatch')
        audit=after.audit()
        if audit.has_errors or audit.has_fixes:raise ValueError('Export audit errors/repairs')
        return dict(status='PASS',original_entities_preserved=len(old),added_entities=[handle],units_preserved=True,human_review='REQUIRED',engineering_acceptance='NOT_VERIFIED')
    except Exception as exc:return dict(status='BLOCK',reasons=[str(exc)],human_review='REQUIRED')

"""Source-linked package image bytes, not rendered Word pages or visual meaning."""
import hashlib
import json
import posixpath
import re
import xml.etree.ElementTree as ET
from urllib.parse import unquote, urlsplit

A='{http://schemas.openxmlformats.org/drawingml/2006/main}'
V='{urn:schemas-microsoft-com:vml}'
R='{http://schemas.openxmlformats.org/officeDocument/2006/relationships}'
REL='{http://schemas.openxmlformats.org/package/2006/relationships}'
WP='{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}'
O='{urn:schemas-microsoft-com:office:office}'
A14='{http://schemas.microsoft.com/office/drawing/2010/main}'
MAX_EFFECT_XML_BYTES=1024*1024
MAX_EFFECT_RECORDS=10000
MAX_EFFECT_REFERENCE_XML_BYTES=16*1024*1024


def validate_identity(identity):
    from .office import OfficeError
    # Supported ASCII NCName subset. Other IDs fail closed, never cross-bind.
    if not identity or len(identity)>1024 or not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_.-]*',identity):
        raise OfficeError('Invalid image relationship ID')


def relationships(package,part):
    from .office import OfficeError,MAX_ENTRIES
    cache=getattr(package,'image_relationships',None)
    if cache is None:cache={};package.image_relationships=cache
    if part in cache:return cache[part]
    path=posixpath.join(posixpath.dirname(part),'_rels',posixpath.basename(part)+'.rels')
    result={}
    if path in package.names:
        root=package.xml(path)
        if root.tag!=REL+'Relationships' or len(root)>MAX_ENTRIES:raise OfficeError('Invalid image relationships')
        for child in root:
            identity=child.get('Id','')
            validate_identity(identity)
            if child.tag!=REL+'Relationship' or not identity or len(identity)>1024 or identity in result:
                raise OfficeError('Ambiguous image relationship identity')
            result[identity]=dict(child.attrib)
    cache[part]=result
    return result


def target_part(part,target):
    from .office import OfficeError
    if not target or len(target)>1024 or re.search(r'%(?![0-9a-fA-F]{2})',target):raise OfficeError('Invalid image target')
    target=unquote(target,encoding='utf-8',errors='strict');url=urlsplit(target)
    if url.scheme or url.netloc or url.query or url.fragment or '\\' in target or any(ord(c)<32 or ord(c)==127 for c in target):
        raise OfficeError('Invalid internal image path')
    path=posixpath.normpath(target.lstrip('/') if target.startswith('/') else posixpath.join(posixpath.dirname(part),target))
    if path in {'.','..'} or path.startswith('../'):raise OfficeError('Image path escapes package')
    return path


def image_descriptor(package,part,identity,linked=False,*,layer=False):
    from .office import OfficeError,MAX_IMAGE_BYTES,MAX_IMAGE_TOTAL_BYTES,MAX_ASSET_TOTAL_BYTES
    result=dict(relationship_id=identity,status='UNAVAILABLE',scope='PACKAGE_IMAGE_UNTRANSFORMED',
                content_verified=False,layout_verified=False)
    rel=relationships(package,part).get(identity)
    if linked or (rel and rel.get('TargetMode')=='External'):
        result['reason']='EXTERNAL_IMAGE_NOT_FETCHED';return result
    allowed_types={R[1:-1]+'/image'}
    if layer:allowed_types.add('http://schemas.microsoft.com/office/2007/relationships/hdphoto')
    if not rel or rel.get('Type') not in allowed_types:
        result['reason']='IMAGE_RELATIONSHIP_MISSING_OR_WRONG_TYPE';return result
    if rel.get('TargetMode','Internal')!='Internal':raise OfficeError('Invalid image target mode')
    path=target_part(part,rel.get('Target',''));result['part']=path
    if path not in package.names:result['reason']='IMAGE_PART_MISSING';return result
    cache=getattr(package,'image_assets',None)
    if cache is None:cache={};package.image_assets=cache;package.image_bytes=getattr(package,'image_bytes',0)
    if path not in cache:
        info=package.zip.getinfo(path)
        if info.is_dir() or info.file_size>MAX_IMAGE_BYTES or package.image_bytes+info.file_size>MAX_IMAGE_TOTAL_BYTES or getattr(package,'asset_bytes',0)+info.file_size>MAX_ASSET_TOTAL_BYTES:
            raise OfficeError('Image byte limit')
        data=package.zip.read(path);package.image_bytes+=len(data);package.asset_bytes=getattr(package,'asset_bytes',0)+len(data)
        cache[path]=dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
        if path.lower().endswith('.emf'):
            from . import emf_text
            try:cache[path]['native_emf']=emf_text.read(data)
            except emf_text.EMFLimitError as exc:raise OfficeError(str(exc)) from exc
            except emf_text.EMFError as exc:
                cache[path]['native_emf']=dict(status='UNAVAILABLE',reason=str(exc),content_verified=False,layout_verified=False)
    if 'native_emf' in cache[path]:
        from . import emf_text
        used=getattr(package,'emf_reference_bytes',0)+len(json.dumps(cache[path]['native_emf'],ensure_ascii=False).encode('utf-8'))
        if used>emf_text.MAX_REFERENCE_JSON_BYTES:raise OfficeError('EMF reference text limit')
        package.emf_reference_bytes=used
    result.update(cache[path],status='BOUND_PACKAGE_IMAGE')
    return result


def layer_metadata(package,node,parents,part):
    from .office import OfficeError
    result=dict(cached_bitmap_association_status='UNAVAILABLE',cached_processed_bitmap=None,
                declared_effects=[],effects_applied=False,render_verified=False,layout_verified=False)
    used=0
    for effect in node.iter(A14+'imgEffect'):
        xml=ET.tostring(effect,encoding='unicode')
        size=len(xml.encode('utf-8'));used+=size
        package.effect_reference_xml_bytes=getattr(package,'effect_reference_xml_bytes',0)+size
        if package.effect_reference_xml_bytes>MAX_EFFECT_REFERENCE_XML_BYTES:raise OfficeError('Image declared effects reference limit')
        if used>MAX_EFFECT_XML_BYTES or len(result['declared_effects'])>=MAX_EFFECT_RECORDS:
            raise OfficeError('Image declared effects limit')
        result['declared_effects'].append(dict(qname=effect.tag,attributes=dict(effect.attrib),normalized_xml=xml,
            children=[dict(qname=e.tag,attributes=dict(e.attrib)) for e in effect],
            wrapper_attributes=dict(node.attrib)))
    ancestor=parents.get(node)
    while ancestor is not None and ancestor.tag!=A+'blip':ancestor=parents.get(ancestor)
    reason=None
    if node.get(R+'embed') is not None and node.get(R+'link') is not None:reason='LAYER_AMBIGUOUS_IDENTITY'
    elif node.get(R+'link') is not None:reason='LAYER_LINKED_IMAGE'
    elif ancestor is None:reason='ANCESTOR_BLIP_MISSING'
    elif ancestor.get(R+'embed') is not None and ancestor.get(R+'link') is not None:reason='ANCESTOR_BLIP_AMBIGUOUS_IDENTITY'
    elif ancestor.get(R+'link') is not None:reason='ANCESTOR_BLIP_LINKED_IMAGE'
    elif ancestor.get(R+'embed') is None:reason='ANCESTOR_BLIP_IDENTITY_MISSING'
    else:
        identity=ancestor.get(R+'embed');validate_identity(identity)
        cached=image_descriptor(package,part,identity)
        result['cached_processed_bitmap']=cached
        if cached['status']=='BOUND_PACKAGE_IMAGE':result['cached_bitmap_association_status']='BOUND_ANCESTOR_BLIP'
        else:reason=cached.get('reason','ANCESTOR_BLIP_UNAVAILABLE')
    if reason:result['cached_bitmap_association_reason']=reason
    return result


def bind_images(package,element,locator):
    from .office import OfficeError,MAX_IMAGE_REFERENCES
    refs=[]
    parents={child:parent for parent in element.iter() for child in parent}
    for node in element.iter():
        if node.tag==A+'blip':
            identities=[(node.get(R+'embed'),False),(node.get(R+'link'),True)]
        elif node.tag==A14+'imgLayer':
            identities=[(node.get(R+'embed'),False),(node.get(R+'link'),True)]
        elif node.tag==V+'imagedata':
            primary=node.get(R+'id');legacy=node.get(O+'relid')
            if primary is not None and legacy is not None and primary!=legacy:raise OfficeError('Conflicting VML image identity')
            identities=[(primary if primary is not None else legacy,False)]
        else:continue
        for identity,linked in identities:
            if identity is None:continue
            validate_identity(identity)
            count=getattr(package,'image_reference_count',0)+1;package.image_reference_count=count
            if count>MAX_IMAGE_REFERENCES or len(identity)>1024:raise OfficeError('Image reference limit')
            descriptor=image_descriptor(package,locator['part'],identity,linked,layer=node.tag==A14+'imgLayer')
            descriptor['image']=len(refs)+1
            if node.tag==A14+'imgLayer':
                descriptor['reference_kind']='HD_PHOTO_LAYER'
                descriptor['layer_composition_verified']=False
                descriptor.update(layer_metadata(package,node,parents,locator['part']))
            refs.append(descriptor)
    if refs:
        locator['images']=refs
        # These are native declared alternative labels, not interpreted captions.
        labels=[dict(e.attrib) for e in element.iter(WP+'docPr')]
        if labels:locator['declared_drawing_labels']=labels
    return refs

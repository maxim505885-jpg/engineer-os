"""Source-linked package image bytes, not rendered Word pages or visual meaning."""
import hashlib
import posixpath
import re
from urllib.parse import unquote, urlsplit

A='{http://schemas.openxmlformats.org/drawingml/2006/main}'
V='{urn:schemas-microsoft-com:vml}'
R='{http://schemas.openxmlformats.org/officeDocument/2006/relationships}'
REL='{http://schemas.openxmlformats.org/package/2006/relationships}'
WP='{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}'
O='{urn:schemas-microsoft-com:office:office}'


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


def image_descriptor(package,part,identity,linked=False):
    from .office import OfficeError,MAX_IMAGE_BYTES,MAX_IMAGE_TOTAL_BYTES
    result=dict(relationship_id=identity,status='UNAVAILABLE',scope='PACKAGE_IMAGE_UNTRANSFORMED',
                content_verified=False,layout_verified=False)
    rel=relationships(package,part).get(identity)
    if linked or (rel and rel.get('TargetMode')=='External'):
        result['reason']='EXTERNAL_IMAGE_NOT_FETCHED';return result
    if not rel or rel.get('Type')!=R[1:-1]+'/image':
        result['reason']='IMAGE_RELATIONSHIP_MISSING_OR_WRONG_TYPE';return result
    if rel.get('TargetMode','Internal')!='Internal':raise OfficeError('Invalid image target mode')
    path=target_part(part,rel.get('Target',''));result['part']=path
    if path not in package.names:result['reason']='IMAGE_PART_MISSING';return result
    cache=getattr(package,'image_assets',None)
    if cache is None:cache={};package.image_assets=cache;package.image_bytes=0
    if path not in cache:
        info=package.zip.getinfo(path)
        if info.is_dir() or info.file_size>MAX_IMAGE_BYTES or package.image_bytes+info.file_size>MAX_IMAGE_TOTAL_BYTES:
            raise OfficeError('Image byte limit')
        data=package.zip.read(path);package.image_bytes+=len(data)
        cache[path]=dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
    result.update(cache[path],status='BOUND_PACKAGE_IMAGE')
    return result


def bind_images(package,element,locator):
    from .office import OfficeError,MAX_IMAGE_REFERENCES
    refs=[]
    for node in element.iter():
        if node.tag==A+'blip':
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
            descriptor=image_descriptor(package,locator['part'],identity,linked)
            descriptor['image']=len(refs)+1;refs.append(descriptor)
    if refs:
        locator['images']=refs
        # These are native declared alternative labels, not interpreted captions.
        labels=[dict(e.attrib) for e in element.iter(WP+'docPr')]
        if labels:locator['declared_drawing_labels']=labels
    return refs

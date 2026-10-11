"""Declared OLE package references; no object activation or executable dispatch."""
import hashlib
from .word_images import O,R,relationships,target_part,validate_identity


def bind_objects(package,element,locator):
    from .office import OfficeError,MAX_IMAGE_BYTES,MAX_OBJECT_TOTAL_BYTES,MAX_ASSET_TOTAL_BYTES,MAX_IMAGE_REFERENCES
    result=[]
    for node in element.iter(O+'OLEObject'):
        identity=node.get(R+'id')
        if identity is None:identity=''
        validate_identity(identity)
        count=getattr(package,'image_reference_count',0)+1;package.image_reference_count=count
        if count>MAX_IMAGE_REFERENCES:raise OfficeError('Object/image reference limit')
        item=dict(object=len(result)+1,relationship_id=identity,status='UNAVAILABLE',scope='PACKAGE_OBJECT_NOT_ACTIVATED',
                  content_verified=False,layout_verified=False,executed=False,
                  program_id=node.get('ProgID',''),declared_type=node.get('Type',''),shape_id=node.get('ShapeID',''))
        if any(len(item[k])>1024 for k in ('program_id','declared_type','shape_id')):raise OfficeError('Object attribute limit')
        rel=relationships(package,locator['part']).get(identity)
        if node.get('Type')!='Embed' or (rel and rel.get('TargetMode')=='External'):
            item['reason']='LINKED_OR_UNSUPPORTED_OBJECT_NOT_FETCHED'
        elif not rel or rel.get('Type')!=R[1:-1]+'/oleObject':item['reason']='OBJECT_RELATIONSHIP_MISSING_OR_WRONG_TYPE'
        else:
            if rel.get('TargetMode','Internal')!='Internal':raise OfficeError('Invalid object target mode')
            path=target_part(locator['part'],rel.get('Target',''));item['part']=path
            if path not in package.names:item['reason']='OBJECT_PART_MISSING'
            else:
                cache=getattr(package,'object_assets',None)
                if cache is None:cache={};package.object_assets=cache
                if path not in cache:
                    info=package.zip.getinfo(path);used=getattr(package,'object_bytes',0)
                    if info.is_dir() or info.file_size>MAX_IMAGE_BYTES or used+info.file_size>MAX_OBJECT_TOTAL_BYTES or getattr(package,'asset_bytes',0)+info.file_size>MAX_ASSET_TOTAL_BYTES:raise OfficeError('Object/image byte limit')
                    data=package.zip.read(path);package.object_bytes=used+len(data);package.asset_bytes=getattr(package,'asset_bytes',0)+len(data)
                    from . import ole_bitmap
                    cache[path]=dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),bitmap=ole_bitmap.describe(data))
                item.update(cache[path],status='BOUND_PACKAGE_OBJECT')
        result.append(item)
    if result:locator['embedded_objects']=result
    return result

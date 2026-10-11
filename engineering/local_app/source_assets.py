"""Bounded readback of source-only document assets, never accepted evidence."""
import hashlib
import zipfile
from dataclasses import asdict
from pathlib import Path
from xml.etree import ElementTree as ET
from engineering.document_intelligence.asset_provenance import DocumentAssetEvidence,verify_payload
from .files import file_limit
from .office import Package,M,MAX_IMAGE_BYTES,MAX_IMAGE_TOTAL_BYTES,MAX_OBJECT_TOTAL_BYTES,MAX_ASSET_TOTAL_BYTES,MAX_UNITS


def candidates(store,session_id,file_id,page=None):
    f=store.get_file(file_id)
    if f['session_id']!=session_id:raise ValueError('File belongs to another project')
    path=Path(f['path'])
    if path.stat().st_size>file_limit(f['name']):raise ValueError('Source size limit')
    with path.open('rb') as stream:data=stream.read(file_limit(f['name'])+1)
    if len(data)>file_limit(f['name']):raise ValueError('Source size limit')
    source_hash=hashlib.sha256(data).hexdigest()
    if source_hash!=f['sha256']:raise ValueError('SOURCE_IDENTITY_MISMATCH')
    suffix=Path(f['name']).suffix.lower()
    limitations=['SOURCE_ASSETS_ONLY_CONTENT_UNVERIFIED']
    if suffix=='.pdf':
        if page is None:raise ValueError('PDF page required')
        from engineering.document_intelligence.pdf_table_asset_ingestion import pdf_table_candidates
        result=pdf_table_candidates(path,[page])
        limitations+=['TABLE_DETECTION_UNVERIFIED','NATIVE_TEXT_ONLY_RASTER_CONTENT_NOT_READ']
    elif suffix=='.docx':
        result=[];package=Package(data);total=0;image_total=0;object_total=0;referenced_objects=set()
        def collect(item,payload):
            nonlocal total,image_total,object_total
            total+=len(payload)
            if item.asset_kind=='embedded_object':object_total+=len(payload)
            else:image_total+=len(payload)
            if len(payload)>MAX_IMAGE_BYTES or total>MAX_ASSET_TOTAL_BYTES or image_total>MAX_IMAGE_TOTAL_BYTES or object_total>MAX_OBJECT_TOTAL_BYTES or len(result)>=MAX_UNITS:
                raise ValueError('Asset size/count limit')
            result.append((item,payload))
        try:
            for name in sorted(package.names):
                if name.startswith('word/') and name.endswith('.xml'):
                    root=package.xml(name)
                    from .word_objects import bind_objects
                    for obj in bind_objects(package,root,dict(part=name)):
                        if obj['status']=='BOUND_PACKAGE_OBJECT':referenced_objects.add(obj['part'])
                        else:limitations.append('OBJECT_REFERENCE_UNAVAILABLE')
                    for index,formula in enumerate(root.iter(M+'oMath')):
                        payload=ET.tostring(formula)
                        item=DocumentAssetEvidence(source_hash,hashlib.sha256(payload).hexdigest(),'omml_formula',f'{name}#oMath[{index}]')
                        collect(item,payload)
                elif name.startswith(('word/media/','word/embeddings/')) and not name.endswith('/'):
                    size=package.zip.getinfo(name).file_size
                    if size>MAX_IMAGE_BYTES or total+size>MAX_ASSET_TOTAL_BYTES or (object_total+size>MAX_OBJECT_TOTAL_BYTES if name.startswith('word/embeddings/') else image_total+size>MAX_IMAGE_TOTAL_BYTES):raise ValueError('Asset size limit')
                    payload=package.zip.read(name)
                    kind='embedded_object' if name.startswith('word/embeddings/') else 'emf_graphic' if name.lower().endswith('.emf') else 'embedded_image'
                    item=DocumentAssetEvidence(source_hash,hashlib.sha256(payload).hexdigest(),kind,name)
                    collect(item,payload)
                if len(result)>MAX_UNITS:raise ValueError('Asset count limit')
            declared={item.location for item,_ in result if item.asset_kind=='embedded_object'}
            for name in sorted(referenced_objects-declared):
                size=package.zip.getinfo(name).file_size
                if size>MAX_IMAGE_BYTES or total+size>MAX_ASSET_TOTAL_BYTES or object_total+size>MAX_OBJECT_TOTAL_BYTES:raise ValueError('Asset size limit')
                payload=package.zip.read(name)
                collect(DocumentAssetEvidence(source_hash,hashlib.sha256(payload).hexdigest(),'embedded_object',name),payload)
            if declared or referenced_objects:limitations.append('EMBEDDED_OLE_UNVERIFIED_NOT_ACTIVATED')
            limitations+=['WORD_LAYOUT_AND_IMAGE_TRANSFORMS_UNVERIFIED','FORMULA_VISUAL_AND_MATHEMATICAL_VALIDATION_NOT_PERFORMED']
        finally:package.close()
    else:raise ValueError('Only DOCX and PDF source assets supported')
    with path.open('rb') as stream:after_hash=hashlib.file_digest(stream,'sha256').hexdigest()
    if after_hash!=source_hash:raise ValueError('SOURCE_IDENTITY_CHANGED_DURING_EXTRACTION')
    if len(result)>MAX_UNITS or any(len(payload)>MAX_IMAGE_BYTES for _,payload in result):raise ValueError('Asset size/count limit')
    for item,payload in result:verify_payload(item,payload,source_hash)
    return f,result,limitations


def read_assets(store,session_id,file_id,*,page=None,offset=0,limit=50,candidate_id=None):
    if not 0<=offset<=MAX_UNITS or not 1<=limit<=50:raise ValueError('Invalid asset pagination')
    try:f,items,limitations=candidates(store,session_id,file_id,page)
    except (zipfile.BadZipFile,ET.ParseError,RecursionError) as exc:raise ValueError('Invalid source package/XML') from exc
    if candidate_id is not None:
        matches=[(item,payload) for item,payload in items if item.candidate_id==candidate_id]
        if len(matches)!=1:raise ValueError('Unknown source candidate')
        item,payload=matches[0]
        return payload,{'Content-Disposition':'attachment; filename="source-asset.bin"','X-Source-SHA256':f['sha256'],'X-Asset-SHA256':item.asset_sha256,'X-Asset-Status':'UNCERTAINTY','X-Asset-Kind':item.asset_kind}
    def summary(item,payload):
        result=dict(asdict(item),candidate_id=item.candidate_id,payload_size=len(payload),representation='SERIALIZED_OMML_FRAGMENT' if item.asset_kind=='omml_formula' else 'DETECTOR_CELL_JSON' if item.asset_kind=='table_cells' else 'SOURCE_BINARY')
        if item.asset_kind=='embedded_object':
            from . import ole_bitmap
            result['bitmap']=ole_bitmap.describe(payload)
        return result
    return dict(source_sha256=f['sha256'],content_verified=False,status='UNCERTAINTY',total=len(items),offset=offset,limit=limit,
        limitations=list(dict.fromkeys(limitations)),items=[summary(item,payload) for item,payload in items[offset:offset+limit]])

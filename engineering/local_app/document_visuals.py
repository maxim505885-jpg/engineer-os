"""Authenticated source identity boundaries for passive document derivatives."""
import base64
import hashlib
import io
import re
from pathlib import Path
from xml.etree import ElementTree as ET
from .files import file_limit
from .office import Package,M
from engineering.document_intelligence.asset_provenance import DocumentAssetEvidence


def source(store,sid,fid,suffix,expected):
    f=store.get_file(fid)
    if f['session_id']!=sid:raise ValueError('File belongs to another project')
    if Path(f['name']).suffix.lower()!=suffix:raise ValueError('Unexpected source format')
    if not isinstance(expected,str) or expected!=f['sha256']:raise ValueError('SOURCE_IDENTITY_MISMATCH')
    with Path(f['path']).open('rb') as stream:data=stream.read(file_limit(f['name'])+1)
    if len(data)!=f['size'] or len(data)>file_limit(f['name']) or hashlib.sha256(data).hexdigest()!=expected:raise ValueError('SOURCE_IDENTITY_MISMATCH')
    return f,data


def unchanged(f):
    with Path(f['path']).open('rb') as stream:digest=hashlib.file_digest(stream,'sha256').hexdigest()
    if digest!=f['sha256']:raise ValueError('SOURCE_IDENTITY_CHANGED_DURING_EXTRACTION')


def formula_preview(store,sid,fid,body):
    if set(body)!={'part','ordinal','candidate_id','expected_sha256'}:raise ValueError('Formula source locator required')
    part=body['part'];ordinal=body['ordinal']
    if not isinstance(part,str) or not re.fullmatch(r'word/[A-Za-z0-9_./-]+\.xml',part) or any(p in {'','..','.'} for p in part.split('/')):raise ValueError('Invalid formula part')
    if type(ordinal) is not int or not 0<=ordinal<=20000:raise ValueError('Invalid formula ordinal')
    f,data=source(store,sid,fid,'.docx',body['expected_sha256'])
    package=Package(data)
    try:
        if part not in package.names:raise ValueError('Unknown formula part')
        formulas=list(package.xml(part).iter(M+'oMath'))
        if ordinal>=len(formulas):raise ValueError('Unknown formula ordinal')
        payload=ET.tostring(formulas[ordinal]);asset_hash=hashlib.sha256(payload).hexdigest()
    finally:package.close()
    item=DocumentAssetEvidence(f['sha256'],asset_hash,'omml_formula',f'{part}#oMath[{ordinal}]')
    if body['candidate_id']!=item.candidate_id:raise ValueError('Unknown source candidate')
    from .word_formula_preview import render_formula
    png,dossier=render_formula(data,part,ordinal)
    if not isinstance(png,bytes) or len(png)>10*1024*1024:raise ValueError('Formula preview byte limit')
    from PIL import Image
    with Image.open(io.BytesIO(png)) as image:
        if image.format!='PNG' or image.width*image.height>16000000:raise ValueError('Invalid formula preview')
        image.verify()
    unchanged(f)
    return dict(status='UNCERTAINTY',source_sha256=f['sha256'],candidate_id=item.candidate_id,asset_sha256=asset_hash,
                png_base64=base64.b64encode(png).decode(),png_sha256=hashlib.sha256(png).hexdigest(),dossier=dossier,
                content_verified=False,layout_verified=False,mathematics_verified=False,acceptance_granted=False)


def table_readback(store,sid,fid,body):
    if set(body)!={'page','bbox','backend','expected_sha256'}:raise ValueError('Table source locator required')
    if body['backend'] not in {'img2table','paddleocr'}:raise ValueError('Unknown table backend')
    if type(body['page']) is not int or body['page']<1:raise ValueError('Invalid page')
    f,data=source(store,sid,fid,'.pdf',body['expected_sha256'])
    from .table_readback import read_tables
    result=read_tables(data,body['page'],body['bbox'],body['backend'])
    unchanged(f)
    # Adapter candidates cannot grant acceptance even if an optional backend returns it.
    result.update(content_verified=False,layout_verified=False,acceptance_granted=False)
    return result

"""Render one checked draft structure into DOCX and PDF. No remote resources."""
import io
from html import escape
import zipfile
import re
import unicodedata
import base64
import hashlib

MAX_ILLUSTRATIONS=3
MAX_ILLUSTRATION_BYTES=1024*1024
MAX_TOTAL_ILLUSTRATION_BYTES=2*1024*1024


def prepare_illustrations(store,session_id,originals,requests):
    """Render authenticated originals without turning illustrations into evidence."""
    from .preview import render_original
    from .core_plan import verify_originals
    from PIL import Image
    if requests is None:requests=[]
    if not isinstance(requests,list) or len(requests)>MAX_ILLUSTRATIONS:raise ValueError('Illustration request limit: 3')
    allowed={f['id']:f for f in originals};descriptors=[];assets=[];total=0
    for request in requests:
        if not isinstance(request,dict) or set(request)!={'file_id','page'}:raise ValueError('Illustration requires source file and page only')
        if not isinstance(request['file_id'],str):raise ValueError('Invalid illustration source ID')
        source=allowed.get(request['file_id'])
        if source is None or type(request['page']) is not int or request['page']<1:raise ValueError('Illustration requires a current case original and valid page')
        original=store.get_file(source['id'])
        if original['session_id']!=session_id or original['sha256']!=source['sha256']:raise ValueError('Illustration source identity changed')
        verify_originals([original])
        png=render_original(store,session_id,source['id'],request['page'])
        with Image.open(io.BytesIO(png)) as image:
            if max(image.size)>1600:
                image.thumbnail((1600,1600));out=io.BytesIO();image.save(out,format='PNG');png=out.getvalue()
            width,height=image.size
        total+=len(png)
        if len(png)>MAX_ILLUSTRATION_BYTES or total>MAX_TOTAL_ILLUSTRATION_BYTES:raise ValueError('Illustration byte limit exceeded')
        verify_originals([original])
        name='illustration-'+str(len(assets)+1)+'.png'
        descriptor=dict(asset_id=name,file_id=source['id'],page=request['page'],source_sha256=source['sha256'],
                        image_sha256=hashlib.sha256(png).hexdigest(),width=width,height=height,
                        caption='НЕПРОВЕРЕННАЯ ИЛЛЮСТРАЦИЯ. Источник '+source['name']+'; ID '+source['id']+'; страница '+str(request['page'])+'; SHA256 оригинала '+source['sha256']+'. Изображение не подтверждает факт или инженерное принятие.')
        descriptors.append(descriptor);assets.append(dict(asset_id=name,data_base64=base64.b64encode(png).decode('ascii')))
    return descriptors,assets


def checked_assets(record):
    """Validate embedded bytes independently of the surrounding record digest."""
    from PIL import Image
    descriptors=record['content'].get('illustrations',[]);assets=record.get('illustration_assets',[])
    if not isinstance(descriptors,list) or not isinstance(assets,list) or len(descriptors)!=len(assets) or len(assets)>MAX_ILLUSTRATIONS:raise ValueError('Invalid illustration inventory')
    out=[];total=0
    for index,(descriptor,asset) in enumerate(zip(descriptors,assets),1):
        name='illustration-'+str(index)+'.png'
        encoded=asset.get('data_base64')
        if descriptor.get('asset_id')!=name or asset.get('asset_id')!=name or not isinstance(encoded,str) or len(encoded)>4*((MAX_ILLUSTRATION_BYTES+2)//3):raise ValueError('Invalid illustration identity or byte limit')
        try:data=base64.b64decode(encoded,validate=True)
        except Exception:raise ValueError('Invalid embedded illustration') from None
        total+=len(data)
        if not data or len(data)>MAX_ILLUSTRATION_BYTES or total>MAX_TOTAL_ILLUSTRATION_BYTES or hashlib.sha256(data).hexdigest()!=descriptor.get('image_sha256'):raise ValueError('Illustration integrity changed')
        with Image.open(io.BytesIO(data)) as image:
            if image.format!='PNG' or image.size!=(descriptor.get('width'),descriptor.get('height')) or max(image.size)>1600:raise ValueError('Invalid illustration dimensions')
            image.verify()
        out.append((descriptor,data))
    return out


def image_size(descriptor):
    scale=min(468/descriptor['width'],360/descriptor['height'],1)
    return descriptor['width']*scale,descriptor['height']*scale

W='http://schemas.openxmlformats.org/wordprocessingml/2006/main'

def _paragraph(text,style=None):
    properties='<w:pPr><w:pStyle w:val="'+style+'"/></w:pPr>' if style else ''
    runs=''.join('<w:r><w:t xml:space="preserve">'+escape(line)+'</w:t></w:r>'+('<w:r><w:br/></w:r>' if i<len(text.split('\n'))-1 else '') for i,line in enumerate(text.split('\n')))
    return '<w:p>'+properties+runs+'</w:p>'

def _docx(record):
    assets=checked_assets(record)
    c=record['content'];body=_paragraph(c['title'],'Title')+_paragraph(c['label'],'Heading1')
    body+=_paragraph('Версия '+str(record['revision'])+'; SHA256 содержания '+record['content_sha256'])
    for s in c['sections']:
        body+=_paragraph(s['title'],'Heading1')
        body+=''.join(_paragraph(p) for p in s['paragraphs'])
        if s['rows']:
            weights={'sources':[2,3,4],'requirements':[2,5,2,4,3],'facts':[4,2,3]}[s['key']]
            widths=[9360*weight//sum(weights) for weight in weights]
            props='<w:tblPr><w:tblW w:w="9360" w:type="dxa"/><w:tblBorders>'+''.join('<w:'+side+' w:val="single" w:sz="4" w:color="D9D9D9"/>' for side in ('top','left','bottom','right','insideH','insideV'))+'</w:tblBorders><w:tblCellMar><w:top w:w="100" w:type="dxa"/><w:left w:w="100" w:type="dxa"/><w:bottom w:w="100" w:type="dxa"/><w:right w:w="100" w:type="dxa"/></w:tblCellMar></w:tblPr>'
            body+='<w:tbl>'+props+'<w:tblGrid>'+''.join('<w:gridCol w:w="'+str(width)+'"/>' for width in widths)+'</w:tblGrid>'
            for i,row in enumerate([s['headers']]+s['rows']):
                body+='<w:tr>'+('<w:trPr><w:tblHeader/></w:trPr>' if i==0 else '')
                for text,width in zip(row,widths):
                    body+='<w:tc><w:tcPr><w:tcW w:w="'+str(width)+'" w:type="dxa"/><w:vAlign w:val="center"/>'+('<w:shd w:fill="E8EDF2"/>' if i==0 else '')+'</w:tcPr>'+_paragraph(str(text),'TableText')+'</w:tc>'
                body+='</w:tr>'
            body+='</w:tbl>'+_paragraph('')
    if assets:body+=_paragraph('Иллюстрации исходных документов','Heading1')
    for index,(descriptor,data) in enumerate(assets,1):
        width,height=image_size(descriptor);cx,cy=round(width*12700),round(height*12700)
        body+=_paragraph(descriptor['caption'],'Caption')
        body+='<w:p><w:r><w:drawing><wp:inline xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><wp:extent cx="'+str(cx)+'" cy="'+str(cy)+'"/><wp:docPr id="'+str(index)+'" name="'+descriptor['asset_id']+'" descr="'+escape(descriptor['caption'],quote=True)+'"/><a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:pic><pic:nvPicPr><pic:cNvPr id="0" name="'+descriptor['asset_id']+'"/><pic:cNvPicPr/></pic:nvPicPr><pic:blipFill><a:blip r:embed="image'+str(index)+'"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill><pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="'+str(cx)+'" cy="'+str(cy)+'"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r></w:p>'
    body+='<w:sectPr><w:pgSz w:w="12240" w:h="15840"/><w:pgMar w:top="1080" w:right="1440" w:bottom="1080" w:left="1440"/></w:sectPr>'
    document='<?xml version="1.0" encoding="UTF-8"?><w:document xmlns:w="'+W+'"><w:body>'+body+'</w:body></w:document>'
    styles='<w:styles xmlns:w="'+W+'"><w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii="DejaVu Sans" w:hAnsi="DejaVu Sans"/><w:sz w:val="22"/><w:color w:val="000000"/></w:rPr></w:rPrDefault><w:pPrDefault><w:pPr><w:spacing w:after="120"/></w:pPr></w:pPrDefault></w:docDefaults>'
    for name,size in [('Title',36),('Heading1',26),('TableText',18),('Caption',18)]:
        styles+='<w:style w:type="paragraph" w:styleId="'+name+'"><w:name w:val="'+name+'"/><w:pPr>'+('<w:keepNext/>' if name!='TableText' else '')+'</w:pPr><w:rPr><w:sz w:val="'+str(size)+'"/><w:color w:val="000000"/>'+('<w:b/>' if name in {'Title','Heading1'} else '')+'</w:rPr></w:style>'
    styles+='</w:styles>'
    out=io.BytesIO()
    with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml','<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Default Extension="png" ContentType="image/png"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/><Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/></Types>')
        z.writestr('_rels/.rels','<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>')
        relationships=''.join('<Relationship Id="image'+str(i)+'" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/'+d['asset_id']+'"/>' for i,(d,data) in enumerate(assets,1))
        z.writestr('word/_rels/document.xml.rels','<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'+relationships+'</Relationships>')
        z.writestr('word/document.xml',document);z.writestr('word/styles.xml',styles)
        for descriptor,data in assets:z.writestr('word/media/'+descriptor['asset_id'],data)
    return out.getvalue()

def _pdf(record):
    import fitz
    assets=checked_assets(record);archive=fitz.Archive()
    def text(value):
        # Explicit zero-width break opportunities prevent Story from clipping
        # unbreakable UUID/hash tokens and long user words in narrow cells.
        wrapped=re.sub(r'\S{13,}',lambda m:'\u200b'.join(m[0][i:i+12] for i in range(0,len(m[0]),12)),value)
        return escape(wrapped).replace('\n','<br/>')
    c=record['content'];html='<h1>'+text(c['title'])+'</h1><p><b>'+text(c['label'])+'</b></p><p>Версия '+str(record['revision'])+'; SHA256 содержания '+text(record['content_sha256'])+'</p>'
    for s in c['sections']:
        html+='<h2>'+text(s['title'])+'</h2>'
        html+=''.join('<p>'+text(p)+'</p>' for p in s['paragraphs'])
        if s['rows']:
            html+='<table><tr>'+''.join('<th>'+text(h)+'</th>' for h in s['headers'])+'</tr>'
            html+=''.join('<tr>'+''.join('<td>'+text(str(cell))+'</td>' for cell in row)+'</tr>' for row in s['rows'])+'</table>'
    for descriptor,data in assets:
        archive.add(data,descriptor['asset_id']);width,height=image_size(descriptor)
        html+='<div style="page-break-before:always"><h2>Иллюстрации исходных документов</h2><p>'+text(descriptor['caption'])+'</p><img src="'+descriptor['asset_id']+'" width="'+str(round(width))+'" height="'+str(round(height))+'"/></div>'
    story=fitz.Story(html=html,archive=archive,user_css='body { font-family: sans-serif; font-size: 11pt; } h1 {font-size:18pt} h2 {font-size:13pt} table {border-collapse:collapse; font-size:9pt; width:100%} td, th {border:0.5pt solid #d9d9d9; padding:5pt} th {background:#e8edf2}')
    def rectfn(page_num,filled):
        if page_num>=300:raise ValueError('PDF exceeds supported pagination limit')
        page=fitz.Rect(0,0,612,792)
        return page,page+(54,54,-54,-54),None
    with story.write_with_links(rectfn) as pdf:
        normalize=lambda value:re.sub(r'[\s\u200b]+','',unicodedata.normalize('NFKC',value))
        actual=normalize(''.join(page.get_text() for page in pdf))
        expected=[c['title'],c['label'],record['content_sha256']]
        for s in c['sections']:expected.extend([s['title']]+s['paragraphs']+(s['headers'] if s['rows'] else [])+[str(cell) for row in s['rows'] for cell in row])
        expected.extend(descriptor['caption'] for descriptor,data in assets)
        if any(normalize(value) not in actual for value in expected):raise ValueError('PDF text preservation check failed; draft was not exported')
        if sum(len(page.get_image_info()) for page in pdf)<len(assets):raise ValueError('PDF illustration preservation check failed')
        return pdf.tobytes(garbage=3,deflate=True)

def render(record,format):
    if format=='docx':return _docx(record),'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    if format=='pdf':return _pdf(record),'application/pdf'
    raise ValueError('Unsupported draft export')

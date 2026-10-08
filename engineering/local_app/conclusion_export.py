"""Render one checked draft structure into DOCX and PDF. No remote resources."""
import io
from html import escape
import zipfile
import re
import unicodedata

W='http://schemas.openxmlformats.org/wordprocessingml/2006/main'

def _paragraph(text,style=None):
    properties='<w:pPr><w:pStyle w:val="'+style+'"/></w:pPr>' if style else ''
    runs=''.join('<w:r><w:t xml:space="preserve">'+escape(line)+'</w:t></w:r>'+('<w:r><w:br/></w:r>' if i<len(text.split('\n'))-1 else '') for i,line in enumerate(text.split('\n')))
    return '<w:p>'+properties+runs+'</w:p>'

def _docx(record):
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
    body+='<w:sectPr><w:pgSz w:w="12240" w:h="15840"/><w:pgMar w:top="1080" w:right="1440" w:bottom="1080" w:left="1440"/></w:sectPr>'
    document='<?xml version="1.0" encoding="UTF-8"?><w:document xmlns:w="'+W+'"><w:body>'+body+'</w:body></w:document>'
    styles='<w:styles xmlns:w="'+W+'"><w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii="DejaVu Sans" w:hAnsi="DejaVu Sans"/><w:sz w:val="22"/><w:color w:val="000000"/></w:rPr></w:rPrDefault><w:pPrDefault><w:pPr><w:spacing w:after="120"/></w:pPr></w:pPrDefault></w:docDefaults>'
    for name,size in [('Title',36),('Heading1',26),('TableText',18)]:
        styles+='<w:style w:type="paragraph" w:styleId="'+name+'"><w:name w:val="'+name+'"/><w:pPr>'+('<w:keepNext/>' if name!='TableText' else '')+'</w:pPr><w:rPr><w:sz w:val="'+str(size)+'"/><w:color w:val="000000"/>'+('<w:b/>' if name!='TableText' else '')+'</w:rPr></w:style>'
    styles+='</w:styles>'
    out=io.BytesIO()
    with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml','<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/><Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/></Types>')
        z.writestr('_rels/.rels','<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>')
        z.writestr('word/_rels/document.xml.rels','<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/></Relationships>')
        z.writestr('word/document.xml',document);z.writestr('word/styles.xml',styles)
    return out.getvalue()

def _pdf(record):
    import fitz
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
    story=fitz.Story(html=html,user_css='body { font-family: sans-serif; font-size: 11pt; } h1 {font-size:18pt} h2 {font-size:13pt} table {border-collapse:collapse; font-size:9pt; width:100%} td, th {border:0.5pt solid #d9d9d9; padding:5pt} th {background:#e8edf2}')
    def rectfn(page_num,filled):
        if page_num>=300:raise ValueError('PDF exceeds supported pagination limit')
        page=fitz.Rect(0,0,612,792)
        return page,page+(54,54,-54,-54),None
    with story.write_with_links(rectfn) as pdf:
        normalize=lambda value:re.sub(r'[\s\u200b]+','',unicodedata.normalize('NFKC',value))
        actual=normalize(''.join(page.get_text() for page in pdf))
        expected=[c['title'],c['label'],record['content_sha256']]
        for s in c['sections']:expected.extend([s['title']]+s['paragraphs']+(s['headers'] if s['rows'] else [])+[str(cell) for row in s['rows'] for cell in row])
        if any(normalize(value) not in actual for value in expected):raise ValueError('PDF text preservation check failed; draft was not exported')
        return pdf.tobytes(garbage=3,deflate=True)

def render(record,format):
    if format=='docx':return _docx(record),'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    if format=='pdf':return _pdf(record),'application/pdf'
    raise ValueError('Unsupported draft export')

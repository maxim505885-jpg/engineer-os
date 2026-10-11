"""Authenticated source candidate readback does not create accepted evidence."""
import io
import json
import zipfile
import unittest
from tests import test_local_app_http as fixture


class SourceAssetHTTPTests(unittest.TestCase):
    setUp=fixture.LocalHTTPTests.setUp
    close=fixture.LocalHTTPTests.close
    request=fixture.LocalHTTPTests.request
    create=fixture.LocalHTTPTests.create
    def test_docx_candidate_payload_scope_and_identity(self):
        sid=self.create()
        out=io.BytesIO()
        with zipfile.ZipFile(out,'w') as z:
            z.writestr('word/document.xml','<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math"><w:body><m:oMath><m:r><m:t>x+1</m:t></m:r></m:oMath></w:body></w:document>')
            z.writestr('word/media/image.png',b'original-image')
        status,_,raw=self.request('POST',f'/api/sessions/{sid}/files?name=source.docx',out.getvalue(),{'Content-Type':'application/octet-stream'})
        self.assertEqual(status,201);f=json.loads(raw)
        route=f'/api/sessions/{sid}/files/{f["id"]}/assets'
        self.assertEqual(self.request('GET',route,token=False)[0],403)
        status,_,raw=self.request('GET',route)
        self.assertEqual(status,200);inventory=json.loads(raw)
        self.assertEqual(inventory['total'],2);self.assertFalse(inventory['content_verified'])
        image=next(a for a in inventory['items'] if a['asset_kind']=='embedded_image')
        status,headers,payload=self.request('GET',route+'/payload?candidate='+image['candidate_id'])
        self.assertEqual(status,200);self.assertEqual(payload,b'original-image')
        self.assertEqual(headers['X-Source-SHA256'],f['sha256'])
        self.assertEqual(self.request('GET',route.replace(sid,self.create()))[0],400)
        self.assertEqual(self.request('GET',route+'/payload?candidate=unknown')[0],400)
        self.assertEqual(self.store.snapshot(sid)['evidence'],[])
        from pathlib import Path
        Path(self.store.get_file(f['id'])['path']).write_bytes(b'changed')
        self.assertEqual(self.request('GET',route)[0],400)

    def test_pdf_page_is_required_and_cell_payload_is_readable(self):
        import fitz
        pdf=fitz.open();page=pdf.new_page()
        for x in (40,140,240):page.draw_line((x,40),(x,140))
        for y in (40,90,140):page.draw_line((40,y),(240,y))
        for x,y,t in ((50,65,'A'),(150,65,'B'),(50,115,'1'),(150,115,'2')):page.insert_text((x,y),t)
        data=pdf.tobytes();pdf.close();sid=self.create()
        status,_,raw=self.request('POST',f'/api/sessions/{sid}/files?name=table.pdf',data,{'Content-Type':'application/octet-stream'})
        self.assertEqual(status,201);f=json.loads(raw);route=f'/api/sessions/{sid}/files/{f["id"]}/assets'
        self.assertEqual(self.request('GET',route)[0],400)
        status,_,raw=self.request('GET',route+'?page=1');self.assertEqual(status,200)
        item=json.loads(raw)['items'][0]
        status,_,raw=self.request('GET',route+'/payload?page=1&candidate='+item['candidate_id'])
        self.assertEqual(status,200);payload=json.loads(raw)
        self.assertEqual(payload['values'],[['A','B'],['1','2']]);self.assertFalse(payload['content_verified'])

    def test_auxiliary_formula_pagination_and_unsafe_xml_rejection(self):
        from engineering.local_app.source_assets import read_assets
        from engineering.local_app.files import preserve_file
        sid=self.create()
        def archive(xml):
            out=io.BytesIO()
            with zipfile.ZipFile(out,'w') as z:
                z.writestr('word/document.xml','<document/>')
                z.writestr('word/custom/header.xml',xml)
            return out.getvalue()
        f=preserve_file(self.store,sid,'aux.docx',archive('<header xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math"><m:oMath><m:r><m:t>Y</m:t></m:r></m:oMath></header>'))
        result=read_assets(self.store,sid,f['id'],limit=1)
        self.assertEqual(result['items'][0]['location'],'word/custom/header.xml#oMath[0]')
        self.assertEqual(read_assets(self.store,sid,f['id'],offset=1)['items'],[])
        f=preserve_file(self.store,sid,'evil.docx',archive('<!DOCTYPE header [<!ENTITY e "secret">]><header>&e;</header>'))
        with self.assertRaisesRegex(ValueError,'XML entities'):read_assets(self.store,sid,f['id'])
        with self.assertRaisesRegex(ValueError,'pagination'):read_assets(self.store,sid,f['id'],limit=51)

    def test_nested_formula_payloads_obey_aggregate_budget(self):
        from unittest.mock import patch
        from engineering.local_app.source_assets import read_assets
        from engineering.local_app.files import preserve_file
        sid=self.create();out=io.BytesIO()
        xml='<root xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math">'+'<m:oMath>'*40+'<m:t>'+'x'*65536+'</m:t>'+'</m:oMath>'*40+'</root>'
        with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED) as z:z.writestr('word/document.xml',xml)
        f=preserve_file(self.store,sid,'nested.docx',out.getvalue())
        with patch('engineering.local_app.source_assets.MAX_IMAGE_TOTAL_BYTES',1024*1024):
            with self.assertRaisesRegex(ValueError,'size/count'):read_assets(self.store,sid,f['id'])

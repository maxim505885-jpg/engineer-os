"""New document tools retain authentication, source identity and evidence gates."""
import io
import json
import unittest
import zipfile
from unittest.mock import patch
from tests import test_local_app_http as http_fixture


class DocumentToolHTTPTests(unittest.TestCase):
    setUp = http_fixture.LocalHTTPTests.setUp
    close = http_fixture.LocalHTTPTests.close
    request = http_fixture.LocalHTTPTests.request
    create = http_fixture.LocalHTTPTests.create

    def fixture(self):
        from engineering.local_app.files import preserve_file
        out=io.BytesIO()
        with zipfile.ZipFile(out,'w') as z:
            z.writestr('word/document.xml','<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math"><w:body><w:p><m:oMath><m:r><m:t>x+1</m:t></m:r></m:oMath></w:p></w:body></w:document>')
        sid=self.create();f=preserve_file(self.store,sid,'formula.docx',out.getvalue())
        from engineering.local_app.source_assets import read_assets
        item=read_assets(self.store,sid,f['id'])['items'][0]
        return sid,f,item

    def test_tool_inventory_authenticated_and_presence_not_execution(self):
        self.assertEqual(self.request('GET','/api/tooling',token=False)[0],403)
        status,_,raw=self.request('GET','/api/tooling')
        self.assertEqual(status,200)
        data=json.loads(raw)
        self.assertFalse(data['acceptance_granted'])
        self.assertFalse(data['execution_verified'])

    def test_invalid_formula_request_rejected_before_converter(self):
        sid,f,item=self.fixture();route=f'/api/sessions/{sid}/files/{f["id"]}/formula-preview'
        self.assertEqual(self.request('POST',route,{},token=False)[0],403)
        self.assertEqual(self.request('POST',route,{})[0],400)

    def test_formula_exact_candidate_and_project_boundaries(self):
        sid,f,item=self.fixture();route=f'/api/sessions/{sid}/files/{f["id"]}/formula-preview'
        body=dict(part='word/document.xml',ordinal=0,candidate_id=item['candidate_id'],expected_sha256=f['sha256'])
        from PIL import Image
        image=io.BytesIO();Image.new('RGB',(16,16),'white').save(image,format='PNG')
        with patch('engineering.local_app.word_formula_preview.render_formula',return_value=(image.getvalue(),{'status':'UNCERTAINTY'})) as render:
            bad=dict(body,expected_sha256='0'*64)
            self.assertEqual(self.request('POST',route,bad)[0],400);render.assert_not_called()
            bad=dict(body,candidate_id='doc-asset:'+'0'*64)
            self.assertEqual(self.request('POST',route,bad)[0],400);render.assert_not_called()
            other=self.create()
            self.assertEqual(self.request('POST',f'/api/sessions/{other}/files/{f["id"]}/formula-preview',body)[0],400);render.assert_not_called()
            status,_,raw=self.request('POST',route,body)
            self.assertEqual(status,200);result=json.loads(raw)
            self.assertEqual(result['candidate_id'],item['candidate_id'])
            self.assertEqual(result['asset_sha256'],item['asset_sha256'])
            self.assertFalse(result['acceptance_granted']);self.assertFalse(result['mathematics_verified'])
            self.assertFalse(self.store.snapshot(sid)['evidence'])

    def test_tables_scope_and_identity_checked_before_adapter(self):
        from engineering.local_app.files import preserve_file
        import fitz
        doc=fitz.open();doc.new_page();data=doc.tobytes();doc.close()
        sid=self.create();f=preserve_file(self.store,sid,'table.pdf',data)
        body=dict(page=1,bbox=[0,0,100,100],backend='img2table',expected_sha256=f['sha256'])
        route=f'/api/sessions/{sid}/files/{f["id"]}/tables'
        with patch('engineering.local_app.table_readback.read_tables',return_value={'status':'UNAVAILABLE','acceptance_granted':False}) as read:
            self.assertEqual(self.request('POST',route,dict(body,expected_sha256='0'*64))[0],400);read.assert_not_called()
            self.assertEqual(self.request('POST',route,dict(body,backend='other'))[0],400);read.assert_not_called()
            self.assertEqual(self.request('POST',route,body,token=False)[0],403);read.assert_not_called()
            self.assertEqual(self.request('POST',route,body)[0],200);read.assert_called_once()
            self.assertFalse(self.store.snapshot(sid)['evidence'])


if __name__=='__main__':unittest.main()

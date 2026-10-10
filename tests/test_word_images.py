import hashlib
import io
import json
import unittest
from unittest.mock import patch
from PIL import Image
from engineering.local_app import office, preview
from tests.test_office_documents import package, W
from tests import test_office_documents as fixtures

R='http://schemas.openxmlformats.org/officeDocument/2006/relationships'
A='http://schemas.openxmlformats.org/drawingml/2006/main'
REL='http://schemas.openxmlformats.org/package/2006/relationships'


def image_bytes():
    buf=io.BytesIO();Image.new('RGB',(12,8),(180,20,40)).save(buf,format='PNG');return buf.getvalue()


def image_doc(target='media/source.png',mode='',image=None):
    drawing=f'<w:r><w:drawing xmlns:a="{A}" xmlns:r="{R}"><a:blip r:embed="img"/></w:drawing></w:r>'
    return package({'word/document.xml':f'<w:document xmlns:w="{W}"><w:body><w:p><w:r><w:t>Figure context</w:t></w:r>{drawing}</w:p></w:body></w:document>',
                    'word/_rels/document.xml.rels':f'<Relationships xmlns="{REL}"><Relationship Id="img" Type="{R}/image" Target="{target}" {mode}/></Relationships>',
                    'word/media/source.png':image_bytes() if image is None else image})


class ImageReaderTests(unittest.TestCase):
    def test_image_only_paragraph_is_not_silently_dropped(self):
        with __import__('zipfile').ZipFile(io.BytesIO(image_doc())) as z:
            parts={n:z.read(n) for n in z.namelist()}
        parts['word/document.xml']=parts['word/document.xml'].replace(
            b'<w:r><w:t>Figure context</w:t></w:r>',b'')
        units,_=office.read(package(parts),'docx')
        self.assertEqual(len(units),1)
        self.assertEqual(units[0]['locator']['kind'],'paragraph')
        self.assertEqual(units[0]['locator']['images'][0]['part'],'word/media/source.png')
        self.assertIn('IMAGE_CONTENT_NOT_VERIFIED',units[0]['limitations'])
        self.assertFalse(any(u['locator']['kind']=='unsupported_body' for u in units))

    def test_image_is_bound_to_parent_and_exact_original_bytes(self):
        units,limits=office.read(image_doc(),'docx')
        self.assertEqual(len(units),1,'Adding images must preserve logical unit ordinals')
        images=units[0]['locator'].get('images',[])
        self.assertEqual(len(images),1,'Embedded image reference was silently lost')
        self.assertEqual(images[0]['part'],'word/media/source.png')
        self.assertEqual(images[0]['sha256'],hashlib.sha256(image_bytes()).hexdigest())
        self.assertEqual(images[0]['status'],'BOUND_PACKAGE_IMAGE')
        self.assertIn('Figure context',units[0]['text'])
        self.assertIn('IMAGE_CONTENT_NOT_VERIFIED',units[0]['limitations'])
        self.assertIn('LAYOUT_NOT_VERIFIED',limits)

    def test_external_missing_and_wrong_type_images_are_not_bound(self):
        for target,mode in [('https://example.invalid/x','TargetMode="External"'),('media/missing.png','')]:
            units,_=office.read(image_doc(target,mode),'docx')
            self.assertEqual(units[0]['locator'].get('images',[{}])[0].get('status'),'UNAVAILABLE')
        with __import__('zipfile').ZipFile(io.BytesIO(image_doc())) as z:parts={n:z.read(n) for n in z.namelist()}
        parts['word/_rels/document.xml.rels']=parts['word/_rels/document.xml.rels'].replace(b'/image',b'/hyperlink')
        units,_=office.read(package(parts),'docx')
        self.assertEqual(units[0]['locator']['images'][0]['status'],'UNAVAILABLE')

    def test_duplicate_relationship_ids_and_escaping_targets_fail_closed(self):
        with __import__('zipfile').ZipFile(io.BytesIO(image_doc())) as z:parts={n:z.read(n) for n in z.namelist()}
        rel=parts['word/_rels/document.xml.rels'].decode()
        parts['word/_rels/document.xml.rels']=rel.replace('</Relationships>',f'<Relationship Id="img" Type="{R}/image" Target="media/source.png"/></Relationships>')
        with self.assertRaises(office.OfficeError):office.read(package(parts),'docx')
        with self.assertRaises(office.OfficeError):office.read(image_doc('../../escape.png'),'docx')

    def test_image_budgets_reject_before_decompression(self):
        with patch.object(office,'MAX_IMAGE_BYTES',1,create=True),self.assertRaises(office.OfficeError):office.read(image_doc(),'docx')
        with patch.object(office,'MAX_IMAGE_TOTAL_BYTES',1),self.assertRaises(office.OfficeError):office.read(image_doc(),'docx')
        with patch.object(office,'MAX_IMAGE_REFERENCES',0),self.assertRaises(office.OfficeError):office.read(image_doc(),'docx')

    def test_malformed_image_identity_and_uri_escapes_are_rejected(self):
        with __import__('zipfile').ZipFile(io.BytesIO(image_doc())) as z:base={n:z.read(n) for n in z.namelist()}
        for identity in ['bad id','7','','²bad']:
            parts=dict(base)
            parts['word/document.xml']=parts['word/document.xml'].replace(b'embed="img"',f'embed="{identity}"'.encode())
            parts['word/_rels/document.xml.rels']=parts['word/_rels/document.xml.rels'].replace(b'Id="img"',f'Id="{identity}"'.encode())
            with self.subTest(identity=identity),self.assertRaises(office.OfficeError):office.read(package(parts),'docx')
        parts=dict(base);parts['word/_rels/document.xml.rels']=parts['word/_rels/document.xml.rels'].replace(b'source.png',b'bad%ZZ.png')
        parts['word/media/bad%ZZ.png']=image_bytes()
        with self.assertRaises(office.OfficeError):office.read(package(parts),'docx')

    def test_legacy_vml_office_relid_is_bound(self):
        with __import__('zipfile').ZipFile(io.BytesIO(image_doc())) as z:parts={n:z.read(n) for n in z.namelist()}
        drawing='<w:p><w:r><w:pict xmlns:v="urn:schemas-microsoft-com:vml" xmlns:o="urn:schemas-microsoft-com:office:office"><v:shape><v:imagedata o:relid="img"/></v:shape></w:pict></w:r></w:p>'
        parts['word/document.xml']=f'<w:document xmlns:w="{W}"><w:body>{drawing}</w:body></w:document>'
        units,_=office.read(package(parts),'docx')
        self.assertEqual(len(units[0]['locator'].get('images',[])),1)

    def test_equation_does_not_inherit_sibling_image(self):
        with __import__('zipfile').ZipFile(io.BytesIO(image_doc())) as z:parts={n:z.read(n) for n in z.namelist()}
        equation='<m:oMath xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math"><m:r><m:t>42</m:t></m:r></m:oMath>'
        parts['word/document.xml']=parts['word/document.xml'].decode().replace('</w:p>',equation+'</w:p>')
        units,_=office.read(package(parts),'docx')
        self.assertEqual(sum(len(u['locator'].get('images',[])) for u in units),1)
        self.assertNotIn('images',next(u for u in units if u['locator']['kind']=='equation')['locator'])

    def test_table_and_nonstandard_auxiliary_vml_keep_part_specific_relationships(self):
        with __import__('zipfile').ZipFile(io.BytesIO(image_doc())) as z:parts={n:z.read(n) for n in z.namelist()}
        drawing=f'<w:p><w:r><w:pict xmlns:v="urn:schemas-microsoft-com:vml" xmlns:r="{R}"><v:shape><v:imagedata r:id="img"/></v:shape></w:pict></w:r></w:p>'
        table='<w:tbl><w:tblGrid><w:gridCol/></w:tblGrid><w:tr><w:tc>'+drawing+'</w:tc></w:tr></w:tbl>'
        parts['word/document.xml']=f'<w:document xmlns:w="{W}"><w:body>{table}</w:body></w:document>'
        parts['word/_rels/document.xml.rels']=parts['word/_rels/document.xml.rels'].decode().replace('</Relationships>',f'<Relationship Id="hdr" Type="{R}/header" Target="custom/header.xml"/></Relationships>')
        parts['word/custom/header.xml']=f'<w:hdr xmlns:w="{W}">{drawing}</w:hdr>'
        parts['word/custom/_rels/header.xml.rels']=f'<Relationships xmlns="{REL}"><Relationship Id="img" Type="{R}/image" Target="../media/other.png"/></Relationships>'
        parts['word/media/other.png']=b'different image bytes'
        units,_=office.read(package(parts),'docx')
        self.assertEqual(units[0]['locator']['kind'],'table_cell')
        self.assertEqual(units[0]['locator']['images'][0]['part'],'word/media/source.png')
        header=next(u for u in units if u['locator'].get('component')=='header')
        self.assertEqual(header['locator']['images'][0]['part'],'word/media/other.png')
        self.assertEqual(header['locator']['images'][0]['sha256'],hashlib.sha256(b'different image bytes').hexdigest())


class ImagePipelineTests(unittest.TestCase):
    setUp=fixtures.OfficeTests.setUp
    run_doc=fixtures.OfficeTests.run_doc

    def test_image_reference_reaches_receipt_and_preview_without_acceptance(self):
        data=image_doc();file,job,model,result=self.run_doc('images.docx',data)
        self.assertEqual(result['state'],'SUCCEEDED')
        refs=self.store.analysis_receipts(self.session,job['id'])['records'][0]['refs']
        ref=next(r for r in refs if r['locator'].get('images'))
        self.assertIsNone(ref['page'])
        self.assertIn('IMAGE_CONTENT_NOT_VERIFIED',str(model.calls))
        self.assertEqual(result['result']['document_analysis']['sources'][0]['coverage_manifest']['source_components']['image_references'],1)
        renderer=getattr(preview,'render_office_image',None);self.assertIsNotNone(renderer)
        png=renderer(self.store,self.session,ref['source_job'],ref['logical_unit'],1)
        with Image.open(io.BytesIO(png)) as im:self.assertEqual(im.getpixel((0,0)),(180,20,40))
        self.assertFalse(result['result']['acceptance_granted'])
        with self.assertRaises(ValueError):renderer(self.store,self.store.create_session()['id'],ref['source_job'],1,1)
        with self.assertRaises(ValueError):renderer(self.store,self.session,ref['source_job'],1,2)
        from pathlib import Path
        self.assertEqual(Path(self.store.get_file(file['id'])['path']).read_bytes(),data)
        Path(self.store.get_file(file['id'])['path']).write_bytes(b'changed')
        with self.assertRaises(ValueError):renderer(self.store,self.session,ref['source_job'],1,1)

    def test_invalid_raster_and_stale_parser_checkpoint_cannot_preview(self):
        _,job,_,result=self.run_doc('images.docx',image_doc(image=b'<svg/>'))
        ref=self.store.analysis_receipts(self.session,job['id'])['records'][0]['refs'][0]
        with self.assertRaises(ValueError):preview.render_office_image(self.store,self.session,ref['source_job'],1,1)
        _,job,_,_=self.run_doc('images.docx',image_doc())
        ref=self.store.analysis_receipts(self.session,job['id'])['records'][0]['refs'][0]
        with patch('engineering.local_app.source_binding.parser_identity',return_value={}):
            with self.assertRaises(ValueError):preview.render_office_image(self.store,self.session,ref['source_job'],1,1)

    def test_transparent_linework_is_not_flattened_to_opaque_black(self):
        im=Image.new('RGBA',(12,8),(0,0,0,0));im.putpixel((0,0),(0,0,0,255));buf=io.BytesIO();im.save(buf,format='PNG')
        _,job,_,_=self.run_doc('images.docx',image_doc(image=buf.getvalue()))
        ref=self.store.analysis_receipts(self.session,job['id'])['records'][0]['refs'][0]
        png=preview.render_office_image(self.store,self.session,ref['source_job'],1,1)
        with Image.open(io.BytesIO(png)) as result:
            self.assertEqual(result.convert('RGBA').getpixel((0,0)),(0,0,0,255))
            self.assertEqual(result.convert('RGBA').getpixel((1,0)),(0,0,0,0))


class ImageHTTPTests(unittest.TestCase):
    def test_preview_endpoint_requires_session_and_token(self):
        import threading
        from http.client import HTTPConnection
        from tests.test_office_documents import Model
        from engineering.local_app.server import make_server
        from engineering.local_app.files import preserve_file
        from engineering.local_app.worker import Worker
        fixtures.OfficeTests.setUp(self)
        file=preserve_file(self.store,self.session,'images.docx',image_doc())
        job=self.store.enqueue(self.session,'Read',[file['id']]);model=Model();Worker(self.store,model).run_once()
        ref=self.store.analysis_receipts(self.session,job['id'])['records'][0]['refs'][0]
        server=make_server(self.store,model,drive_client=None);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        def request(session,token=True):
            conn=HTTPConnection('127.0.0.1',server.server_port,timeout=5)
            try:
                path=f'/api/sessions/{session}/jobs/{ref["source_job"]}/images?unit=1&image=1'
                conn.request('GET',path,headers={'X-Engineer-Token':server.token} if token else {})
                response=conn.getresponse();return response.status,response.getheader('Content-Type'),response.read()
            finally:conn.close()
        try:
            status,kind,png=request(self.session);self.assertEqual(status,200);self.assertEqual(kind,'image/png');self.assertTrue(png.startswith(b'\x89PNG'))
            self.assertEqual(request(self.session,False)[0],403)
            self.assertEqual(request(self.store.create_session()['id'])[0],400)
        finally:server.shutdown();server.server_close();thread.join()

"""Previously omitted image layers and embedded objects keep exact source bindings."""
import hashlib,unittest
from engineering.local_app import office
from tests.test_office_documents import package,W
from tests.test_word_images import R,A,REL,image_bytes
O='urn:schemas-microsoft-com:office:office'
A14='http://schemas.microsoft.com/office/drawing/2010/main'


def doc(body,relationships,parts=None):
    entries={'word/document.xml':f'<w:document xmlns:w="{W}" xmlns:r="{R}" xmlns:a="{A}" xmlns:a14="{A14}" xmlns:o="{O}"><w:body>{body}</w:body></w:document>',
      'word/_rels/document.xml.rels':f'<Relationships xmlns="{REL}">{relationships}</Relationships>'}
    entries.update(parts or {});return package(entries)


class EmbeddedLayerTests(unittest.TestCase):
    def test_wdp_layer_is_bound_to_same_logical_unit_with_declared_source_kind(self):
        data=doc('<w:p><w:r><w:drawing><a:blip r:embed="img"><a:extLst><a:ext uri="x"><a14:imgLayer r:embed="layer"/></a:ext></a:extLst></a:blip></w:drawing></w:r></w:p>',
          f'<Relationship Id="img" Type="{R}/image" Target="media/base.png"/><Relationship Id="layer" Type="http://schemas.microsoft.com/office/2007/relationships/hdphoto" Target="media/layer.wdp"/>',{'word/media/base.png':image_bytes(),'word/media/layer.wdp':b'layer-bytes'})
        units,_=office.read(data,'docx');self.assertEqual(len(units),1)
        images=units[0]['locator']['images'];self.assertEqual(len(images),2)
        self.assertEqual(images[1]['part'],'word/media/layer.wdp')
        self.assertEqual(images[1]['reference_kind'],'HD_PHOTO_LAYER')
        self.assertEqual(images[1]['sha256'],hashlib.sha256(b'layer-bytes').hexdigest())
        self.assertFalse(images[1]['layout_verified']);self.assertIn('IMAGE_LAYER_COMPOSITION_UNVERIFIED',units[0]['limitations'])

    def test_ole_object_without_preview_is_retained_and_part_hash_bound(self):
        payload=b'compound-object-placeholder'
        data=doc('<w:p><w:r><w:object><o:OLEObject Type="Embed" ProgID="PBrush" ShapeID="s1" r:id="obj"/></w:object></w:r></w:p>',
          f'<Relationship Id="obj" Type="{R}/oleObject" Target="embeddings/object.bin"/>',{'word/embeddings/object.bin':payload})
        units,_=office.read(data,'docx');obj=units[0]['locator']['embedded_objects'][0]
        self.assertEqual(obj['status'],'BOUND_PACKAGE_OBJECT');self.assertEqual(obj['part'],'word/embeddings/object.bin')
        self.assertEqual(obj['sha256'],hashlib.sha256(payload).hexdigest());self.assertEqual(obj['program_id'],'PBrush')
        self.assertIn('EMBEDDED_OBJECT_CONTENT_UNVERIFIED',units[0]['limitations'])
        self.assertFalse(obj['content_verified']);self.assertFalse(obj['executed'])

    def test_external_missing_or_wrong_object_type_is_never_bound(self):
        for attributes,parts in [(f'Type="{R}/oleObject" Target="https://example.invalid/a" TargetMode="External"',{}),
            (f'Type="{R}/oleObject" Target="embeddings/missing.bin"',{}),(f'Type="{R}/hyperlink" Target="embeddings/o.bin"',{'word/embeddings/o.bin':b'x'})]:
            data=doc('<w:p><w:r><w:object><o:OLEObject Type="Embed" r:id="obj"/></w:object></w:r></w:p>',f'<Relationship Id="obj" {attributes}/>',parts)
            units,_=office.read(data,'docx');self.assertEqual(units[0]['locator']['embedded_objects'][0]['status'],'UNAVAILABLE')
            self.assertIn('EMBEDDED_OBJECT_REFERENCE_UNAVAILABLE',units[0]['limitations'])

    def test_object_relationship_traversal_and_budget_fail_closed(self):
        from unittest.mock import patch
        data=doc('<w:p><w:object><o:OLEObject Type="Embed" r:id="obj"/></w:object></w:p>',
          f'<Relationship Id="obj" Type="{R}/oleObject" Target="../../escape.bin"/>')
        with self.assertRaises(office.OfficeError):office.read(data,'docx')
        data=doc('<w:p><w:object><o:OLEObject Type="Embed" r:id="obj"/></w:object></w:p>',
          f'<Relationship Id="obj" Type="{R}/oleObject" Target="embeddings/a.bin"/>',{'word/embeddings/a.bin':b'123'})
        with patch.object(office,'MAX_OBJECT_TOTAL_BYTES',2),self.assertRaises(office.OfficeError):office.read(data,'docx')


class ObjectPipelineTests(unittest.TestCase):
    from tests import test_office_documents as fixtures
    setUp=fixtures.OfficeTests.setUp
    run_doc=fixtures.OfficeTests.run_doc

    def test_object_pixels_reach_source_checkpoint_and_preview_without_acceptance(self):
        import io
        from PIL import Image
        from tests.test_ole_bitmap import compound,bmp
        from engineering.local_app import preview
        payload=compound([('CONTENTS',bmp())])
        data=doc('<w:p><w:object><o:OLEObject Type="Embed" ProgID="PBrush" r:id="obj"/></w:object></w:p>',
          f'<Relationship Id="obj" Type="{R}/oleObject" Target="embeddings/a.bin"/>',{'word/embeddings/a.bin':payload})
        file,job,model,result=self.run_doc('objects.docx',data)
        self.assertEqual(result['state'],'SUCCEEDED')
        refs=self.store.analysis_receipts(self.session,job['id'])['records'][0]['refs']
        ref=next(r for r in refs if r['locator'].get('embedded_objects'))
        obj=ref['locator']['embedded_objects'][0]
        self.assertEqual(obj['bitmap']['status'],'AVAILABLE')
        png=preview.render_office_object(self.store,self.session,ref['source_job'],ref['logical_unit'],1)
        with Image.open(io.BytesIO(png)) as image:self.assertEqual(image.getpixel((0,0)),(255,0,0))
        self.assertIn('EMBEDDED_OBJECT_CONTENT_UNVERIFIED',str(model.calls))
        self.assertFalse(result['result']['acceptance_granted'])
        self.assertEqual(self.store.snapshot(self.session)['evidence'],[])
        with self.assertRaises(ValueError):preview.render_office_object(self.store,self.store.create_session()['id'],ref['source_job'],ref['logical_unit'],1)
        with self.assertRaises(ValueError):preview.render_office_object(self.store,self.session,ref['source_job'],ref['logical_unit'],2)


class CombinedAssetBudgetTests(unittest.TestCase):
    def test_object_before_first_image_cannot_reset_shared_budget(self):
        from unittest.mock import patch
        data=doc('<w:p><w:object><o:OLEObject Type="Embed" r:id="obj"/></w:object></w:p><w:p><w:drawing><a:blip r:embed="img"/></w:drawing></w:p>',
            f'<Relationship Id="obj" Type="{R}/oleObject" Target="embeddings/a.bin"/><Relationship Id="img" Type="{R}/image" Target="media/a.png"/>',
            {'word/embeddings/a.bin':b'123456','word/media/a.png':b'123456'})
        with patch.object(office,'MAX_ASSET_TOTAL_BYTES',10),self.assertRaisesRegex(office.OfficeError,'byte limit'):
            office.read(data,'docx')

    def test_image_and_object_use_separate_bounded_budgets(self):
        from unittest.mock import patch
        data=doc('<w:p><w:object><o:OLEObject Type="Embed" r:id="obj"/></w:object><w:drawing><a:blip r:embed="img"/></w:drawing></w:p>',
            f'<Relationship Id="obj" Type="{R}/oleObject" Target="embeddings/a.bin"/><Relationship Id="img" Type="{R}/image" Target="media/a.png"/>',
            {'word/embeddings/a.bin':b'123456','word/media/a.png':b'123456'})
        with patch.object(office,'MAX_IMAGE_TOTAL_BYTES',6),patch.object(office,'MAX_OBJECT_TOTAL_BYTES',6),patch.object(office,'MAX_ASSET_TOTAL_BYTES',12):
            units,_=office.read(data,'docx');self.assertEqual(len(units[0]['locator']['embedded_objects']),1)
        with patch.object(office,'MAX_OBJECT_TOTAL_BYTES',5),self.assertRaises(office.OfficeError):office.read(data,'docx')
        with patch.object(office,'MAX_IMAGE_TOTAL_BYTES',5),self.assertRaises(office.OfficeError):office.read(data,'docx')

import unittest
from engineering.local_app import office
from tests.test_word_embedded_layers import doc
from tests.test_word_images import R,image_bytes
REL=f'<Relationship Id="img" Type="{R}/image" Target="media/base.png"/><Relationship Id="layer" Type="http://schemas.microsoft.com/office/2007/relationships/hdphoto" Target="media/layer.wdp"/>'
PARTS={'word/media/base.png':image_bytes(),'word/media/layer.wdp':b'original'}
class LayerPairTests(unittest.TestCase):
    def read(self,body):return office.read(doc('<w:p><w:r><w:drawing>'+body+'</w:drawing></w:r></w:p>',REL,PARTS),'docx')[0][0]['locator']['images'][-1]
    def test_ancestor_cached_bitmap_and_ordered_declared_effects(self):
        item=self.read('<a:blip r:embed="img"><a:extLst><a:ext uri="wrapper"><a14:imgLayer r:embed="layer"><a14:imgEffect name="first"><a14:brightnessContrast bright="10"/></a14:imgEffect><a14:imgEffect name="second"><a14:sharpenSoften amount="1"/></a14:imgEffect></a14:imgLayer></a:ext></a:extLst></a:blip>')
        self.assertEqual(item.get('cached_bitmap_association_status'),'BOUND_ANCESTOR_BLIP')
        self.assertEqual(item['cached_processed_bitmap']['part'],'word/media/base.png')
        self.assertEqual([e['attributes']['name'] for e in item['declared_effects']],['first','second'])
        self.assertIn('brightnessContrast',item['declared_effects'][0]['normalized_xml'])
        self.assertFalse(item['effects_applied']);self.assertFalse(item['render_verified'])
    def test_sibling_never_associates_and_ambiguous_original_or_parent_unavailable(self):
        for body,reason in [('<a:blip r:embed="img"/><a14:imgLayer r:embed="layer"/>','ANCESTOR_BLIP_MISSING'),('<a:blip r:embed="img" r:link="img"><a14:imgLayer r:embed="layer"/></a:blip>','ANCESTOR_BLIP_AMBIGUOUS_IDENTITY'),('<a:blip r:embed="img"><a14:imgLayer r:embed="layer" r:link="img"/></a:blip>','LAYER_AMBIGUOUS_IDENTITY')]:
            with self.subTest(reason=reason):
                item=self.read(body);self.assertEqual(item.get('cached_bitmap_association_status'),'UNAVAILABLE');self.assertEqual(item['cached_bitmap_association_reason'],reason)
    def test_missing_linked_parent_and_effect_budget_fail_closed(self):
        from unittest.mock import patch
        from engineering.local_app import word_images
        for attrs,reason in [('r:link="img"','ANCESTOR_BLIP_LINKED_IMAGE'),('r:embed="missing"','IMAGE_RELATIONSHIP_MISSING_OR_WRONG_TYPE')]:
            item=self.read(f'<a:blip {attrs}><a14:imgLayer r:embed="layer"/></a:blip>')
            self.assertEqual(item['cached_bitmap_association_reason'],reason)
        with patch.object(word_images,'MAX_EFFECT_XML_BYTES',0),self.assertRaises(office.OfficeError):
            self.read('<a:blip r:embed="img"><a14:imgLayer r:embed="layer"><a14:imgEffect><a14:sharpenSoften amount="1"/></a14:imgEffect></a14:imgLayer></a:blip>')

import unittest
from engineering.local_app.office import read
from tests.test_office_documents import docx
class PrivateUseGlyphTests(unittest.TestCase):
    def test_private_use_codes_preserved_and_marked_unverified(self):
        for glyph in ['\uf061','\U000f0001','\U00100001']:
            text='Source '+glyph+' = 25'
            units,_=read(docx(text),'docx');item=next(u for u in units if u['text']==text)
            with self.subTest(code=hex(ord(glyph))):
                self.assertIn('PRIVATE_USE_GLYPH_UNVERIFIED',item['limitations'])
                self.assertEqual(item['text'],text)
    def test_standard_unicode_greek_is_not_relabelled(self):
        text='Source α = 25';units,_=read(docx(text),'docx');item=next(u for u in units if u['text']==text)
        self.assertNotIn('PRIVATE_USE_GLYPH_UNVERIFIED',item['limitations'])
if __name__=='__main__':unittest.main()

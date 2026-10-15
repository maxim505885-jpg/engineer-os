import tempfile
import unittest
from pathlib import Path
from scripts.pdf_layer_census import inventory

class PDFLayerCensusTests(unittest.TestCase):
    def test_native_and_image_only_pages_are_distinguished(self):
        import fitz
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'sample.pdf'
            document=fitz.open()
            first=document.new_page()
            first.insert_text((30,60),'Native text')
            document.new_page()
            document.save(path)
            document.close()
            result=inventory(path)
            self.assertEqual(result['page_count'],2)
            self.assertEqual(result['native_empty_pages'],[2])
            self.assertGreater(result['pages'][0]['native_text_chars'],0)
            self.assertFalse(result['visual_content_verified'])
            self.assertEqual(len(result['pages']),2)

if __name__=='__main__':
    unittest.main()

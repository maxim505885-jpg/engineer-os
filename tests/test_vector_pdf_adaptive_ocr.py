import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from scripts.vector_pdf_ocr_review import collect


class AdaptiveOCRFallbackTests(unittest.TestCase):
    def test_one_failed_subtile_remains_partial_not_verified(self):
        import fitz
        with tempfile.TemporaryDirectory() as directory:
            source=Path(directory)/'vector.pdf'
            document=fitz.open()
            page=document.new_page()
            shape=page.new_shape()
            shape.draw_line((10,10),(100,10))
            shape.finish(color=(0,0,0))
            shape.commit()
            document.save(source)
            document.close()
            calls=[0]
            def OCR(*args,**kwargs):
                calls[0]+=1
                if calls[0]==1 or calls[0]==2:
                    raise RuntimeError('timeout')
                return dict(text=['Опора'],conf=['90'],left=[4],top=[4],width=[20],height=[10])
            fake=SimpleNamespace(Output=SimpleNamespace(DICT=dict),image_to_data=OCR)
            with patch.dict('sys.modules',{'pytesseract':fake}):
                result=collect(source,[1])
            record=result['records'][0]
            self.assertTrue(record['ocr_failures'])
            self.assertEqual(record['ocr_failures'][0]['reason'],'FALLBACK_SUBTILES_FAILED')
            self.assertTrue(record['candidates'])
            self.assertFalse(record['visual_verified'])
            self.assertTrue(all(x['status']=='OCR_CANDIDATE_UNVERIFIED' for x in record['candidates']))


if __name__=='__main__':
    unittest.main()

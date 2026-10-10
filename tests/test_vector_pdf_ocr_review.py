import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.vector_pdf_ocr_review import collect


class VectorOCRReviewTests(unittest.TestCase):
    def test_native_text_page_rejected_before_ocr(self):
        import fitz
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)/'native.pdf'
            pdf=fitz.open()
            page=pdf.new_page()
            page.insert_text((25,30),'Ordinary text')
            pdf.save(source)
            pdf.close()
            with self.assertRaisesRegex(ValueError,'Expected vector-only'):
                collect(source,[1])

    def test_vector_candidate_is_never_accepted_as_verified(self):
        import fitz
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)/'vector.pdf'
            pdf=fitz.open()
            page=pdf.new_page()
            shape=page.new_shape()
            shape.draw_line((20,30),(120,30))
            shape.finish(color=(0,0,0))
            shape.commit()
            pdf.save(source)
            pdf.close()
            fake=dict(text=['Label','noise'],conf=['72','-1'],
                      left=[10,20],top=[15,18],width=[50,20],height=[12,12])
            with patch('pytesseract.image_to_data',return_value=fake):
                result=collect(source,[1])
            self.assertEqual(result['quality_status'],'VISUAL_REVIEW_REQUIRED')
            self.assertEqual(len(result['records'][0]['candidates']),1)
            self.assertFalse(result['records'][0]['visual_verified'])
            self.assertEqual(result['records'][0]['candidates'][0]['status'],'OCR_CANDIDATE_UNVERIFIED')


if __name__=='__main__':
    unittest.main()

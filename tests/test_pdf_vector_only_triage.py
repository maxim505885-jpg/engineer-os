import tempfile
import unittest
from pathlib import Path
from scripts.pdf_vector_only_triage import triage


class PDFVectorOnlyTriageTests(unittest.TestCase):
    def test_vector_without_native_text_is_not_equated_with_raster_scan(self):
        import fitz
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'drawing.pdf'
            pdf=fitz.open()
            page=pdf.new_page()
            shape=page.new_shape()
            shape.draw_line((20,30),(250,30))
            shape.finish(color=(0,0,0))
            shape.commit()
            page2=pdf.new_page()
            page2.insert_text((25,50),'hello')
            pdf.save(path)
            pdf.close()
            result=triage(path,1,2)
            self.assertEqual(result['vector_only_pages'],[1])
            self.assertGreater(result['rows'][0]['vector_paths'],0)
            self.assertFalse(result['rows'][0]['semantic_content_verified'])
            self.assertFalse(result['visual_ocr_and_drawing_semantics_verified'])

if __name__=='__main__':
    unittest.main()

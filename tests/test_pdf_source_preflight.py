import hashlib
import importlib.util
import tempfile
import unittest
from pathlib import Path


@unittest.skipUnless(importlib.util.find_spec('fitz'), 'optional PDF review dependency absent')
class PdfSourcePreflightTests(unittest.TestCase):
    def test_rotated_pages_use_the_native_geometry_coordinate_system(self):
        import fitz
        from scripts.pdf_source_preflight import inspect_source
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'rotated.pdf'
            with fitz.open() as pdf:
                page = pdf.new_page(width=595, height=842)
                page.insert_text((60, 650), 'Visible native body text')
                page.set_rotation(90)
                pdf.save(path)
            result = inspect_source(path)
        self.assertEqual(result['pages'][0]['source_kind'], 'NATIVE_TEXT')
        self.assertEqual(result['pages'][0]['native_body_words'], 4)

    def test_native_scan_and_outlined_drawing_receive_distinct_routes(self):
        import fitz
        from scripts.pdf_source_preflight import inspect_source
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'source.pdf'
            with fitz.open() as pdf:
                page = pdf.new_page(width=200, height=300)
                page.insert_text((20, 40), 'Native body text')
                page = pdf.new_page(width=200, height=300)
                image = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 100, 140), False)
                image.clear_with(255)
                page.insert_image(fitz.Rect(20, 20, 190, 250), pixmap=image)
                page = pdf.new_page(width=200, height=300)
                page.draw_rect(fitz.Rect(20, 20, 180, 200))
                page.draw_line((20, 80), (180, 80))
                pdf.save(path)
            sha = hashlib.sha256(path.read_bytes()).hexdigest()
            result = inspect_source(path, expected_sha256=sha)
        self.assertEqual(result['source_sha256'], sha)
        self.assertEqual([p['source_page'] for p in result['pages']], [1, 2, 3])
        self.assertEqual([p['source_kind'] for p in result['pages']],
                         ['NATIVE_TEXT', 'RASTER', 'VECTOR_WITHOUT_NATIVE_TEXT'])
        self.assertEqual(result['pages'][1]['low_resolution_images'], 1)
        self.assertEqual(result['pages'][2]['recommended_route'], 'VECTOR_VISUAL_REVIEW')
        self.assertFalse(result['complete_document'])
        self.assertFalse(result['acceptance_granted'])
        self.assertEqual(result['document_status'], 'BLOCK')

    def test_wrong_source_digest_is_rejected_before_inspection(self):
        from scripts.pdf_source_preflight import inspect_source
        with tempfile.NamedTemporaryFile() as handle:
            handle.write(b'not a PDF'); handle.flush()
            with self.assertRaisesRegex(ValueError, 'source checksum mismatch'):
                inspect_source(Path(handle.name), expected_sha256='0' * 64)

    def test_requested_pages_preserve_original_numbers_and_reject_bad_scope(self):
        import fitz
        from scripts.pdf_source_preflight import inspect_source
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'source.pdf'
            with fitz.open() as pdf:
                pdf.new_page(); pdf.new_page(); pdf.save(path)
            result = inspect_source(path, pages=[2])
            self.assertEqual([p['source_page'] for p in result['pages']], [2])
            with self.assertRaisesRegex(ValueError, 'invalid source pages'):
                inspect_source(path, pages=[0, 3])


if __name__ == '__main__':
    unittest.main()

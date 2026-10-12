"""Reading an unrotated page must not invoke a metadata rewrite."""
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import fitz
from engineering.local_app import ocr, region_readback, table_worker


class ReadOnlyRotationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.source = Path(self.temp.name)/'source.pdf'
        with fitz.open() as doc:
            doc.new_page(width=200,height=200).insert_text((40,50),'Height 4 metres')
            doc.save(self.source)
        self.raw = self.source.read_bytes()
        self.sha = hashlib.sha256(self.raw).hexdigest()

    def test_region_native_readback_never_rewrites_zero_rotation(self):
        original = fitz.Page.set_rotation
        with patch.object(fitz.Page,'set_rotation',autospec=True,side_effect=original) as rewrite:
            result = region_readback.recognize(self.source,1,[20,20,180,100],self.sha)
        self.assertEqual(rewrite.call_count,0)
        self.assertIn('Height',result['native_blocks'][0]['text'])
        self.assertEqual(self.source.read_bytes(),self.raw)

    def test_ocr_render_does_not_dirty_unrotated_document(self):
        # Only recognition is controlled; the PDF open, render and mutation state
        # are real. A readback fixture must work without optional language models.
        with fitz.open(self.source) as doc:
            self.assertFalse(doc.is_dirty)
            with patch.object(ocr,'_paths',return_value=(None,None)):
                parser = ocr.TesseractOCR()
            with patch.object(parser,'_recognize',return_value=b'level\ttext\n'):
                parser.page_blocks(doc[0],1,bbox=[20,20,180,100])
            self.assertFalse(doc.is_dirty)
        self.assertEqual(self.source.read_bytes(),self.raw)

    def test_table_source_raster_never_rewrites_zero_rotation(self):
        request = dict(source=str(self.source),source_sha256=self.sha,page=1,
                       bbox=[20,20,180,100],backend='img2table',unavailable_reason='TABLE_DEPENDENCIES_UNAVAILABLE')
        original = fitz.Page.set_rotation
        with patch.object(fitz.Page,'set_rotation',autospec=True,side_effect=original) as rewrite:
            result = table_worker.execute(request)
        self.assertEqual(rewrite.call_count,0)
        self.assertEqual(result['status'],'UNAVAILABLE')
        self.assertTrue(result['raster']['png_sha256'])
        self.assertEqual(self.source.read_bytes(),self.raw)

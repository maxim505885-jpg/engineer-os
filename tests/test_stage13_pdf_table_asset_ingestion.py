import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from engineering.document_intelligence.pdf_table_asset_ingestion import pdf_table_candidates
from engineering.document_intelligence.asset_provenance import verify_payload

class PDFTableAssetTests(unittest.TestCase):
    def test_table_candidate_has_validated_bytes_not_verified_meaning(self):
        import fitz
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'table.pdf'
            doc=fitz.open()
            page=doc.new_page(width=420,height=420)
            shape=page.new_shape()
            for x in (30,140,250):
                shape.draw_line((x,50),(x,160))
            for y in (50,105,160):
                shape.draw_line((30,y),(250,y))
            shape.finish(color=(0,0,0))
            shape.commit()
            page.insert_text((45,80),'A1')
            page.insert_text((155,80),'B1')
            page.insert_text((45,135),'A2')
            page.insert_text((155,135),'B2')
            doc.save(path)
            doc.close()
            pairs=pdf_table_candidates(path,[1])
            self.assertGreaterEqual(len(pairs),1)
            for candidate,payload in pairs:
                self.assertEqual(candidate.asset_kind,'table_cells')
                self.assertIn('bbox=',candidate.location)
                self.assertEqual(candidate.page_number,1)
                self.assertEqual(candidate.source_sha256,hashlib.sha256(path.read_bytes()).hexdigest())
                self.assertFalse(candidate.verified)
                self.assertTrue(verify_payload(candidate,payload,candidate.source_sha256))
                self.assertIsInstance(json.loads(payload),list)

    def test_invalid_page_rejected(self):
        import fitz
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'t.pdf'
            doc=fitz.open()
            doc.new_page()
            doc.save(path)
            doc.close()
            with self.assertRaisesRegex(ValueError,'INVALID_PAGE_NUMBER'):
                pdf_table_candidates(path,[2])

if __name__=='__main__':
    unittest.main()

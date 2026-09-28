import json
import tempfile
import unittest
from pathlib import Path

from scripts.run_v4_local import DOCUMENT_ID, PROJECT_ID, SOURCE_SHA256
from scripts.v4_blocked_review import render_report


class BlockedReviewTests(unittest.TestCase):
    def test_inventory_links_to_pdf_and_escapes_failed_audit_details(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary) / "check"
            directory.mkdir()
            audit = {"source_sha256": SOURCE_SHA256, "project_id": PROJECT_ID,
                     "document_id": DOCUMENT_ID, "page_start": 500, "page_end": 500,
                     "stderr": 'Traceback\nDocumentParseError: <script>alert(1)</script>'}
            (directory / "pages-0500-0500.audit.json").write_text(json.dumps(audit))
            result = {"source_sha256": SOURCE_SHA256, "page_count": 534,
                      "blocked_reasons": {"MERGED_TABLE_CELL": [500]}, "status": "BLOCK"}
            html = render_report(result, directory, directory.parent / "v4-drive-source.pdf")
            self.assertIn('../v4-drive-source.pdf#page=500', html)
            self.assertIn('MERGED_TABLE_CELL', html)
            self.assertIn('&lt;script&gt;alert(1)&lt;/script&gt;', html)
            self.assertNotIn('<script>alert(1)</script>', html)
            self.assertIn('BLOCK', html)


if __name__ == "__main__":
    unittest.main()

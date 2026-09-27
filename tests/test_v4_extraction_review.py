import json
import tempfile
import unittest
from pathlib import Path

from scripts.local_docling_batch import CHECK_VERSION
from scripts.run_v4_local import DOCUMENT_ID, PROJECT_ID, SOURCE_SHA256
from scripts.v4_extraction_review import review


class ExtractionReviewTests(unittest.TestCase):
    def test_reports_missing_chunk_and_page_without_blocks(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            base = {"source_sha256": SOURCE_SHA256, "project_id": PROJECT_ID,
                    "document_id": DOCUMENT_ID, "page_start": 1, "page_end": 2}
            audit = dict(base, check_version=CHECK_VERSION, exit_code=0)
            output = dict(base, status="UNCERTAINTY", blocks=[
                {"block_id": "docling:1", "kind": "table_row", "text": "A",
                 "provenance": [{"page_no": 1, "bbox": None}]},
            ])
            (root / "pages-0001-0002.audit.json").write_text(json.dumps(audit))
            (root / "pages-0001-0002.json").write_text(json.dumps(output))
            result = review(root, 4)
            self.assertEqual(result["successful_chunks"], 1)
            self.assertEqual(result["blocked_chunks"], 1)
            self.assertEqual(result["pages_without_extracted_blocks"], [2])
            self.assertEqual(result["issues"][0]["chunk"], "pages-0003-0004")
            self.assertEqual([item["page"] for item in result["review_queue"]], [3, 4, 2, 1])
            self.assertEqual(result["review_queue"][-1]["reason"], "TABLE_REQUIRES_VISUAL_REVIEW")
            self.assertEqual(result["status"], "BLOCK")


if __name__ == "__main__":
    unittest.main()

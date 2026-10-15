import json
import tempfile
import unittest
from pathlib import Path

from scripts.local_docling_batch import CHECK_VERSION
from scripts.run_v4_local import DOCUMENT_ID, PROJECT_ID, SOURCE_SHA256
from scripts.v4_extraction_review import review


class ExtractionReviewTests(unittest.TestCase):
    def test_successful_pair_with_one_unlocated_page_remains_blocked(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            base=dict(source_sha256=SOURCE_SHA256,project_id=PROJECT_ID,
                      document_id=DOCUMENT_ID,page_start=1,page_end=2)
            (root/'pages-0001-0002.audit.json').write_text(json.dumps(dict(base,check_version=CHECK_VERSION,exit_code=0)))
            (root/'pages-0001-0002.json').write_text(json.dumps(dict(base,status='UNCERTAINTY',blocks=[
                dict(block_id='one',kind='text',text='page one',provenance=[{'page_no':1}]) ])))
            result=review(root,2)
            self.assertEqual(result['blocked_chunks'],0)
            self.assertEqual(result['status'],'BLOCK')
            self.assertEqual(result['pages_without_extracted_blocks'],[2])

    def test_pre_header_gate_cache_is_not_counted_as_current_extraction(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            base = {"source_sha256": SOURCE_SHA256, "project_id": PROJECT_ID,
                    "document_id": DOCUMENT_ID, "page_start": 1, "page_end": 1}
            audit = dict(base, check_version=4, exit_code=0)
            output = dict(base, status="UNCERTAINTY", blocks=[
                {"block_id": "docling:1", "kind": "table_row", "text": "old inferred heading",
                 "provenance": [{"page_no": 1}]}])
            (root / "pages-0001-0001.audit.json").write_text(json.dumps(audit))
            (root / "pages-0001-0001.json").write_text(json.dumps(output))
            result = review(root, 1)
            self.assertEqual(result["successful_chunks"], 0)
            self.assertEqual(result["status"], "BLOCK")

    def test_version_five_false_header_cache_is_not_current(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            base = {"source_sha256": SOURCE_SHA256, "project_id": PROJECT_ID,
                    "document_id": DOCUMENT_ID, "page_start": 1, "page_end": 1}
            audit = dict(base, check_version=5, exit_code=0)
            output = dict(base, status="UNCERTAINTY", blocks=[
                {"block_id": "docling:1", "kind": "table_row", "text": "old inferred heading",
                 "provenance": [{"page_no": 1}]}])
            (root / "pages-0001-0001.audit.json").write_text(json.dumps(audit))
            (root / "pages-0001-0001.json").write_text(json.dumps(output))
            result = review(root, 1)
            self.assertEqual(result["successful_chunks"], 0)
            self.assertEqual(result["status"], "BLOCK")

    def test_version_six_pre_stamp_fix_cache_is_not_current(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            base = {"source_sha256": SOURCE_SHA256, "project_id": PROJECT_ID,
                    "document_id": DOCUMENT_ID, "page_start": 1, "page_end": 1}
            audit = dict(base, check_version=6, exit_code=0)
            output = dict(base, status="UNCERTAINTY", blocks=[
                {"block_id": "docling:1", "kind": "table_row", "text": "old inferred heading",
                 "provenance": [{"page_no": 1}]}])
            (root / "pages-0001-0001.audit.json").write_text(json.dumps(audit))
            (root / "pages-0001-0001.json").write_text(json.dumps(output))
            result = review(root, 1)
            self.assertEqual(result["successful_chunks"], 0)
            self.assertEqual(result["status"], "BLOCK")

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
            self.assertEqual(result["blocked_chunks"], 2)
            self.assertEqual(result["pages_without_extracted_blocks"], [2])
            self.assertEqual(result["issues"][0]["chunk"], "pages-0003-0003")
            self.assertEqual([item["page"] for item in result["review_queue"]], [3, 4, 2, 1])
            self.assertEqual(result["review_queue"][-1]["reason"], "TABLE_REQUIRES_VISUAL_REVIEW")
            self.assertEqual(result["status"], "BLOCK")

    def test_failed_pair_preserves_healthy_isolated_page(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            base = {"source_sha256": SOURCE_SHA256, "project_id": PROJECT_ID,
                    "document_id": DOCUMENT_ID, "page_start": 499, "page_end": 499}
            audit = dict(base, check_version=CHECK_VERSION, exit_code=0)
            output = dict(base, status="UNCERTAINTY", blocks=[
                {"block_id": "docling:1", "kind": "text", "text": "Page 499",
                 "provenance": [{"page_no": 499, "bbox": None}]},
            ])
            (root / "pages-0499-0499.audit.json").write_text(json.dumps(audit))
            (root / "pages-0499-0499.json").write_text(json.dumps(output))
            result = review(root, 500)
            self.assertIn(499, result["isolated_pages"])
            self.assertEqual(result["review_queue"][0]["page"], 1)
            self.assertEqual(result["review_queue"][-1]["page"], 499)
            self.assertIn(500, [item["page"] for item in result["review_queue"] if item["priority"] == 1])


if __name__ == "__main__":
    unittest.main()

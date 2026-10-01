import json
import tempfile
import unittest
from pathlib import Path

from scripts.local_docling_batch import CHECK_VERSION
from scripts.retry_v4_footer_stamps import FOOTER_PAGES, retry
from scripts.run_v4_local import DOCUMENT_ID, PROJECT_ID, SOURCE_SHA256


class FooterRetryTests(unittest.TestCase):
    def test_retries_only_confirmed_footer_failures_and_leaves_other_blocks(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            identity = dict(source_sha256=SOURCE_SHA256, project_id=PROJECT_ID,
                            document_id=DOCUMENT_ID)
            for page in (*FOOTER_PAGES, 57):
                data = dict(identity, check_version=CHECK_VERSION, exit_code=1,
                            page_start=page, page_end=page,
                            stderr="table dimensions are invalid" if page != 57 else
                                   "table caption lacks verified table rows")
                (directory / f"pages-{page:04d}-{page:04d}.audit.json").write_text(json.dumps(data))
            calls = []

            def run(args, first, last):
                calls.append(first)
                audit = dict(identity, check_version=CHECK_VERSION, exit_code=0,
                             page_start=first, page_end=last)
                output = dict(identity, page_start=first, page_end=last, status="UNCERTAINTY",
                              blocks=[{"text": "Body", "kind": "text",
                                       "provenance": [{"page_no": first}]}])
                stem = f"pages-{first:04d}-{last:04d}"
                (directory / f"{stem}.audit.json").write_text(json.dumps(audit))
                (directory / f"{stem}.json").write_text(json.dumps(output))
                return 0

            result = retry(directory, source=Path("unused"), run=run)
            self.assertEqual(calls, list(FOOTER_PAGES))
            self.assertIn(57, result["blocked_reasons"]["OTHER_EXTRACTION_FAILURE"])
            self.assertTrue(all(page not in result["blocked_reasons"].get("OTHER_EXTRACTION_FAILURE", [])
                                for page in FOOTER_PAGES))

    def test_refuses_mismatched_audit_before_any_retry(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            for page in FOOTER_PAGES:
                (directory / f"pages-{page:04d}-{page:04d}.audit.json").write_text(json.dumps({
                    "source_sha256": SOURCE_SHA256, "project_id": PROJECT_ID,
                    "document_id": DOCUMENT_ID, "page_start": page, "page_end": page,
                    "stderr": "table dimensions are invalid" if page != 254 else "other failure"}))
            calls = []
            with self.assertRaises(ValueError):
                retry(directory, source=Path("unused"), run=lambda *args: calls.append(args))
            self.assertEqual(calls, [])


if __name__ == "__main__":
    unittest.main()

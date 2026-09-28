import json
import tempfile
import unittest
from pathlib import Path

from scripts.local_docling_batch import CHECK_VERSION
from scripts.retry_v4_legacy import retry_legacy
from scripts.run_v4_local import DOCUMENT_ID, PROJECT_ID, SOURCE_SHA256


class RetryLegacyTests(unittest.TestCase):
    def test_retries_only_old_ambiguous_audit_pages(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            metadata = {"source_sha256": SOURCE_SHA256, "project_id": PROJECT_ID,
                        "document_id": DOCUMENT_ID, "check_version": CHECK_VERSION,
                        "exit_code": 1}
            for page, error in ((1, "table cell is missing, merged or ambiguous"),
                                (2, "table grid has missing cells")):
                data = dict(metadata, page_start=page, page_end=page, stderr=error)
                (directory / f"pages-{page:04d}-{page:04d}.audit.json").write_text(json.dumps(data))
            calls = []

            def run(args, first, last):
                calls.append((first, last))
                data = dict(metadata, page_start=first, page_end=last,
                            stderr="table page 1 table 0 merged cell row 11 col 0")
                (directory / f"pages-{first:04d}-{last:04d}.audit.json").write_text(json.dumps(data))
                return 2

            count, result = retry_legacy(directory, 2, run=run)
            self.assertEqual(count, 1)
            self.assertEqual(calls, [(1, 1)])
            self.assertEqual(result["blocked_reasons"],
                             {"MERGED_TABLE_CELL": [1], "MISSING_TABLE_CELLS": [2]})
            self.assertEqual(result["status"], "BLOCK")


if __name__ == "__main__":
    unittest.main()

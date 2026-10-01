import hashlib
import json
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path

from scripts.v4_full_region_export import collect


class FullRegionExportTests(unittest.TestCase):
    def test_resumes_only_source_bound_pages_and_retries_failures(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.pdf"
            source.write_bytes(b"document")
            digest = hashlib.sha256(b"document").hexdigest()
            review = root / "review.json"
            review.write_text(json.dumps({"source_sha256": digest, "status": "BLOCK",
                "page_count": 3, "blocked_reasons": {"MERGED_TABLE_CELL": [1, 2]}}))
            cache = root / "cache"
            calls = []

            def run(command, **kwargs):
                page = int(command[command.index("--page") + 1])
                calls.append(page)
                if page == 2 and len(calls) == 2:
                    return subprocess.CompletedProcess(command, 1, "", "conversion failed")
                Path(command[command.index("--output") + 1]).write_text(json.dumps({
                    "source_sha256": digest, "page_start": page, "page_end": page,
                    "tables": [], "text_blocks": [{"text": "body", "provenance": [{"page_no": page}]}]}))
                return subprocess.CompletedProcess(command, 0, "ok", "")

            target = root / "bundle.zip"
            first = collect(source, review, target, cache, runner=run)
            self.assertEqual([p["page"] for p in first["failed_pages"]], [2])
            second = collect(source, review, target, cache, runner=run)
            self.assertEqual(calls, [1, 2, 2])
            self.assertEqual(second["reused_pages"], [1])
            self.assertEqual(len(second["exported_pages"]), 2)
            with zipfile.ZipFile(target) as archive:
                self.assertEqual(sorted(archive.namelist()),
                                 ["manifest.json", "page-0001.json", "page-0002.json"])
            cached = cache / "page-0001.json"
            data = json.loads(cached.read_text())
            data["text_blocks"][0]["provenance"][0]["page_no"] = 3
            cached.write_text(json.dumps(data))
            collect(source, review, target, cache, runner=run)
            self.assertEqual(calls, [1, 2, 2, 1])


if __name__ == "__main__":
    unittest.main()

import hashlib
import json
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path

from scripts.v4_region_probe import collect


class RegionProbeTests(unittest.TestCase):
    def test_collects_only_source_bound_outputs_and_records_failures(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.pdf"
            source.write_bytes(b"test source")
            digest = hashlib.sha256(source.read_bytes()).hexdigest()
            review = root / "review.json"
            review.write_text(json.dumps({"source_sha256": digest, "status": "BLOCK",
                                          "blocked_reasons": {"MERGED_TABLE_CELL": [1],
                                                              "OTHER_EXTRACTION_FAILURE": [2]}}))

            def run(command, **kwargs):
                page = int(command[command.index("--page") + 1])
                if page == 2:
                    return subprocess.CompletedProcess(command, 2, "", "conversion failed")
                output = Path(command[command.index("--output") + 1])
                output.write_text(json.dumps({"source_sha256": digest, "page_start": page,
                                              "page_end": page, "tables": [],
                                              "text_blocks": [{"kind": "caption", "text": "Table 1",
                                                               "provenance": [{"page_no": page}]}]}))
                return subprocess.CompletedProcess(command, 0, "ok", "")

            target = root / "probe.zip"
            manifest = collect(source, review, target, pages=(1, 2), runner=run)
            self.assertEqual(manifest["status"], "BLOCK")
            self.assertEqual(manifest["failed_pages"], [{"page": 2, "error": "conversion failed"}])
            with zipfile.ZipFile(target) as archive:
                self.assertEqual(sorted(archive.namelist()), ["manifest.json", "page-0001.json"])
                self.assertEqual(json.loads(archive.read("page-0001.json"))["text_blocks"][0]["text"],
                                 "Table 1")

    def test_rejects_source_mismatch_before_running_converter(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.pdf"
            source.write_bytes(b"wrong")
            review = root / "review.json"
            review.write_text(json.dumps({"source_sha256": "different", "status": "BLOCK",
                                          "blocked_reasons": {"MERGED_TABLE_CELL": [1]}}))
            with self.assertRaisesRegex(ValueError, "SHA-256"):
                collect(source, review, root / "probe.zip", pages=(1,),
                        runner=lambda *args, **kwargs: self.fail("converter called"))
            self.assertFalse((root / "probe.zip").exists())


if __name__ == "__main__":
    unittest.main()

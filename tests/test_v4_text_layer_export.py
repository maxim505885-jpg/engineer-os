import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.v4_text_layer_export import export


class TextLayerExportTests(unittest.TestCase):
    def test_exports_only_blocked_pages_bound_to_source(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source.pdf"
            source.write_bytes(b"source")
            digest = hashlib.sha256(source.read_bytes()).hexdigest()
            review = root / "review.json"
            review.write_text(json.dumps({"source_sha256": digest, "page_count": 3,
                                          "status": "BLOCK", "blocked_reasons": {
                                              "MERGED_TABLE_CELL": [1, 3]}}))
            def run(*args, **kwargs):
                return subprocess.CompletedProcess(args, 0, "Таблица 1\fignored\f\f", "")
            output = root / "out"
            result = export(source, review, output, runner=run)
            self.assertEqual(result["status"], "BLOCK")
            self.assertEqual([e["page"] for e in result["pages"]], [1, 3])
            self.assertEqual((output / "page-0001.txt").read_text(), "Таблица 1")
            self.assertEqual((output / "page-0003.txt").read_text(), "")
            self.assertFalse((output / "page-0002.txt").exists())
            self.assertEqual(result["pages"][1]["route"], "NO_TEXT_LAYER")

    def test_rejects_mismatched_source_before_export(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source.pdf"
            source.write_bytes(b"source")
            review = root / "review.json"
            review.write_text(json.dumps({"source_sha256": "0" * 64,
                                          "page_count": 1, "status": "BLOCK",
                                          "blocked_reasons": {"MERGED_TABLE_CELL": [1]}}))
            output = root / "out"
            with self.assertRaisesRegex(ValueError, "SHA-256"):
                export(source, review, output, runner=lambda *a, **k: self.fail("ran"))
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()

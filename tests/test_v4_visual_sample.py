import hashlib
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from reportlab.pdfgen import canvas

from scripts.v4_visual_sample import export_batches


class VisualBatchTests(unittest.TestCase):
    def test_exports_remaining_blocked_pages_once_with_source_identity(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source.pdf"
            pdf = canvas.Canvas(str(source))
            for page in range(1, 7):
                pdf.drawString(50, 50, f"Page {page}")
                pdf.showPage()
            pdf.save()
            digest = hashlib.sha256(source.read_bytes()).hexdigest()
            review = root / "review.json"
            review.write_text(json.dumps({"source_sha256": digest, "page_count": 6,
                                          "blocked_reasons": {"MERGED_TABLE_CELL": [1, 2, 5],
                                                              "MISSING_TABLE_CELLS": [4, 6]},
                                          "status": "BLOCK"}))

            paths = export_batches(source, review, root / "out", batch_size=2, exclude=(2,))

            self.assertEqual([p.name for p in paths], ["v4-blocked-001.zip", "v4-blocked-002.zip"])
            for path, expected in zip(paths, ([1, 4], [5, 6])):
                with zipfile.ZipFile(path) as archive:
                    manifest = json.loads(archive.read("manifest.json"))
                    self.assertEqual(manifest["source_sha256"], digest)
                    self.assertEqual(manifest["status"], "BLOCK")
                    self.assertEqual([entry["page"] for entry in manifest["sample"]], expected)
                    self.assertEqual(sorted(archive.namelist()),
                                     ["manifest.json", *[f"page-{p:04d}.png" for p in expected]])

    def test_source_mismatch_leaves_no_partial_archives(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source.pdf"
            source.write_bytes(b"wrong")
            review = root / "review.json"
            review.write_text(json.dumps({"source_sha256": "expected", "page_count": 1,
                                          "blocked_reasons": {"MERGED_TABLE_CELL": [1]},
                                          "status": "BLOCK"}))
            with self.assertRaisesRegex(ValueError, "SHA-256"):
                export_batches(source, review, root / "out")
            self.assertFalse((root / "out").exists())


if __name__ == "__main__":
    unittest.main()

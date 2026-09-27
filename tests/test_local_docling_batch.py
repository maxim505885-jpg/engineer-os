import unittest
import json
import tempfile
from pathlib import Path

from scripts.local_docling_batch import ranges, reusable_output


class LocalDoclingBatchTests(unittest.TestCase):
    def test_ranges_are_bounded_and_cover_each_page_once(self):
        self.assertEqual(list(ranges(11, 16, 2)), [(11, 12), (13, 14), (15, 16)])
        with self.assertRaises(ValueError):
            list(ranges(1, 534, 2))

    def test_resume_rejects_corrupted_or_misbound_chunk(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "pages-0015-0016.json"
            expected = dict(first=15, last=16, sha256="a" * 64,
                            project_id="project", document_id="document")
            payload = {"page_start": 15, "page_end": 16,
                       "source_sha256": "a" * 64, "project_id": "project",
                       "document_id": "document", "status": "UNCERTAINTY",
                       "blocks": [{"text": "sample", "provenance": [{"page_no": 15}]}]}
            path.write_text(json.dumps(payload), encoding="utf-8")
            self.assertTrue(reusable_output(path, **expected))
            payload["blocks"][0]["provenance"][0]["page_no"] = 17
            path.write_text(json.dumps(payload), encoding="utf-8")
            self.assertFalse(reusable_output(path, **expected))
            path.write_text("{bad", encoding="utf-8")
            self.assertFalse(reusable_output(path, **expected))


if __name__ == "__main__":
    unittest.main()

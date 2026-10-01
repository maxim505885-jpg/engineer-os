import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.v4_offline_table_candidates import collect


class Table:
    def __init__(self, bbox, grid):
        self.bbox = bbox
        self._grid = grid
        self.rows = grid
        self.columns = grid[0]

    def extract(self):
        return self._grid


class Page:
    width, height = 595, 842

    def find_tables(self):
        return [Table((10, 10, 580, 827), [["frame", "stamp"]] * 3),
                Table((55, 30, 530, 300), [["6", "load"], ["7", "load"]])]


class Pdf:
    pages = [Page()]

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False


class OfflineCandidateTests(unittest.TestCase):
    def test_frame_is_excluded_and_numbered_data_remains_blocked(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "source.pdf"
            source.write_bytes(b"source")
            review = {"source_sha256": hashlib.sha256(b"source").hexdigest(),
                      "status": "BLOCK", "page_count": 1,
                      "blocked_reasons": {"MERGED_TABLE_CELL": [1]}}
            with patch("scripts.v4_offline_table_candidates.pdfplumber.open", return_value=Pdf()):
                result = collect(source, review)
                self.assertEqual((result["page_count"], result["candidate_tables"]), (1, 1))
                self.assertTrue(result["pages"][0]["candidates"][0]["first_row_is_numbered_data"])
                self.assertEqual(result["pages"][0]["page_status"], "BLOCK")
                review["source_sha256"] = "bad"
                with self.assertRaisesRegex(ValueError, "identity"):
                    collect(source, review)


if __name__ == "__main__":
    unittest.main()

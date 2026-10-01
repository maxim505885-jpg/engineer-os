import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.v4_load_continuation import recover


class LoadContinuationTests(unittest.TestCase):
    def test_complete_continuation_requires_independent_cell_match(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.pdf"
            source.write_bytes(b"source")
            sha = hashlib.sha256(b"source").hexdigest()
            review = {"source_sha256": sha, "status": "BLOCK", "isolated_pages": [254]}
            ids = [str(n) for n in range(6, 16)] + [f"{n} (S)" for n in range(16, 20)]
            grid = [[n, "Load", "Type", "0,5", "1,2"] for n in ids]
            cells = [{"text": value, "start_row_offset_idx": r,
                      "end_row_offset_idx": r + 1, "start_col_offset_idx": c,
                      "end_col_offset_idx": c + 1}
                     for r, row in enumerate(grid) for c, value in enumerate(row)]
            exported = {"source_sha256": sha, "page_start": 254, "page_end": 254,
                        "tables": [{"num_rows": 14, "num_cols": 5,
                                    "provenance": [{"page_no": 254}], "cells": cells}]}

            class Page:
                def __init__(self, tables):
                    self.tables = tables

                def extract_tables(self):
                    return self.tables

            class Pdf:
                def __init__(self):
                    self.pages = [Page([]) for _ in range(534)]
                    self.pages[252] = Page([[['№', 'Load', 'Type', 'Share', 'Factor']]
                                            + [['', '', '', '', ''] for _ in range(5)]])
                    self.pages[253] = Page([grid])

                def __enter__(self):
                    return self

                def __exit__(self, *_):
                    return False

            pdf = Pdf()
            with patch("scripts.v4_load_continuation.pdfplumber.open", return_value=pdf):
                result = recover(source, review, exported)
                self.assertEqual(result["page_status"], "UNCERTAINTY")
                self.assertEqual(len(result["rows"]), 14)
                cells[1]["text"] = "altered"
                with self.assertRaisesRegex(ValueError, "disagree"):
                    recover(source, review, exported)
                cells[1]["text"] = "Load"
                cells.pop()
                with self.assertRaisesRegex(ValueError, "missing cells"):
                    recover(source, review, exported)


if __name__ == "__main__":
    unittest.main()

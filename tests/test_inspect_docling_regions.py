import unittest

from scripts.inspect_docling_tables import text_blocks


class InspectorRegionsTests(unittest.TestCase):
    def test_preserves_caption_and_page_provenance_without_unbound_cell_text(self):
        exported = {"texts": [{"label": "caption", "text": "Таблица 1", "prov": [{"page_no": 57}]},
                              {"label": "text", "text": "Body", "prov": [{"page_no": 57}]}],
                    "tables": [{"data": {"table_cells": [{"text": "unbound cell"}]}}]}
        self.assertEqual(text_blocks(exported), [
            {"kind": "caption", "text": "Таблица 1", "provenance": [{"page_no": 57}]},
            {"kind": "text", "text": "Body", "provenance": [{"page_no": 57}]},
        ])


if __name__ == "__main__":
    unittest.main()

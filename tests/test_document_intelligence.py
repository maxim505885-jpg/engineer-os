import os
import tempfile
import unittest
from unittest.mock import patch

from engineering.document_intelligence import DoclingDocumentParser, DocumentParseError


class _FakeDocument:
    def __init__(self, payload):
        self.payload = payload

    def export_to_dict(self):
        return self.payload


class _FakeResult:
    def __init__(self, payload):
        self.document = _FakeDocument(payload)


class _FakeConverter:
    def __init__(self, payload):
        self.payload = payload

    def convert(self, source):
        return _FakeResult(self.payload)


class DocumentIntelligenceTests(unittest.TestCase):
    def test_unknown_table_mode_is_rejected(self):
        with self.assertRaises(ValueError):
            DoclingDocumentParser(table_mode="unknown")

    def _source(self):
        handle = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        handle.write(b"synthetic engineering fixture")
        handle.close()
        self.addCleanup(lambda: os.path.exists(handle.name) and os.unlink(handle.name))
        return handle.name

    def test_disabled_is_fail_closed(self):
        source = self._source()
        with patch.dict(os.environ, {"ENGINEER_OS_DOCUMENT_INTELLIGENCE": "false"}):
            with self.assertRaises(DocumentParseError):
                DoclingDocumentParser(lambda: _FakeConverter({})).parse(source)

    def test_normalizes_text_and_provenance(self):
        source = self._source()
        payload = {
            "texts": [
                {
                    "label": "section_header",
                    "text": "3. Результаты обследования",
                    "prov": [{"page_no": 12, "bbox": {"l": 10, "t": 20, "r": 300, "b": 60}}],
                },
                {"label": "text", "text": "Доказательный фрагмент", "prov": [{"page_no": 12}]},
            ]
        }
        parser = DoclingDocumentParser(lambda: _FakeConverter(payload))
        with patch.dict(os.environ, {"ENGINEER_OS_DOCUMENT_INTELLIGENCE": "true"}):
            document = parser.parse(source)

        self.assertEqual(document.parser, "docling")
        self.assertEqual(len(document.source_sha256), 64)
        self.assertEqual(len(document.blocks), 2)
        self.assertEqual(document.blocks[0].provenance[0].page_no, 12)
        self.assertEqual(document.blocks[0].provenance[0].bbox.left, 10.0)

    def test_empty_conversion_is_rejected(self):
        source = self._source()
        parser = DoclingDocumentParser(lambda: _FakeConverter({"texts": []}))
        with patch.dict(os.environ, {"ENGINEER_OS_DOCUMENT_INTELLIGENCE": "true"}):
            with self.assertRaises(DocumentParseError):
                parser.parse(source)

    def test_unlocated_nested_text_is_not_emitted_as_evidence_block(self):
        source = self._source()
        payload = {"texts": [{"text": "Located", "prov": [{"page_no": 2}]},
                             {"text": "Unlocated table cell"}]}
        with patch.dict(os.environ, {"ENGINEER_OS_DOCUMENT_INTELLIGENCE": "true"}):
            document = DoclingDocumentParser(lambda: _FakeConverter(payload)).parse(source)
        self.assertEqual([(b.text, b.provenance[0].page_no) for b in document.blocks], [("Located", 2)])

    def test_only_unlocated_text_is_rejected(self):
        source = self._source()
        with patch.dict(os.environ, {"ENGINEER_OS_DOCUMENT_INTELLIGENCE": "true"}):
            with self.assertRaises(DocumentParseError):
                DoclingDocumentParser(lambda: _FakeConverter({"texts": [{"text": "Unlocated"}]})).parse(source)

    def test_table_caption_without_verified_cells_blocks_chunk(self):
        source = self._source()
        payload = {"texts": [{"label": "caption", "text": "Табл. П.2.1.", "prov": [{"page_no": 15}]}]}
        with patch.dict(os.environ, {"ENGINEER_OS_DOCUMENT_INTELLIGENCE": "true"}):
            with self.assertRaisesRegex(DocumentParseError, "table"):
                DoclingDocumentParser(lambda: _FakeConverter(payload)).parse(source)

    def test_exported_table_with_empty_cells_blocks_chunk(self):
        source = self._source()
        payload = {"texts": [{"text": "Text", "prov": [{"page_no": 15}]}], "tables": [{"data": {"table_cells": []}}]}
        with patch.dict(os.environ, {"ENGINEER_OS_DOCUMENT_INTELLIGENCE": "true"}):
            with self.assertRaisesRegex(DocumentParseError, "table"):
                DoclingDocumentParser(lambda: _FakeConverter(payload)).parse(source)

    def test_complete_table_uses_parent_page_and_preserves_row_meaning(self):
        source = self._source()
        cells = []
        for row, values in enumerate((("Параметр", "Значение", "Обоснование"),
                                      ("Вес снегового покрова", "0,50 кПа", "СП 131"))):
            for col, value in enumerate(values):
                cells.append({"text": value, "start_row_offset_idx": row,
                              "end_row_offset_idx": row + 1, "start_col_offset_idx": col,
                              "end_col_offset_idx": col + 1})
        payload = {"texts": [{"label": "caption", "text": "Табл. П.2.1.",
                              "prov": [{"page_no": 15}]}],
                   "tables": [{"prov": [{"page_no": 15}], "data": {
                       "num_rows": 2, "num_cols": 3, "table_cells": cells}}]}
        with patch.dict(os.environ, {"ENGINEER_OS_DOCUMENT_INTELLIGENCE": "true"}):
            result = DoclingDocumentParser(lambda: _FakeConverter(payload)).parse(source)
        rows = [block for block in result.blocks if block.kind == "table_row"]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].provenance[0].page_no, 15)
        self.assertIn("Вес снегового покрова", rows[0].text)
        self.assertIn("Значение: 0,50 кПа", rows[0].text)
        self.assertIn("Обоснование: СП 131", rows[0].text)

    def test_incomplete_table_grid_is_blocked(self):
        source = self._source()
        payload = {"tables": [{"prov": [{"page_no": 15}], "data": {
            "num_rows": 2, "num_cols": 2, "table_cells": [
                {"text": "Header", "start_row_offset_idx": 0,
                 "end_row_offset_idx": 1, "start_col_offset_idx": 0,
                 "end_col_offset_idx": 1}]}}]}
        with patch.dict(os.environ, {"ENGINEER_OS_DOCUMENT_INTELLIGENCE": "true"}):
            with self.assertRaisesRegex(DocumentParseError, "missing cells"):
                DoclingDocumentParser(lambda: _FakeConverter(payload)).parse(source)

    def test_merged_figure_legend_identifies_page_and_cell_without_accepting_it(self):
        source = self._source()
        payload = {"texts": [{"text": "Рисунок Ж.9", "prov": [{"page_no": 500}]}],
                   "tables": [{"prov": [{"page_no": 500}], "data": {
                       "num_rows": 14, "num_cols": 3, "table_cells": [
                           {"text": "Лист", "start_row_offset_idx": 11,
                            "end_row_offset_idx": 12, "start_col_offset_idx": 0,
                            "end_col_offset_idx": 3}]}}]}
        with patch.dict(os.environ, {"ENGINEER_OS_DOCUMENT_INTELLIGENCE": "true"}):
            with self.assertRaisesRegex(DocumentParseError, r"page 500.*table 0.*merged.*row 11.*col 0"):
                DoclingDocumentParser(lambda: _FakeConverter(payload)).parse(source)

    def test_bottom_title_stamp_is_excluded_without_blocking_real_table(self):
        stamp = {"prov": [{"page_no": 16, "bbox": {
            "l": 44, "t": 60, "r": 580, "b": 15, "coord_origin": "BOTTOMLEFT"}}],
            "data": {"num_rows": 3, "num_cols": 7, "table_cells": [
                {"text": label} for label in (
                    "Изм.", "Кол.уч", "№ док. Лист", "Подп.", "Дата",
                    "ОСК-ССК-22/0526-1", "Лист", "16") ]}}
        source = self._source()
        payload = {"texts": [{"text": "Body", "prov": [{"page_no": 16}]}],
                   "tables": [stamp]}
        with patch.dict(os.environ, {"ENGINEER_OS_DOCUMENT_INTELLIGENCE": "true"}):
            result = DoclingDocumentParser(lambda: _FakeConverter(payload)).parse(source)
        self.assertEqual([b.text for b in result.blocks], ["Body"])

    def test_missing_source_is_rejected(self):
        with patch.dict(os.environ, {"ENGINEER_OS_DOCUMENT_INTELLIGENCE": "true"}):
            with self.assertRaises(DocumentParseError):
                DoclingDocumentParser(lambda: _FakeConverter({})).parse("/missing/report.pdf")


if __name__ == "__main__":
    unittest.main()

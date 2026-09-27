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

    def test_exported_table_without_cell_provenance_blocks_chunk(self):
        source = self._source()
        payload = {"texts": [{"text": "Text", "prov": [{"page_no": 15}]}], "tables": [{"data": {"table_cells": []}}]}
        with patch.dict(os.environ, {"ENGINEER_OS_DOCUMENT_INTELLIGENCE": "true"}):
            with self.assertRaisesRegex(DocumentParseError, "table"):
                DoclingDocumentParser(lambda: _FakeConverter(payload)).parse(source)

    def test_missing_source_is_rejected(self):
        with patch.dict(os.environ, {"ENGINEER_OS_DOCUMENT_INTELLIGENCE": "true"}):
            with self.assertRaises(DocumentParseError):
                DoclingDocumentParser(lambda: _FakeConverter({})).parse("/missing/report.pdf")


if __name__ == "__main__":
    unittest.main()

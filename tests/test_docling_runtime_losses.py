"""Parser loss diagnostics must follow every caller, including the local worker."""
import logging
import tempfile
import threading
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from engineering.document_intelligence.contracts import DocumentParseError
from engineering.document_intelligence.docling_adapter import DoclingDocumentParser


class DoclingRuntimeLossTests(unittest.TestCase):
    def parse(self, convert):
        with tempfile.TemporaryDirectory() as directory:
            source=Path(directory)/'source.pdf'
            source.write_bytes(b'synthetic source')
            parser=DoclingDocumentParser(lambda:SimpleNamespace(convert=convert))
            with patch.dict('os.environ',{'ENGINEER_OS_DOCUMENT_INTELLIGENCE':'true'}):
                return parser.parse(str(source),page_range=(1,1))

    @staticmethod
    def result():
        return SimpleNamespace(document=SimpleNamespace(export_to_dict=lambda:dict(
            texts=[dict(text='candidate',prov=[dict(page_no=1)])])))

    def test_table_loss_warning_is_a_parser_limitation_without_cli(self):
        def convert(*a,**k):
            logging.getLogger('docling.test').warning(
                '3 pdf cells matched neither a row nor a column band and were dropped from the table PRIVATE_SOURCE')
            return self.result()
        document=self.parse(convert)
        self.assertIn('TABLE_CELLS_DROPPED_BY_LAYOUT_PARSER',document.limitations)
        self.assertNotIn('PRIVATE_SOURCE',repr(document.limitations))
        self.assertEqual(document.blocks[0].text,'candidate')

    def test_unrelated_warning_does_not_invent_table_loss(self):
        def convert(*a,**k):
            logging.getLogger('docling.test').warning('other diagnostic')
            return self.result()
        self.assertEqual(self.parse(convert).limitations,())

    def test_table_loss_from_pipeline_worker_thread_is_retained(self):
        def convert(*a,**k):
            worker=threading.Thread(target=lambda:logging.getLogger('docling.pipeline').warning(
                'pdf cells matched neither a row nor a column band; dropped from the table'))
            worker.start();worker.join()
            return self.result()
        self.assertIn('TABLE_CELLS_DROPPED_BY_LAYOUT_PARSER',self.parse(convert).limitations)

    def test_source_change_during_conversion_is_rejected(self):
        def convert(path,**k):
            Path(path).write_bytes(b'changed source')
            return self.result()
        with self.assertRaisesRegex(DocumentParseError,'source changed during conversion'):
            self.parse(convert)

    def test_warning_handler_is_removed_after_conversion_failure(self):
        before=list(logging.getLogger().handlers)
        def convert(*a,**k):raise RuntimeError('synthetic failure')
        with self.assertRaises(DocumentParseError):self.parse(convert)
        self.assertEqual(logging.getLogger().handlers,before)

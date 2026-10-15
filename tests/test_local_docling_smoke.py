import logging
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from scripts.local_docling_smoke import _TableLossMonitor, main


class TableLossMonitorTests(unittest.TestCase):
    def test_captures_table_cell_loss_warning(self):
        monitor = _TableLossMonitor()
        logger = logging.getLogger()
        logger.addHandler(monitor)
        try:
            logging.getLogger("MatchingPostProcessor").warning(
                "15 of 229 pdf cells matched neither a row nor a column band of the 46x7 grid and were dropped from the table"
            )
        finally:
            logger.removeHandler(monitor)
        self.assertEqual(len(monitor.messages), 1)

    def test_partial_text_is_written_as_block_without_acceptance(self):
        from engineering.document_intelligence import DoclingDocumentParser
        from engineering.document_intelligence.contracts import DocumentBlock, NormalizedDocument, PageRef
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);source=root/'source.pdf';source.write_bytes(b'original')
            output=root/'partial.json';sha=hashlib.sha256(b'original').hexdigest()
            document=NormalizedDocument(str(source),'docling',(
                DocumentBlock('text-1','text','Observed source text',(PageRef(1),)),),sha,
                limitations=('TABLE_CAPTION_WITHOUT_VERIFIED_ROWS',))
            argv=['smoke',str(source),'--start','1','--end','1','--sha256',sha,
                  '--project-id','project','--document-id','document','--output-json',str(output)]
            with patch.object(sys,'argv',argv),patch.object(DoclingDocumentParser,'parse',return_value=document):
                self.assertEqual(main(),0)
            result=json.loads(output.read_text(encoding='utf-8'))
            self.assertEqual(result['status'],'BLOCK')
            self.assertEqual(result['blocks'][0]['text'],'Observed source text')
            self.assertEqual(result['limitations'],['TABLE_CAPTION_WITHOUT_VERIFIED_ROWS'])
            self.assertEqual(result['evidentiary_status'],'NOT_EVIDENCE')
            self.assertFalse(result['complete_document']);self.assertFalse(result['acceptance_granted'])


if __name__ == "__main__":
    unittest.main()

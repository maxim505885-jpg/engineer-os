import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace

from engineering.document_intelligence.contracts import DocumentParseError
from engineering.local_app.files import preserve_file
from engineering.local_app.store import Store
from engineering.local_app.worker import Worker


class ParseDiagnosticsTests(unittest.TestCase):
    def run_error(self,error):
        import fitz
        from engineering.local_app import extraction
        with tempfile.TemporaryDirectory() as tmp:
            store=Store(Path(tmp));sid=store.create_session()['id']
            with fitz.open() as doc:
                doc.new_page();data=doc.tobytes()
            f=preserve_file(store,sid,'scan.pdf',data)
            job=store.enqueue_extraction(sid,f['id'],'docling')
            def parse(*args,**kwargs):raise error
            with patch.object(extraction,'docling_parser',return_value=SimpleNamespace(parse=parse)):
                Worker(store,None).run_once()
            return store.extraction_page(sid,job['id'],1),store.snapshot(sid)

    def test_known_table_ambiguity_is_explained_without_removing_block(self):
        page,state=self.run_error(DocumentParseError('table cell is missing, merged or ambiguous'))
        self.assertTrue(any('TABLE_STRUCTURE_UNVERIFIED' in x for x in page['limitations']))
        self.assertEqual(page['status'],'BLOCK');self.assertEqual(page['execution'],'FAILED')
        self.assertEqual(page['blocks'],[]);self.assertFalse(page['acceptance_granted'])

    def test_arbitrary_parser_text_is_never_exposed_as_diagnostic(self):
        for error in [RuntimeError('PRIVATE_SECRET'),DocumentParseError('table cell is missing, merged or ambiguous PRIVATE_SECRET')]:
            with self.subTest(error=type(error).__name__):
                page,state=self.run_error(error)
                self.assertNotIn('PRIVATE_SECRET',json.dumps(state))
                self.assertNotIn('PRIVATE_SECRET',json.dumps(page))
                self.assertTrue(any('PARSE_FAILED' in x for x in page['limitations']))


if __name__=='__main__':unittest.main()

"""Coverage must disclose missing native text, limits and unknown legacy data."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from engineering.local_app.files import preserve_file
from engineering.local_app.store import Store
from engineering.local_app.worker import Worker


class LocalExtractionCoverageTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.store=Store(Path(self.tmp.name));self.session=self.store.create_session()['id']

    def pdf(self,pages):
        import fitz
        with fitz.open() as doc:
            for text in pages:
                p=doc.new_page()
                if text:p.insert_text((30,40),text)
            return doc.tobytes()

    def coverage(self,file):
        self.assertIn('extraction_coverage',file,'Preview must disclose actual coverage')
        return file['extraction_coverage']

    def test_pdf_page_limit_records_missing_text_without_claiming_completeness(self):
        data=self.pdf(['height 4m','']+['more text']*21)
        f=preserve_file(self.store,self.session,'report.pdf',data);c=self.coverage(f)
        self.assertEqual(c['total_pages'],23);self.assertEqual(c['attempted_pages'],20)
        self.assertEqual(c['pages_with_text'],19);self.assertEqual(c['pages_without_text'],[2])
        self.assertEqual(c['unattempted_pages'],3);self.assertIn('PAGE_LIMIT',c['stop_reasons'])
        self.assertEqual(c['completeness'],'NOT_CHECKED');self.assertFalse(f['acceptance_granted'])
        self.assertEqual(c['page_records'][1]['status'],'NO_NATIVE_TEXT')
        self.assertEqual(Store(self.store.root).snapshot(self.session)['files'][0]['extraction_coverage'],c)
        self.assertEqual(Path(self.store.get_file(f['id'])['path']).read_bytes(),data)

    def test_character_limit_records_partial_page_and_true_attempted_count(self):
        data=self.pdf(['A'*60,'B'*60,'C'])
        with patch('engineering.local_app.files.MAX_TEXT',45):
            f=preserve_file(self.store,self.session,'long.pdf',data)
        c=self.coverage(f)
        self.assertEqual(c['attempted_pages'],1);self.assertEqual(c['unattempted_pages'],2)
        self.assertEqual(c['page_records'][0]['status'],'PARTIAL_TEXT')
        self.assertIn('CHAR_LIMIT',c['stop_reasons']);self.assertTrue(f['text_truncated'])
        self.assertEqual(len(self.store.get_file(f['id'])['text']),45)

    def test_all_pages_with_text_are_still_unverified_native_preview(self):
        f=preserve_file(self.store,self.session,'native.pdf',self.pdf(['1 2 3','native']))
        c=self.coverage(f)
        self.assertEqual(c['unattempted_pages'],0);self.assertEqual(c['pages_without_text'],[])
        self.assertEqual(c['stop_reasons'],[]);self.assertEqual(c['completeness'],'NOT_CHECKED')
        self.assertEqual(c['ocr'],'NOT_RUN');self.assertEqual(f['extraction_status'],'UNVERIFIED')

    def test_empty_native_pages_are_unavailable_not_successful_reading(self):
        f=preserve_file(self.store,self.session,'scan.pdf',self.pdf(['','']))
        c=self.coverage(f)
        self.assertEqual(c['attempted_pages'],2);self.assertEqual(c['pages_without_text'],[1,2])
        self.assertEqual(c['pages_with_text'],0);self.assertEqual(f['extraction_status'],'UNAVAILABLE')

    def test_discarded_whitespace_preview_does_not_report_stored_page_text(self):
        f=preserve_file(self.store,self.session,'blank.pdf',self.pdf(['   ']))
        c=self.coverage(f)
        self.assertEqual(self.store.get_file(f['id'])['text'],'')
        self.assertEqual(c['stored_chars'],0)
        self.assertEqual(c['page_records'][0]['stored_chars'],0)
        self.assertEqual(c['page_records'][0]['status'],'NO_NATIVE_TEXT')

    def test_invalid_pdf_and_utf8_keep_original_with_unknown_coverage(self):
        for name,data in [('broken.pdf',b'invalid'),('bad.txt',b'\xff')]:
            f=preserve_file(self.store,self.session,name,data);c=self.coverage(f)
            self.assertEqual(c['status'],'UNKNOWN');self.assertIn('EXTRACTION_UNAVAILABLE',c['stop_reasons'])
            self.assertIsNone(c['total_pages']);self.assertEqual(f['extraction_status'],'UNAVAILABLE')
            self.assertEqual(Path(self.store.get_file(f['id'])['path']).read_bytes(),data)

    def test_utf8_character_coverage_is_not_pdf_page_coverage(self):
        with patch('engineering.local_app.files.MAX_TEXT',5):
            f=preserve_file(self.store,self.session,'text.md','Привет мир'.encode())
        c=self.coverage(f)
        self.assertEqual(c['method'],'UTF8');self.assertIsNone(c['total_pages'])
        self.assertEqual(c['source_chars'],10);self.assertEqual(c['stored_chars'],5)
        self.assertEqual(c['stop_reasons'],['CHAR_LIMIT']);self.assertEqual(c['completeness'],'NOT_CHECKED')

    def test_legacy_migration_does_not_invent_page_coverage(self):
        f=preserve_file(self.store,self.session,'old.txt',b'original')
        self.coverage(f)
        with self.store.connection() as db:db.execute('ALTER TABLE files DROP COLUMN extraction_coverage')
        c=self.coverage(Store(self.store.root).get_file(f['id']))
        self.assertEqual(c['status'],'UNKNOWN');self.assertEqual(c['stop_reasons'],['LEGACY_UNKNOWN'])
        self.assertIsNone(c['total_pages']);self.assertEqual(Path(self.store.get_file(f['id'])['path']).read_bytes(),b'original')

    def test_core_plan_and_role_context_include_missing_native_page(self):
        f=preserve_file(self.store,self.session,'mixed.pdf',self.pdf(['height 4m','']))
        self.store.enqueue(self.session,'Review',[f['id']],mode='CORE_RUN',requested_checks=['report'])
        calls=[]
        class Model:
            def chat(inner,messages):
                calls.append(messages)
                return json.dumps(dict(status='UNCERTAINTY',summary='Draft',observations=[],limitations=['Partial source']))
        Worker(self.store,Model()).run_once()
        r=self.store.snapshot(self.session)['jobs'][0]['result']
        self.assertIn('extraction_coverage',r['core_plan']['materials'][0])
        self.assertEqual(r['core_plan']['materials'][0]['extraction_coverage']['pages_without_text'],[2])
        self.assertTrue(r['context_truncated'],'Missing native text must be disclosed as incomplete context')
        self.assertIn('pages_without_text',str(calls[0]));self.assertIn('NOT_CHECKED',str(calls[0]))
        self.assertFalse(r['acceptance_granted'])

    def test_chat_records_and_discloses_source_coverage_with_context_cut(self):
        f=preserve_file(self.store,self.session,'long.txt',b'x'*20000)
        self.store.enqueue(self.session,'Read',[f['id']])
        class Model:
            def chat(inner,messages):inner.messages=messages;return 'Draft'
        model=Model();Worker(self.store,model).run_once()
        r=self.store.snapshot(self.session)['jobs'][0]['result']
        self.assertIn('source_coverage',r)
        self.assertTrue(r['source_coverage'][0]['context_text_truncated'])
        self.assertIn('extraction_coverage',str(model.messages));self.assertTrue(r['context_truncated'])
        self.assertIn('"context_text_truncated": true',model.messages[1]['content'])
        self.assertLessEqual(len(model.messages[1]['content']),16000)


if __name__=='__main__':unittest.main()

import hashlib
import importlib
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from engineering.local_app.files import preserve_file
from engineering.local_app.store import Store
from engineering.local_app.worker import Worker


class LocalDocumentExtractionTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.store=Store(Path(self.tmp.name));self.session=self.store.create_session()['id']
        self.assertTrue(hasattr(self.store,'enqueue_extraction'),'Extraction queue is missing')
        self.module=importlib.import_module('engineering.local_app.extraction')

    def source(self,texts):
        import fitz
        with fitz.open() as d:
            for text in texts:
                p=d.new_page()
                if text:p.insert_text((30,40),text)
            data=d.tobytes()
        return preserve_file(self.store,self.session,'report.pdf',data)

    def job(self):return self.store.snapshot(self.session)['jobs'][0]

    def test_native_all_23_pages_without_model_ocr_or_acceptance(self):
        f=self.source(['height 4m']*22+[''])
        self.store.enqueue_extraction(self.session,f['id'],'native')
        Worker(self.store,None).run_once();job=self.job();r=job['result']['extraction']
        self.assertEqual(job['state'],'SUCCEEDED');self.assertEqual(r['processed_pages'],23)
        self.assertEqual(r['blocked_pages'],1);self.assertEqual(r['ocr'],'NOT_RUN')
        self.assertEqual(r['completeness'],'NOT_CHECKED');self.assertFalse(job['result']['acceptance_granted'])
        journal=self.store.extraction_pages(self.session,job['id'],offset=20,limit=10)
        self.assertEqual([p['page'] for p in journal['pages']],[21,22,23])
        self.assertEqual(journal['pages'][-1]['status'],'BLOCK')
        page=self.store.extraction_page(self.session,job['id'],21)
        self.assertIn('height 4m',page['blocks'][0]['text'])
        self.assertEqual(Store(self.store.root).extraction_page(self.session,job['id'],21),page)
        self.assertEqual(hashlib.sha256(Path(self.store.get_file(f['id'])['path']).read_bytes()).hexdigest(),f['sha256'])

    def test_interruption_checkpoint_resume_skips_completed_pages(self):
        f=self.source(['first','second','third']);job=self.store.enqueue_extraction(self.session,f['id'],'native')
        worker=Worker(self.store,None);original=self.module.native_page;calls=[]
        def stop_after_one(pdf,page):
            calls.append(page);result=original(pdf,page)
            worker.stop_event.set();return result
        with patch.object(self.module,'native_page',stop_after_one):worker.run_once()
        self.assertEqual(self.job()['state'],'FAILED')
        self.assertEqual(self.job()['result']['extraction']['processed_pages'],1)
        self.store.resume_extraction(self.session,job['id'])
        with patch.object(self.module,'native_page',side_effect=lambda pdf,page:(calls.append(page),original(pdf,page))[1]):
            Worker(self.store,None).run_once()
        self.assertEqual(calls,[1,2,3]);self.assertEqual(self.job()['state'],'SUCCEEDED')
        with self.assertRaises(ValueError):self.store.resume_extraction(self.session,job['id'])

    def test_restart_keeps_pages_and_requires_explicit_resume(self):
        f=self.source(['first','second']);job=self.store.enqueue_extraction(self.session,f['id'],'native')
        worker=Worker(self.store,None);original=self.module.native_page
        def stop(pdf,page):
            result=original(pdf,page);worker.stop_event.set();return result
        with patch.object(self.module,'native_page',stop):worker.run_once()
        restarted=Store(self.store.root);restarted.interrupt_running()
        self.assertIsNone(restarted.claim())
        self.assertEqual(restarted.extraction_pages(self.session,job['id'])['total'],1)
        restarted.resume_extraction(self.session,job['id']);Worker(restarted,None).run_once()
        self.assertEqual(restarted.extraction_pages(self.session,job['id'])['total'],2)

    def test_changed_original_blocks_current_page_and_resume(self):
        f=self.source(['first','second']);job=self.store.enqueue_extraction(self.session,f['id'],'native')
        original=self.module.native_page
        def change(pdf,page):
            result=original(pdf,page);Path(self.store.get_file(f['id'])['path']).write_bytes(b'changed');return result
        with patch.object(self.module,'native_page',change):Worker(self.store,None).run_once()
        self.assertEqual(self.job()['state'],'FAILED')
        self.assertEqual(self.store.extraction_pages(self.session,job['id'])['pages'],[])
        with self.assertRaises(ValueError):self.store.resume_extraction(self.session,job['id'])

    def test_unknown_backend_non_pdf_and_foreign_jobs_are_rejected(self):
        f=self.source(['native']);other=self.store.create_session()['id']
        txt=preserve_file(self.store,self.session,'text.txt',b'original')
        for session,fid,backend in [(other,f['id'],'native'),(self.session,txt['id'],'native'),(self.session,f['id'],'fake')]:
            with self.subTest(backend=backend),self.assertRaises(ValueError):self.store.enqueue_extraction(session,fid,backend)
        job=self.store.enqueue_extraction(self.session,f['id'],'native');Worker(self.store,None).run_once()
        for action in [lambda:self.store.extraction_pages(other,job['id']),lambda:self.store.extraction_page(other,job['id'],1),lambda:self.store.resume_extraction(other,job['id'])]:
            with self.assertRaises(ValueError):action()

    def test_page_error_is_sanitized_and_retry_reprocesses_failed_only(self):
        f=self.source(['first','second']);job=self.store.enqueue_extraction(self.session,f['id'],'native');original=self.module.native_page
        def broken(pdf,page):
            if page==2:raise RuntimeError('PRIVATE_PATH_AND_SECRET')
            return original(pdf,page)
        with patch.object(self.module,'native_page',broken):Worker(self.store,None).run_once()
        self.assertEqual(self.job()['result']['extraction']['failed_pages'],1)
        self.assertNotIn('PRIVATE_PATH_AND_SECRET',json.dumps(self.job()))
        # Completed cycle with page errors can be explicitly resumed.
        self.store.resume_extraction(self.session,job['id']);calls=[]
        with patch.object(self.module,'native_page',side_effect=lambda pdf,page:(calls.append(page),original(pdf,page))[1]):Worker(self.store,None).run_once()
        self.assertEqual(calls,[2]);self.assertEqual(self.job()['result']['extraction']['failed_pages'],0)

    def test_limits_disclose_clipping_and_cannot_be_bypassed_by_resume(self):
        f=self.source(['abcdefghij','second','third'])
        self.store.enqueue_extraction(self.session,f['id'],'native')
        with patch.object(self.module,'MAX_PAGE_TEXT',5),patch.object(self.module,'MAX_TOTAL_TEXT',5):Worker(self.store,None).run_once()
        r=self.job()['result']['extraction'];self.assertTrue(r['budget_exhausted']);self.assertEqual(r['processed_pages'],1)
        self.assertEqual(r['blocked_pages'],1)
        page=self.store.extraction_page(self.session,self.job()['id'],1)
        self.assertTrue(page['text_truncated']);self.assertEqual(page['stored_chars'],5)
        with self.assertRaises(ValueError):self.store.resume_extraction(self.session,self.job()['id'])

    def test_missing_docling_has_explicit_failure_without_native_fallback(self):
        f=self.source(['native']);self.store.enqueue_extraction(self.session,f['id'],'docling')
        with patch.dict('os.environ',{},clear=True):Worker(self.store,None).run_once()
        self.assertEqual(self.job()['state'],'FAILED')
        self.assertIn('Docling',self.job()['error'])
        self.assertEqual(self.job()['result']['extraction']['processed_pages'],0)
        self.assertEqual(self.job()['result']['extraction']['ocr'],'NOT_RUN')

    def test_local_docling_converter_is_initialized_once_per_task(self):
        from engineering.document_intelligence.docling_adapter import DoclingDocumentParser
        f=self.source(['first','second']);self.store.enqueue_extraction(self.session,f['id'],'docling')
        class Converter:
            def convert(inner,path,page_range):
                exported=dict(texts=[dict(text='Candidate',prov=[dict(page_no=page_range[0])])])
                return SimpleNamespace(document=SimpleNamespace(export_to_dict=lambda:exported))
        env={'ENGINEER_OS_DOCUMENT_INTELLIGENCE':'true','ENGINEER_OS_DOCLING_ARTIFACTS_PATH':self.tmp.name}
        original=DoclingDocumentParser._converter;constructions=[]
        def construct(parser):
            if parser._converter_factory is not None:return original(parser)
            constructions.append(True);return Converter()
        with patch.dict('os.environ',env),patch.object(self.module.importlib.util,'find_spec',return_value=True),patch.object(DoclingDocumentParser,'_converter',construct):
            Worker(self.store,None).run_once()
        self.assertEqual(len(constructions),1,'Avoid reloading model/converter for every page')
        self.assertEqual(self.job()['result']['extraction']['processed_pages'],2)

    def test_docling_resume_preserves_prior_ocr_request_on_failed_retry(self):
        from engineering.document_intelligence.docling_adapter import DoclingDocumentParser
        f=self.source(['first','second']);job=self.store.enqueue_extraction(self.session,f['id'],'docling')
        class Converter:
            def convert(inner,path,page_range):
                if page_range[0]==2:raise RuntimeError('Synthetic parser failure')
                return SimpleNamespace(document=SimpleNamespace(export_to_dict=lambda:dict(texts=[dict(text='Candidate',prov=[dict(page_no=1)])])))
        parser=DoclingDocumentParser(lambda:Converter())
        with patch.dict('os.environ',{'ENGINEER_OS_DOCUMENT_INTELLIGENCE':'true'}),patch.object(self.module,'docling_parser',return_value=parser):
            Worker(self.store,None).run_once()
            self.assertEqual(self.job()['result']['extraction']['ocr'],'REQUESTED_NOT_VERIFIED')
            self.store.resume_extraction(self.session,job['id']);Worker(self.store,None).run_once()
        self.assertEqual(self.job()['result']['extraction']['ocr'],'REQUESTED_NOT_VERIFIED')
        self.assertEqual(self.store.extraction_page(self.session,job['id'],2)['ocr'],'REQUESTED_NOT_VERIFIED')

    def test_existing_docling_adapter_range_and_normalized_source_contract(self):
        from engineering.document_intelligence.docling_adapter import DoclingDocumentParser
        f=self.source(['first','second']);self.store.enqueue_extraction(self.session,f['id'],'docling');ranges=[]
        class Converter:
            def convert(inner,path,page_range):
                ranges.append(page_range);p=page_range[0]
                exported=dict(texts=[dict(text='OCR candidate',label='text',prov=[dict(page_no=p,bbox=dict(l=1,t=1,r=50,b=20,coord_origin='TOPLEFT'))])])
                return SimpleNamespace(document=SimpleNamespace(export_to_dict=lambda:exported))
        parser=DoclingDocumentParser(lambda:Converter())
        with patch.dict('os.environ',{'ENGINEER_OS_DOCUMENT_INTELLIGENCE':'true'}),patch.object(self.module,'docling_parser',return_value=parser):Worker(self.store,None).run_once()
        self.assertEqual(ranges,[(1,1),(2,2)])
        page=self.store.extraction_page(self.session,self.job()['id'],2)
        self.assertEqual(page['blocks'][0]['provenance'][0]['page_no'],2)
        self.assertEqual(page['source_sha256'],f['sha256']);self.assertFalse(page['acceptance_granted'])


if __name__=='__main__':unittest.main()

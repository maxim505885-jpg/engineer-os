import json
import tempfile
import unittest
from pathlib import Path

from engineering.local_app.files import preserve_file
from engineering.local_app.store import Store
from engineering.local_app.worker import Worker


class AutomaticDocumentAnalysisTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.store=Store(Path(self.tmp.name));self.session=self.store.create_session()['id']

    def pdf(self,texts):
        import fitz
        with fitz.open() as doc:
            for text in texts:
                page=doc.new_page()
                if text:page.insert_textbox((30,30,570,800),text,fontsize=8)
            data=doc.tobytes()
        return preserve_file(self.store,self.session,'report.pdf',data)

    def model(self,core=False):
        calls=[]
        class Model:
            def chat(inner,messages):
                calls.append(messages)
                return json.dumps(dict(status='UNCERTAINTY',summary='Draft',observations=[],limitations=['Unverified source'])) if core else 'Draft summary'
        return Model(),calls

    def result(self):return self.store.snapshot(self.session)['jobs'][0]

    def test_attach_and_send_reads_page_24_without_manual_extraction(self):
        f=self.pdf(['height 4m']*23+['UNIQUE_TAIL_PAGE24'])
        self.store.enqueue(self.session,'Review the whole document',[f['id']])
        model,calls=self.model();Worker(self.store,model).run_once()
        self.assertIn('UNIQUE_TAIL_PAGE24',str(calls),'Automatic analysis must go beyond preview20')
        job=self.result();self.assertEqual(job['state'],'SUCCEEDED')
        self.assertEqual(len(self.store.snapshot(self.session)['jobs']),1,'Internal extraction is not another user task')
        self.assertIn('document_analysis',job['result'])
        self.assertEqual(job['result']['document_analysis']['sources'][0]['total_pages'],24)
        self.assertFalse(job['result']['acceptance_granted'])

    def test_overlapping_ocr_passes_remain_labelled_in_model_payload(self):
        from unittest.mock import patch
        from engineering.local_app import ocr
        if not ocr.identity()['available']:self.skipTest('Local rus+eng models unavailable')
        import fitz
        with fitz.open() as doc:
            doc.new_page().insert_text((60,120),'Height 4 metres',fontsize=30)
            file=preserve_file(self.store,self.session,'regional.pdf',doc.tobytes())
        self.store.enqueue(self.session,'Read',[file['id']]);model,calls=self.model()
        with patch.dict('os.environ',{'ENGINEER_OS_ATTACHMENT_PARSER':'ocr','ENGINEER_OS_OCR_LAYOUT':'regions'}):
            Worker(self.store,model).run_once()
        self.assertEqual(self.result()['state'],'SUCCEEDED')
        payload=json.loads(calls[0][-1]['content'].split('\n',1)[1])
        self.assertIn('[OCR pass whole;',payload['text'])
        self.assertIn('[OCR pass r1;',payload['text'])
        self.assertIn('OCR_REGION_CANDIDATES_UNMERGED',payload['sources_report'][0]['limitations'])
        self.assertEqual(payload['refs'][0]['ocr_candidates'],'OVERLAPPING_ALTERNATIVES_NOT_INDEPENDENT_EVIDENCE')
        self.assertFalse(self.result()['result']['acceptance_granted'])

    def test_large_pdf_all_text_batches_are_analyzed_and_receipts_persist(self):
        f=self.pdf([('PAGE_'+str(i)+' '+'native source '*450) for i in range(1,7)])
        self.store.enqueue(self.session,'Read all selected pages',[f['id']])
        model,calls=self.model();Worker(self.store,model).run_once();job=self.result()
        self.assertGreater(len(calls),1)
        for i in range(1,7):self.assertIn('PAGE_'+str(i),str(calls))
        self.assertIn('document_analysis',job['result'])
        self.assertTrue(job['result']['document_analysis']['all_batches_completed'])
        self.assertTrue(hasattr(self.store,'analysis_receipts'))
        receipts=self.store.analysis_receipts(self.session,job['id'])
        self.assertGreater(receipts['total'],1)
        self.assertEqual(Store(self.store.root).analysis_receipts(self.session,job['id']),receipts)
        self.assertTrue(all(r['acceptance_granted'] is False for r in receipts['records']))

    def test_core_roles_get_late_pages_automatically(self):
        f=self.pdf(['native']*20+['CORE_TAIL21'])
        self.store.enqueue(self.session,'Review',[f['id']],mode='CORE_RUN',requested_checks=['report'])
        model,calls=self.model(core=True);Worker(self.store,model).run_once()
        self.assertIn('CORE_TAIL21',str(calls))
        r=self.result()['result'];self.assertEqual(r['core_run']['status'],'BLOCK');self.assertIn('TZ_CHECKLIST_MISSING',r['core_run']['engineering_review']['reasons'])
        self.assertIn('document_analysis',r);self.assertFalse(r['acceptance_granted'])

    def test_bad_pdf_fails_before_model_and_unknown_text_is_disclosed(self):
        f=preserve_file(self.store,self.session,'invalid.pdf',b'not a PDF')
        self.store.enqueue(self.session,'Read',[f['id']]);model,calls=self.model();Worker(self.store,model).run_once()
        self.assertEqual(self.result()['state'],'FAILED');self.assertEqual(calls,[])

    def test_blank_page_is_disclosed_without_fake_ocr(self):
        f=self.pdf(['native',''])
        self.store.enqueue(self.session,'Read',[f['id']]);model,calls=self.model();Worker(self.store,model).run_once()
        self.assertIn('NO_NATIVE_TEXT',str(calls))
        self.assertIn('document_analysis',self.result()['result'])
        self.assertEqual(self.result()['result']['document_analysis']['sources'][0]['blocked_pages'],1)

    def test_blank_pdf_failure_has_terminal_progress(self):
        f=self.pdf(['']);self.store.enqueue(self.session,'Read',[f['id']])
        model,calls=self.model();Worker(self.store,model).run_once()
        job=self.result();self.assertEqual(job['state'],'FAILED')
        self.assertEqual(job['result']['document_analysis']['stage'],'PARTIAL')
        self.assertEqual(calls,[])

    def test_actual_ocr_context_does_not_claim_preview_ocr_was_not_run(self):
        from types import SimpleNamespace
        from unittest.mock import patch
        from engineering.document_intelligence.docling_adapter import DoclingDocumentParser
        f=self.pdf([''])
        class Converter:
            def convert(inner,*args,**kwargs):
                return SimpleNamespace(document=SimpleNamespace(export_to_dict=lambda:dict(
                    texts=[dict(text='OCR candidate height 4m',prov=[dict(page_no=1)])])))
        parser=DoclingDocumentParser(lambda:Converter())
        self.store.enqueue(self.session,'Read',[f['id']]);model,calls=self.model()
        with patch.dict('os.environ',{'ENGINEER_OS_DOCUMENT_INTELLIGENCE':'true','ENGINEER_OS_ATTACHMENT_PARSER':'docling'}),patch('engineering.local_app.extraction.docling_parser',return_value=parser):
            Worker(self.store,model).run_once()
        self.assertEqual(self.result()['state'],'SUCCEEDED')
        self.assertNotIn('TEXT_PREVIEW_ONLY',str(calls))
        self.assertNotIn('"ocr": "NOT_RUN"',str(calls))
        self.assertIn('REQUESTED_NOT_VERIFIED',str(calls))
        self.assertIn('OCR candidate height 4m',str(calls))
        self.assertEqual(self.result()['result']['source_coverage'][0]['extraction_coverage']['method'],'DOCLING')
        self.assertFalse(self.result()['result']['acceptance_granted'])

    def test_core_ocr_prompts_and_saved_context_use_current_extraction(self):
        from types import SimpleNamespace
        from unittest.mock import patch
        from engineering.document_intelligence.docling_adapter import DoclingDocumentParser
        f=self.pdf([''])
        class Converter:
            def convert(inner,*args,**kwargs):
                return SimpleNamespace(document=SimpleNamespace(export_to_dict=lambda:dict(
                    texts=[dict(text='OCR candidate height 4m',prov=[dict(page_no=1)])])))
        parser=DoclingDocumentParser(lambda:Converter())
        self.store.enqueue(self.session,'Review',[f['id']],mode='CORE_RUN',requested_checks=['report'])
        model,calls=self.model(core=True)
        with patch.dict('os.environ',{'ENGINEER_OS_DOCUMENT_INTELLIGENCE':'true','ENGINEER_OS_ATTACHMENT_PARSER':'docling'}),patch('engineering.local_app.extraction.docling_parser',return_value=parser):
            Worker(self.store,model).run_once()
        self.assertEqual(self.result()['state'],'SUCCEEDED');self.assertEqual(len(calls),2)
        self.assertNotIn('TEXT_PREVIEW_ONLY',str(calls));self.assertNotIn('"ocr": "NOT_RUN"',str(calls))
        context=self.result()['result']['core_run']['source_context']['sources'][0]
        self.assertEqual(context['extraction_coverage']['method'],'DOCLING')
        self.assertEqual(context['extraction_coverage']['ocr'],'REQUESTED_NOT_VERIFIED')
        self.assertNotIn('preview',context['extraction_note'])
        self.assertFalse(self.result()['result']['acceptance_granted'])

    def test_core_block_in_a_source_part_cannot_disappear_in_summary(self):
        f=self.pdf(['source '*500]*3)
        self.store.enqueue(self.session,'Review',[f['id']],mode='CORE_RUN',requested_checks=['report'])
        count=0
        class Model:
            def chat(inner,messages):
                nonlocal count
                count+=1
                return json.dumps(dict(status='BLOCK' if count==1 else 'UNCERTAINTY',summary='Draft',observations=[],limitations=['Unverified']))
        Worker(self.store,Model()).run_once()
        self.assertEqual(self.result()['result']['core_run']['status'],'BLOCK')

    def test_foreign_receipts_are_not_accessible(self):
        f=self.pdf(['source']);job=self.store.enqueue(self.session,'Read',[f['id']])
        model,_=self.model();Worker(self.store,model).run_once();other=self.store.create_session()['id']
        self.assertTrue(hasattr(self.store,'analysis_receipts'))
        with self.assertRaises(ValueError):self.store.analysis_receipts(other,job['id'])

    def test_core_block_survives_later_part_failure(self):
        f=self.pdf(['source '*500]*3)
        self.store.enqueue(self.session,'Review',[f['id']],mode='CORE_RUN',requested_checks=['report'])
        count=0
        class Model:
            def chat(inner,messages):
                nonlocal count
                count+=1
                if count==2:raise RuntimeError('offline')
                return json.dumps(dict(status='BLOCK' if count==1 else 'UNCERTAINTY',summary='Draft',observations=[],limitations=['Unverified']))
        Worker(self.store,Model()).run_once()
        run=self.result()['result']['core_run']
        self.assertEqual(run['status'],'BLOCK')
        self.assertEqual(run['results'][0]['execution'],'FAILED')

    def test_completed_role_block_survives_another_role_failure(self):
        f=self.pdf(['source'])
        self.store.enqueue(self.session,'Review',[f['id']],mode='CORE_RUN',requested_checks=['report','final_audit'])
        count=0
        class Model:
            def chat(inner,messages):
                nonlocal count
                count+=1
                if count==2:raise RuntimeError('offline')
                return json.dumps(dict(status='BLOCK',summary='Draft',observations=[],limitations=['Unverified']))
        Worker(self.store,Model()).run_once()
        self.assertEqual(self.result()['result']['core_run']['status'],'BLOCK')

    def test_saved_block_survives_shutdown(self):
        f=self.pdf(['source '*500]*3)
        self.store.enqueue(self.session,'Review',[f['id']],mode='CORE_RUN',requested_checks=['report'])
        class Model:
            def chat(inner,messages):
                worker.stop_event.set()
                return json.dumps(dict(status='BLOCK',summary='Draft',observations=[],limitations=['Unverified']))
        worker=Worker(self.store,Model());worker.run_once()
        self.assertEqual(self.result()['result']['core_run']['status'],'BLOCK')

    def test_saved_block_survives_progress_write_failure(self):
        f=self.pdf(['source']);self.store.enqueue(self.session,'Review',[f['id']],mode='CORE_RUN',requested_checks=['report'])
        original=self.store.analysis_progress;failed=False
        def progress(job_id,report):
            nonlocal failed
            if not failed and any(r.get('block_seen') for r in report['roles'].values()):
                failed=True;raise RuntimeError('checkpoint failed')
            return original(job_id,report)
        self.store.analysis_progress=progress
        class Model:
            def chat(inner,messages):return json.dumps(dict(status='BLOCK',summary='Draft',observations=[],limitations=['Unverified']))
        Worker(self.store,Model()).run_once()
        self.assertEqual(self.result()['result']['core_run']['status'],'BLOCK')

    def test_extraction_budget_failure_prevents_partial_model_analysis(self):
        from unittest.mock import patch
        f=self.pdf(['first page','second page'])
        self.store.enqueue(self.session,'Read',[f['id']]);model,calls=self.model()
        with patch('engineering.local_app.extraction.MAX_TOTAL_TEXT',10):Worker(self.store,model).run_once()
        job=self.result()
        self.assertEqual(job['state'],'FAILED')
        self.assertEqual(job['result']['document_analysis']['stage'],'PARTIAL')
        self.assertEqual(calls,[])

    def test_batch_references_identify_exact_text_and_page_boundaries(self):
        import hashlib
        f=self.pdf(['PAGE_ONE','PAGE_TWO'])
        self.store.enqueue(self.session,'Read',[f['id']]);model,calls=self.model();Worker(self.store,model).run_once()
        payload=json.loads(calls[0][-1]['content'].split('\n',1)[1])
        self.assertIn('PAGE_ONE\n\nPAGE_TWO',payload['text'])
        for ref in payload['refs']:
            segment=payload['text'][ref['batch_start']:ref['batch_end']]
            self.assertEqual(hashlib.sha256(segment.encode()).hexdigest(),ref['text_sha256'])

    def test_changed_source_during_model_call_fails_and_retains_receipt(self):
        f=self.pdf(['source']);self.store.enqueue(self.session,'Read',[f['id']])
        class Model:
            def chat(inner,messages):
                Path(f['path']).write_bytes(b'changed');return 'Draft'
        Worker(self.store,Model()).run_once();job=self.result()
        self.assertEqual(job['state'],'FAILED')
        self.assertFalse(job['result']['document_analysis']['all_batches_completed'])
        self.assertEqual(self.store.analysis_receipts(self.session,job['id'])['records'][0]['status'],'FAILED')


if __name__=='__main__':unittest.main()

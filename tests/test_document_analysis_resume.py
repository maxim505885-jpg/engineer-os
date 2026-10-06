"""Durable resume contracts; controlled transport, not live model quality."""
import json
from pathlib import Path
from unittest.mock import patch

import unittest
import test_automatic_document_analysis as automatic_tests
from engineering.local_app.store import Store
from engineering.local_app.worker import Worker


class ControlledModel:
    def __init__(self,fail_at=None,core=False,long=False):
        self.calls=[];self.fail_at=fail_at;self.core=core;self.long=long;self.revision='fixed-test-1'

    def checkpoint_identity(self):return dict(provider='controlled',revision=self.revision)

    def chat(self,messages):
        self.calls.append(messages)
        if len(self.calls)==self.fail_at:raise RuntimeError('private failure')
        if self.core:
            return json.dumps(dict(status='BLOCK' if len(self.calls)==1 else 'UNCERTAINTY',summary='Draft',observations=[],limitations=['Unverified']))
        return 'HEAD_'+('x'*4500)+'_TAIL_MARKER' if self.long else 'Draft summary'


class DocumentResumeTests(unittest.TestCase):
    setUp=automatic_tests.AutomaticDocumentAnalysisTests.setUp
    pdf=automatic_tests.AutomaticDocumentAnalysisTests.pdf
    result=automatic_tests.AutomaticDocumentAnalysisTests.result
    def start(self,model,core=False):
        f=self.pdf(['page '+str(i)+' source '*500 for i in range(4)])
        job=self.store.enqueue(self.session,'Read unchanged task',[f['id']],mode='CORE_RUN' if core else 'CHAT',requested_checks=['report'] if core else [])
        Worker(self.store,model).run_once()
        return f,job

    def test_restart_resume_reuses_parts_without_duplicate_messages(self):
        model=ControlledModel(fail_at=2);_,job=self.start(model)
        before=self.store.analysis_receipts(self.session,job['id'])
        self.assertEqual(before['records'][0]['status'],'COMPLETED')
        restarted=Store(self.store.root)
        self.assertTrue(hasattr(restarted,'resume_analysis'),'Explicit analysis resume is missing')
        restarted.resume_analysis(self.session,job['id'],model)
        model.fail_at=None;Worker(restarted,model).run_once()
        current=restarted.snapshot(self.session)
        self.assertEqual(current['jobs'][0]['state'],'SUCCEEDED')
        self.assertEqual(len(current['jobs']),1);self.assertEqual(len(current['messages']),2)
        first=model.calls[0][-1]['content']
        self.assertEqual(sum(c[-1]['content']==first for c in model.calls),1)
        self.assertGreater(current['jobs'][0]['result']['document_analysis']['calls_reused'],0)
        with self.assertRaises(ValueError):restarted.resume_analysis(self.session,job['id'],model)

    def test_changed_model_parser_source_and_foreign_session_reject_resume(self):
        model=ControlledModel(fail_at=2);f,job=self.start(model)
        self.assertTrue(hasattr(self.store,'resume_analysis'))
        other=self.store.create_session()['id']
        with self.assertRaises(ValueError):self.store.resume_analysis(other,job['id'],model)
        model.revision='changed'
        with self.assertRaises(ValueError):self.store.resume_analysis(self.session,job['id'],model)
        model.revision='fixed-test-1'
        with patch.dict('os.environ',{'ENGINEER_OS_ATTACHMENT_PARSER':'docling'}):
            with self.assertRaises(ValueError):self.store.resume_analysis(self.session,job['id'],model)
        Path(self.store.get_file(f['id'])['path']).write_bytes(b'changed')
        with self.assertRaises(ValueError):self.store.resume_analysis(self.session,job['id'],model)
        self.assertEqual(self.result()['state'],'FAILED')

    def test_summary_failure_resumes_summary_without_repeating_sources(self):
        model=ControlledModel()
        def stop_summary(messages):
            payload=json.loads(messages[-1]['content'].split('\n',1)[1])
            model.calls.append(messages)
            if 'drafts' in payload:raise RuntimeError('summary unavailable')
            return 'Retained draft'
        model.chat=stop_summary;_,job=self.start(model)
        nsource=sum('"refs"' in c[-1]['content'] for c in model.calls)
        self.assertEqual(self.result()['state'],'FAILED')
        self.assertFalse(self.result()['result']['document_analysis']['all_batches_completed'])
        self.assertTrue(hasattr(self.store,'resume_analysis'))
        self.store.resume_analysis(self.session,job['id'],model)
        model.chat=lambda messages:(model.calls.append(messages),'Recovered summary')[1]
        Worker(self.store,model).run_once()
        self.assertEqual(sum('"refs"' in c[-1]['content'] for c in model.calls),nsource)
        self.assertEqual(self.result()['state'],'SUCCEEDED')

    def test_summary_clipping_is_reported_and_full_drafts_survive(self):
        model=ControlledModel(long=True);_,job=self.start(model)
        report=self.result()['result']['document_analysis']
        self.assertTrue(report.get('summary_input_clipped'),'Summary loss is hidden')
        self.assertGreater(report['summary_omitted_chars'],0)
        receipts=self.store.analysis_receipts(self.session,job['id'])['records']
        self.assertTrue(any('TAIL_MARKER' in r.get('text','') for r in receipts))
        self.assertTrue(all(r.get('elapsed_seconds',-1)>=0 for r in receipts))

    def test_core_failed_parts_resume_and_preserve_block(self):
        model=ControlledModel(fail_at=2,core=True);_,job=self.start(model,core=True)
        self.assertEqual(self.result()['result']['core_run']['status'],'BLOCK')
        self.assertEqual(self.result()['state'],'FAILED','Incomplete CORE execution must remain resumable, not succeeded')
        self.assertTrue(hasattr(self.store,'resume_analysis'))
        self.store.resume_analysis(self.session,job['id'],model);model.fail_at=None
        Worker(self.store,model).run_once()
        self.assertEqual(self.result()['result']['core_run']['status'],'BLOCK')
        self.assertTrue(self.result()['result']['document_analysis']['all_batches_completed'])
        self.assertFalse(self.result()['result']['acceptance_granted'])

    def test_analysis_call_budget_fails_closed_with_receipts(self):
        model=ControlledModel()
        with patch('engineering.local_app.automatic_analysis.MAX_MODEL_CALLS',1,create=True):_,job=self.start(model)
        self.assertEqual(self.result()['state'],'FAILED')
        self.assertEqual(len(model.calls),1)
        self.assertTrue(self.result()['result']['document_analysis']['budget_exhausted'])
        self.assertFalse(self.result()['result']['document_analysis']['all_batches_completed'])

    def test_interrupted_extraction_resumes_same_child_and_skips_pages(self):
        from engineering.local_app import extraction
        f=self.pdf(['first','second','third']);job=self.store.enqueue(self.session,'Read',[f['id']])
        model=ControlledModel();worker=Worker(self.store,model);calls=[];original=extraction.native_page
        def stop(pdf,page):
            calls.append(page);blocks=original(pdf,page);worker.stop_event.set();return blocks
        with patch.object(extraction,'native_page',stop):worker.run_once()
        child=self.result()['result']['document_analysis']['sources'][0]['extraction_job']
        self.store.resume_analysis(self.session,job['id'],model)
        with patch.object(extraction,'native_page',side_effect=lambda pdf,page:(calls.append(page),original(pdf,page))[1]):Worker(self.store,model).run_once()
        self.assertEqual(calls,[1,2,3]);self.assertEqual(self.result()['state'],'SUCCEEDED')
        self.assertEqual(self.result()['result']['document_analysis']['sources'][0]['extraction_job'],child)

    def test_failed_parser_pages_retry_only_failed_and_retained_block_survives(self):
        from engineering.local_app import extraction
        f=self.pdf(['first','','third']);job=self.store.enqueue(self.session,'Read',[f['id']]);model=ControlledModel();original=extraction.native_page
        def broken(pdf,page):
            if page==3:raise RuntimeError('private')
            return original(pdf,page)
        with patch.object(extraction,'native_page',broken):Worker(self.store,model).run_once()
        self.assertEqual(model.calls,[]);self.assertEqual(self.result()['state'],'FAILED')
        self.store.resume_analysis(self.session,job['id'],model);calls=[]
        with patch.object(extraction,'native_page',side_effect=lambda pdf,page:(calls.append(page),original(pdf,page))[1]):Worker(self.store,model).run_once()
        self.assertEqual(calls,[3]);self.assertEqual(self.result()['state'],'SUCCEEDED')
        self.assertEqual(self.result()['result']['document_analysis']['sources'][0]['blocked_pages'],1)

    def test_busy_session_and_budget_changes_cannot_resume(self):
        model=ControlledModel(fail_at=2);_,job=self.start(model)
        with patch('engineering.local_app.automatic_analysis.PART_CHARS',5000):
            with self.assertRaises(ValueError):self.store.resume_analysis(self.session,job['id'],model)
        self.store.enqueue(self.session,'another request',[])
        with self.assertRaises(ValueError):self.store.resume_analysis(self.session,job['id'],model)

    def test_model_changes_between_enqueue_resume_and_claim_rejects_reuse(self):
        model=ControlledModel(fail_at=2);_,job=self.start(model)
        self.store.resume_analysis(self.session,job['id'],model);model.revision='changed';model.fail_at=None
        before=len(model.calls);Worker(self.store,model).run_once()
        self.assertEqual(len(model.calls),before);self.assertEqual(self.result()['state'],'FAILED')

    def test_stop_after_last_call_can_finalize_from_retained_draft(self):
        f=self.pdf(['source']);job=self.store.enqueue(self.session,'Read',[f['id']]);model=ControlledModel();worker=Worker(self.store,model)
        original=model.chat
        def stop(messages):
            reply=original(messages);worker.stop_event.set();return reply
        model.chat=stop;worker.run_once()
        self.assertEqual(self.result()['state'],'FAILED')
        self.store.resume_analysis(self.session,job['id'],model);model.chat=original
        Worker(self.store,model).run_once();self.assertEqual(len(model.calls),1)
        self.assertEqual(self.result()['state'],'SUCCEEDED')

    def test_cumulative_time_budget_cannot_be_reset_by_restart(self):
        model=ControlledModel(fail_at=2)
        with patch('engineering.local_app.automatic_analysis.MAX_MODEL_SECONDS',0.000001):
            _,job=self.start(model)
            self.assertEqual(self.result()['state'],'FAILED')
            self.assertTrue(self.result()['result']['document_analysis']['budget_exhausted'])
            with self.assertRaises(ValueError):Store(self.store.root).resume_analysis(self.session,job['id'],model)

    def test_corrupted_completed_receipt_is_never_reused(self):
        model=ControlledModel(fail_at=2);_,job=self.start(model)
        with self.store.connection() as db:
            row=db.execute('SELECT seq,record FROM analysis_receipts WHERE job_id=? ORDER BY seq LIMIT 1',(job['id'],)).fetchone()
            value=json.loads(row['record']);value['text']='Tampered draft'
            db.execute('UPDATE analysis_receipts SET record=? WHERE seq=?',(json.dumps(value),row['seq']))
        self.store.resume_analysis(self.session,job['id'],model);model.fail_at=None
        Worker(self.store,model).run_once();self.assertEqual(self.result()['state'],'FAILED')
        self.assertFalse(self.result()['result']['acceptance_granted'])

    def test_inflight_call_is_journaled_before_process_interruption(self):
        model=ControlledModel();f=self.pdf(['source']);job=self.store.enqueue(self.session,'Read',[f['id']])
        def crash(messages):raise KeyboardInterrupt('simulated process interruption')
        model.chat=crash
        with self.assertRaises(KeyboardInterrupt):Worker(self.store,model).run_once()
        rows=self.store.analysis_receipts(self.session,job['id'])['records']
        self.assertEqual(len(rows),1);self.assertEqual(rows[0]['status'],'RUNNING')
        restarted=Store(self.store.root);restarted.interrupt_running()
        model.chat=lambda messages:'Retried draft'
        restarted.resume_analysis(self.session,job['id'],model);Worker(restarted,model).run_once()
        self.assertEqual(restarted.snapshot(self.session)['jobs'][0]['result']['document_analysis']['model_calls'],2)

    def test_changed_final_audit_skill_rejects_core_resume(self):
        from engineering.core.skill_loader import SkillLoader
        model=ControlledModel(fail_at=2,core=True);_,job=self.start(model,core=True)
        original=SkillLoader.load
        with patch.object(SkillLoader,'load',lambda loader,name:original(loader,name)+('\nChanged' if name=='final-audit' else '')):
            with self.assertRaises(ValueError):self.store.resume_analysis(self.session,job['id'],model)

    def test_new_evidence_candidate_requires_new_core_task(self):
        from engineering.local_app.evidence import register
        model=ControlledModel(fail_at=2,core=True);f,job=self.start(model,core=True)
        register(self.store,self.session,file_id=f['id'],quote='page 0 source',statement='New context',page=1)
        with self.assertRaises(ValueError):self.store.resume_analysis(self.session,job['id'],model)

    def test_saved_block_survives_identity_failure_before_receipt_replay(self):
        model=ControlledModel(fail_at=2,core=True);_,job=self.start(model,core=True)
        self.assertEqual(self.result()['result']['core_run']['status'],'BLOCK')
        self.store.resume_analysis(self.session,job['id'],model)
        original=model.checkpoint_identity;calls=0
        def unavailable():
            nonlocal calls
            calls+=1
            return original() if calls==1 else None
        model.checkpoint_identity=unavailable
        Worker(self.store,model).run_once()
        self.assertEqual(self.result()['state'],'FAILED')
        self.assertEqual(self.result()['result']['core_run']['status'],'BLOCK')

    def test_parent_extraction_budget_exhaustion_cannot_start_new_child(self):
        from engineering.local_app import extraction
        model=ControlledModel();f=self.pdf(['abcdefghij','second']);job=self.store.enqueue(self.session,'Read',[f['id']])
        with patch.object(extraction,'MAX_TOTAL_TEXT',5):
            Worker(self.store,model).run_once()
            report=self.result()['result']['document_analysis']
            self.assertTrue(report['budget_exhausted'],'Parent must carry terminal child budget')
            child=report['sources'][0]['extraction_job']
            with self.assertRaises(ValueError):self.store.resume_analysis(self.session,job['id'],model)
            self.assertEqual(self.result()['result']['document_analysis']['sources'][0]['extraction_job'],child)
        self.assertEqual(model.calls,[])

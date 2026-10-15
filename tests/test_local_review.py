import tempfile
import unittest
from pathlib import Path
from engineering.local_app.store import Store
from engineering.local_app.files import preserve_file
from engineering.local_app.evidence import register

class LocalReviewTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.store=Store(self.tmp.name);self.session=self.store.create_session()['id']
        self.file=preserve_file(self.store,self.session,'source.txt',b'height 4m')
        self.candidate=register(self.store,self.session,file_id=self.file['id'],quote='height 4m',statement='Unknown')

    def review(self,revision=0,decision='SOURCE_CONFIRMED',**overrides):
        try:from engineering.local_app.review import record_review
        except ImportError:self.fail('Source review journal missing')
        args=dict(expected_revision=revision,decision=decision,note='Quote checked against original',actor='Local reviewer');args.update(overrides)
        return record_review(self.store,self.session,self.candidate['id'],**args)

    def test_review_identity_uses_bounded_stream_reads(self):
        from unittest.mock import patch
        original_open=Path.open
        class BoundedReader:
            def __init__(self,stream):self.stream=stream
            def __enter__(self):return self
            def __exit__(self,*args):return self.stream.__exit__(*args)
            def __getattr__(self,name):return getattr(self.stream,name)
            def read(self,size=-1):
                if size<0 or size>1024*1024:raise AssertionError('Original verification must stream bounded chunks')
                return self.stream.read(size)
        def bounded_open(path,*args,**kwargs):return BoundedReader(original_open(path,*args,**kwargs))
        with patch.object(Path,'open',bounded_open):
            result=self.review(decision='NEEDS_DATA')
        self.assertEqual(result['decision'],'NEEDS_DATA')
        self.assertFalse(result['acceptance_granted'])

    def test_append_only_decisions_survive_restart_without_acceptance(self):
        first=self.review();second=self.review(1,'REJECTED',note='Needs correction')
        r=Store(self.tmp.name).snapshot(self.session)['evidence'][0]
        self.assertEqual(r['review_revision'],2)
        self.assertEqual([e['decision'] for e in r['reviews']],['SOURCE_CONFIRMED','REJECTED'])
        self.assertEqual(r['latest_review']['id'],second['id']);self.assertNotEqual(first['id'],second['id'])
        self.assertEqual(first['source_sha256'],self.file['sha256'])
        self.assertEqual(len(first['candidate_digest']),64)
        self.assertFalse(r['acceptance_granted']);self.assertEqual(r['status'],'UNVERIFIED')
        self.assertFalse(first['actor_verified'])

    def test_stale_revision_and_invalid_fields_do_not_overwrite_history(self):
        self.review()
        with self.assertRaises(ValueError):self.review(0,'REJECTED')
        for args in [dict(revision=True),dict(decision='ACCEPTED'),dict(note=''),dict(actor='')]:
            with self.assertRaises(ValueError):self.review(**args)
        self.assertEqual(self.store.snapshot(self.session)['evidence'][0]['review_revision'],1)

    def test_changed_original_and_foreign_session_cannot_record_review(self):
        other=self.store.create_session()['id']
        try:from engineering.local_app.review import record_review
        except ImportError:self.fail('Source review journal missing')
        with self.assertRaises(ValueError):record_review(self.store,other,self.candidate['id'],expected_revision=0,decision='NEEDS_DATA',note='x',actor='x')
        Path(self.store.get_file(self.file['id'])['path']).write_bytes(b'changed')
        with self.assertRaises(ValueError):self.review()

    def test_unchecked_pdf_cannot_be_confirmed_as_source_match(self):
        f=preserve_file(self.store,self.session,'bad.pdf',b'broken')
        self.candidate=register(self.store,self.session,file_id=f['id'],quote='claimed text',statement='Unknown',page=1)
        with self.assertRaises(ValueError):self.review()
        r=self.review(decision='NEEDS_DATA');self.assertEqual(r['decision'],'NEEDS_DATA')

    def test_core_plan_reports_reviews_for_selected_sources_without_accepting(self):
        from engineering.local_app.worker import Worker
        self.review();job=self.store.enqueue(self.session,'ТЗ',[self.file['id']],mode='CORE_PLAN')
        Worker(self.store,None).run_once();r=self.store.snapshot(self.session)['jobs'][0]['result']
        self.assertIn('source_reviews',r['core_plan'],'CORE review context missing')
        summary=r['core_plan']['source_reviews'];self.assertEqual(summary['candidates'][0]['decision'],'SOURCE_CONFIRMED')
        self.assertFalse(r['acceptance_granted']);self.assertEqual(r['final_audit'],'NOT_RUN')

    def test_core_plan_rejects_changed_original_after_source_review(self):
        from engineering.local_app.worker import Worker
        self.review();Path(self.store.get_file(self.file['id'])['path']).write_bytes(b'changed')
        self.store.enqueue(self.session,'ТЗ',[self.file['id']],mode='CORE_PLAN')
        Worker(self.store,None).run_once()
        self.assertEqual(self.store.snapshot(self.session)['jobs'][0]['state'],'FAILED')

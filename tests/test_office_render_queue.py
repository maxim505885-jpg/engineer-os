import hashlib,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from engineering.local_app.store import Store
from engineering.local_app.files import preserve_file
from engineering.local_app.engineering_jobs import enqueue_engineering,revision,catalog
from engineering.local_app.worker import Worker

class OfficeRenderQueueTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.store=Store(Path(self.tmp.name));self.sid=self.store.create_session()['id'];self.file=preserve_file(self.store,self.sid,'owned.docx',b'PK\x03\x04owned fixture')
    def configure(self):
        (self.store.root/'office-renderer.json').write_text(json.dumps(dict(bundle_root=str(self.store.root/'bundle'),manifest_sha256='a'*64)))
    def enqueue(self):
        return enqueue_engineering(self.store,self.sid,tool='DOCUMENT_RENDER',input_file_ids=[self.file['id']],options={},expected_revision=revision(self.store,self.sid))
    def test_unconfigured_renderer_is_not_available(self):
        tool=next(x for x in catalog(self.store,self.sid)['tools'] if x['tool']=='DOCUMENT_RENDER');self.assertFalse(tool['available'])
        with self.assertRaises(ValueError):self.enqueue()
    def test_durable_job_keeps_original_and_unverified_derived_lineage(self):
        self.configure();job=self.enqueue();pdf=b'%PDF-1.7\nowned fixture\n%%EOF\n';lineage=dict(source_sha256=self.file['sha256'],derived_sha256=hashlib.sha256(pdf).hexdigest(),scope='DERIVED_UNVERIFIED',acceptance_granted=False)
        with patch('engineering.local_app.office_render_process.render_office',return_value=(pdf,lineage)) as renderer:Worker(self.store,None).run_once()
        snapshot=self.store.snapshot(self.sid);finished=next(x for x in snapshot['jobs'] if x['id']==job['id']);self.assertEqual(finished['state'],'SUCCEEDED');self.assertTrue(renderer.called)
        result=finished['result']['engineering_run']['result'];derived=self.store.get_file(result['derived_file_id']);self.assertEqual(derived['source_metadata']['kind'],'DERIVED_OFFICE_PDF');self.assertEqual(derived['source_metadata']['original_file_id'],self.file['id']);self.assertEqual(derived['sha256'],lineage['derived_sha256']);self.assertEqual(len(snapshot['files']),2);self.assertFalse(finished['result']['acceptance_granted']);self.assertEqual(snapshot['evidence'],[]);self.assertEqual(hashlib.sha256(Path(self.store.get_file(self.file['id'])['path']).read_bytes()).hexdigest(),self.file['sha256'])
    def test_failed_conversion_retains_diagnostic_without_pdf_or_evidence(self):
        from engineering.local_app.office_render_process import OfficeRenderError
        self.configure();job=self.enqueue()
        diagnostic=dict(scope='UNVERIFIED_WORKER_DIAGNOSTIC',acceptance_granted=False,guest_failure=dict(code=1,error='GuestInputError',detail='Office timeout'))
        with patch('engineering.local_app.office_render_process.render_office',side_effect=OfficeRenderError('OFFICE_RESULT_INVALID',diagnostic)):
            Worker(self.store,None).run_once()
        snapshot=self.store.snapshot(self.sid);failed=next(x for x in snapshot['jobs'] if x['id']==job['id'])
        self.assertEqual(failed['state'],'FAILED')
        self.assertEqual(failed['result']['office_render_failure']['diagnostic'],diagnostic)
        self.assertIn('engineering_run',failed['result'])
        self.assertEqual(len(snapshot['files']),1);self.assertEqual(snapshot['evidence'],[])
        self.assertFalse(failed['result']['acceptance_granted'])
    def test_malformed_guest_unicode_still_reaches_failed_state(self):
        from engineering.local_app.office_render_process import OfficeRenderError,_failure_diagnostic
        self.configure();job=self.enqueue()
        raw=b'ENGINEER_OFFICE_RESULT {"code":1,"error":"GuestInputError","detail":"\\ud800"}\n'
        diagnostic=_failure_diagnostic(raw,self.file['sha256'],'a'*64,dict(reason='EXITED',exit_code=0))
        with patch('engineering.local_app.office_render_process.render_office',side_effect=OfficeRenderError('OFFICE_RESULT_INVALID',diagnostic)):
            self.assertTrue(Worker(self.store,None).run_once())
        failed=next(x for x in self.store.snapshot(self.sid)['jobs'] if x['id']==job['id'])
        self.assertEqual(failed['state'],'FAILED')
        self.assertNotIn('guest_failure',failed['result']['office_render_failure']['diagnostic'])
    def test_cancelled_queue_does_not_invoke_converter(self):
        self.configure();job=self.enqueue();self.store.cancel(self.sid,job['id'])
        with patch('engineering.local_app.office_render_process.render_office') as renderer:Worker(self.store,None).run_once()
        renderer.assert_not_called();self.assertEqual(len(self.store.snapshot(self.sid)['files']),1)
if __name__=='__main__':unittest.main()

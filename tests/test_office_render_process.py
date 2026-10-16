import base64,hashlib,json,tempfile,threading,unittest
from pathlib import Path
from unittest.mock import patch
from engineering.local_app.office_render_process import render_office,OfficeRenderError

class OfficeRenderProcessTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        self.source=self.root/'owned.docx';self.source.write_bytes(b'PK\x03\x04owned fixture');self.sha=hashlib.sha256(self.source.read_bytes()).hexdigest();self.stop=threading.Event()
        self.engine=self.root/'qemu';self.engine.mkdir();self.image=self.root/'worker.qcow2';self.image.write_bytes(b'owned image');self.seed=self.root/'worker-seed.iso';self.seed.write_bytes(b'owned seed')
        self.bundle=dict(root=self.root,engine=self.engine,image=self.image,seed=self.seed,files={'worker.qcow2':hashlib.sha256(self.image.read_bytes()).hexdigest(),'worker-seed.iso':hashlib.sha256(self.seed.read_bytes()).hexdigest()},manifest_sha256='a'*64,guest_worker_sha256='b'*64)
        self.pdf=b'%PDF-1.7\nowned fixture\n%%EOF\n'
    def invoke(self,effect=None,raw_override=None):
        def execute(command,engine,stage,**options):
            self.assertEqual(options['timeout_seconds'],450)
            self.assertIn('-nic',command);self.assertEqual(command[command.index('-nic')+1],'none');self.assertNotIn('-virtfs',command)
            self.assertEqual(json.loads((stage/'request.json').read_text())['source_sha256'],self.sha)
            raw=('ENGINEER_INPUT_SHA256 '+self.sha+'\nENGINEER_OFFICE_RESULT {"code":0}\nENGINEER_PDF_SHA256 '+hashlib.sha256(self.pdf).hexdigest()+'\nENGINEER_PDF_BEGIN\n'+base64.b64encode(self.pdf).decode()+'\nENGINEER_PDF_END\n').encode()
            if raw_override is not None:raw=raw_override
            target=stage/'out/results.log';target.write_bytes(raw)
            if effect:effect(target)
            return dict(reason='EXITED',exit_code=0,outputs={'out/results.log':{'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}})
        with patch('engineering.local_app.office_render_process.verify_bundle',return_value=self.bundle),patch('engineering.local_app.office_render_process.run_contained',side_effect=execute):
            return render_office(self.source,self.sha,'.docx',bundle_root=self.root,manifest_sha256='a'*64,stop=self.stop)
    def test_guest_failure_retains_bounded_unverified_diagnostic(self):
        raw=b'ENGINEER_OFFICE_RESULT {"code":1,"error":"GuestInputError","detail":"Office timeout"}\n'
        with self.assertRaises(OfficeRenderError) as caught:self.invoke(raw_override=raw)
        diagnostic=caught.exception.diagnostic
        self.assertEqual(diagnostic['guest_failure']['detail'],'Office timeout')
        self.assertFalse(diagnostic['acceptance_granted'])
        self.assertEqual(diagnostic['source_sha256'],self.sha)
        self.assertEqual(diagnostic['result_sha256'],hashlib.sha256(raw).hexdigest())
    def test_ambiguous_failure_is_not_interpreted(self):
        raw=b'ENGINEER_OFFICE_RESULT {"code":1,"code":0,"detail":"fake"}\n'
        with self.assertRaises(OfficeRenderError) as caught:self.invoke(raw_override=raw)
        self.assertNotIn('guest_failure',caught.exception.diagnostic)
    def test_small_unparsed_failure_keeps_exact_bounded_bytes(self):
        import base64
        raw=b'unknown diagnostic\r\n'
        with self.assertRaises(OfficeRenderError) as caught:self.invoke(raw_override=raw)
        self.assertEqual(base64.b64decode(caught.exception.diagnostic['result_base64']),raw)
        self.assertNotIn('guest_failure',caught.exception.diagnostic)
    def test_large_invalid_stream_is_hashed_without_copying_into_diagnostic(self):
        raw=b'x'*4097
        with self.assertRaises(OfficeRenderError) as caught:self.invoke(raw_override=raw)
        self.assertNotIn('result_base64',caught.exception.diagnostic)
        self.assertEqual(caught.exception.diagnostic['result_bytes'],4097)
        self.assertEqual(caught.exception.diagnostic['result_sha256'],hashlib.sha256(raw).hexdigest())
    def test_surrogate_failure_text_is_not_retained(self):
        raw=b'ENGINEER_OFFICE_RESULT {"code":1,"error":"GuestInputError","detail":"\\ud800"}\n'
        with self.assertRaises(OfficeRenderError) as caught:self.invoke(raw_override=raw)
        self.assertNotIn('guest_failure',caught.exception.diagnostic)
        json.dumps(caught.exception.diagnostic,ensure_ascii=False).encode('utf-8')
    def test_owned_source_staged_and_result_bound_without_acceptance(self):
        data,receipt=self.invoke();self.assertEqual(data,self.pdf);self.assertEqual(receipt['source_sha256'],self.sha);self.assertFalse(receipt['acceptance_granted']);self.assertEqual(hashlib.sha256(self.source.read_bytes()).hexdigest(),self.sha)
    def test_changed_original_rejected_after_worker(self):
        with self.assertRaises(OfficeRenderError):self.invoke(lambda target:self.source.write_bytes(b'changed'))
    def test_changed_serial_rejected(self):
        with self.assertRaises(OfficeRenderError):self.invoke(lambda target:target.write_bytes(b'changed'))
    def test_cancel_after_worker_prevents_result(self):
        with self.assertRaises(OfficeRenderError):self.invoke(lambda target:self.stop.set())
if __name__=='__main__':unittest.main()

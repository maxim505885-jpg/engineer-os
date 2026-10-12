"""Independent regression checks for isolated region reads and history validation."""
import copy
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

import fitz
from engineering.local_app import region_history as history
from engineering.local_app.files import preserve_file
from engineering.local_app.region_readback import recognize
from engineering.local_app.store import Store


class RegionProcessSafetyTests(unittest.TestCase):
    def setUp(self):
        self.folder=tempfile.TemporaryDirectory();self.addCleanup(self.folder.cleanup)
        self.root=Path(self.folder.name)
        self.store=Store(self.root/'data')
        self.sid=self.store.create_session('Region safety')['id']
        with fitz.open() as doc:
            page=doc.new_page(width=200,height=150)
            page.insert_text((30,60),'VALUE 56320',fontsize=12)
            self.raw=doc.tobytes()
        self.file=preserve_file(self.store,self.sid,'safety.pdf',self.raw)
        self.file=self.store.get_file(self.file['id'])
        self.request=dict(page=1,bbox=[20,35,160,80],expected_sha256=self.file['sha256'],ocr=False)

    def valid_result(self):
        result=recognize(self.file['path'],1,self.request['bbox'],self.file['sha256'])
        result['process_isolated']=True
        return result

    def stored_count(self):
        with self.store.connection() as db:
            return db.execute('SELECT count(*) FROM source_region_reads').fetchone()[0]

    def test_wrong_worker_identity_status_and_raster_are_never_persisted(self):
        valid=self.valid_result()
        changes=[dict(page_no=999),dict(source_bbox=[0,0,1,1]),dict(coordinate_space='FOREIGN'),
                 dict(source_bytes=len(self.raw)+1),dict(quality_verified=True),dict(page_complete=True),
                 dict(document_complete=True),dict(acceptance_granted=True),dict(process_isolated=False),
                 dict(scope='ENGINEERING_EVIDENCE'),dict(ocr_blocks=[dict(text='invented')])]
        invalid=copy.deepcopy(valid);invalid['rendered_region']['png_sha256']='0'*64
        cases=[dict(valid,**change) for change in changes]+[invalid]
        for result in cases:
            with self.subTest(result={k:v for k,v in result.items() if k in {'page_no','quality_verified','source_bbox','scope'}}):
                with patch.object(history,'_run',return_value=result),self.assertRaises(ValueError):
                    history.read_region(self.store,self.sid,self.file['id'],self.request)
                self.assertEqual(self.stored_count(),0)
        self.assertEqual(Path(self.file['path']).read_bytes(),self.raw)

    def test_render_provenance_and_enabled_ocr_input_must_match_request(self):
        valid=self.valid_result()
        for changed in ({'source_sha256':'0'*64},{'page_no':999},{'coordinate_space':'FOREIGN'}):
            invalid=copy.deepcopy(valid)
            invalid['rendered_region'].update(changed)
            with self.subTest(raster=changed),patch.object(history,'_run',return_value=invalid),self.assertRaises(ValueError):
                history.read_region(self.store,self.sid,self.file['id'],self.request)
        enabled=dict(self.request,ocr=True)
        with patch.object(history,'_run',return_value=valid),self.assertRaisesRegex(ValueError,'OCR'):
            history.read_region(self.store,self.sid,self.file['id'],enabled)
        self.assertEqual(self.stored_count(),0)

    def test_real_isolated_worker_preserves_exact_source_and_selection(self):
        result=history._run(self.file,self.request)
        history._validate(result,self.file,self.request)
        self.assertTrue(result['process_isolated'])
        self.assertEqual(result['page_no'],1)
        self.assertEqual(result['source_bbox'],[20,35,160,80])
        self.assertIn('56320',' '.join(w['text'] for w in result['native_words']))
        self.assertFalse(result['acceptance_granted'])
        self.assertEqual(Path(self.file['path']).read_bytes(),self.raw)

    def test_optional_psm_binding_survives_real_worker_save_and_reload(self):
        for psm in (7,11):
            with self.subTest(psm=psm):
                request=dict(self.request,ocr_psm=psm)
                item=history.read_region(self.store,self.sid,self.file['id'],request)
                self.assertEqual(item['result']['request_binding'],request)
                reloaded=history.get_region(self.store,self.sid,self.file['id'],item['id'])
                self.assertEqual(reloaded,item)
                self.assertFalse(reloaded['result']['quality_verified'])

    def test_invalid_psm_profiles_never_start_worker_or_write_history(self):
        for psm in (True,3,99,11.0,'11',None):
            with self.subTest(psm=psm),patch.object(history,'_run') as worker,self.assertRaisesRegex(ValueError,'OCR profile'):
                history.read_region(self.store,self.sid,self.file['id'],dict(self.request,ocr_psm=psm))
            worker.assert_not_called()
            self.assertEqual(self.stored_count(),0)

    def test_saved_request_binding_disagreement_rejects_hash_valid_record(self):
        item=history.read_region(self.store,self.sid,self.file['id'],self.request)
        for changed in ({'page':2},{'expected_sha256':'0'*64},{'ocr_psm':3},{'ocr':'false'}):
            altered=copy.deepcopy(item['result'])
            altered['request_binding'].update(changed)
            serialized=json.dumps(altered,ensure_ascii=False,sort_keys=True,separators=(',',':'))
            with self.store.connection() as db:
                db.execute('UPDATE source_region_reads SET result=?,result_sha256=? WHERE id=?',
                           (serialized,hashlib.sha256(serialized.encode()).hexdigest(),item['id']))
            with self.subTest(binding=changed),self.assertRaises(ValueError):
                history.get_region(self.store,self.sid,self.file['id'],item['id'])
        self.assertEqual(Path(self.file['path']).read_bytes(),self.raw)

    def test_actual_history_gets_obey_shared_concurrency_budget(self):
        from tests.test_region_readback_http import RegionHTTPTests
        http=RegionHTTPTests();http.setUp()
        try:
            sid,file,original,route=http.source()
            http.server.preview_slots.acquire();http.server.preview_slots.acquire()
            try:
                self.assertEqual(http.request('GET',route)[0],429)
                self.assertEqual(http.request('GET',route+'/'+sid)[0],429)
            finally:
                http.server.preview_slots.release();http.server.preview_slots.release()
            self.assertEqual(http.request('GET',route)[0],200)
        finally:http.doCleanups()

    def test_source_growth_after_fstat_is_rejected_without_reading_past_size(self):
        original_fstat=os.fstat;changed=False
        def grow_after_snapshot(descriptor):
            nonlocal changed
            result=original_fstat(descriptor)
            if not changed and result.st_size==len(self.raw):
                changed=True
                with Path(self.file['path']).open('ab') as stream:stream.write(b'EXTRA SOURCE BYTES')
            return result
        with patch.object(history.os,'fstat',side_effect=grow_after_snapshot),self.assertRaisesRegex(ValueError,'grew'):
            history._source(self.store,self.sid,self.file['id'])
        self.assertTrue(changed)
        self.assertEqual(self.stored_count(),0)

    def test_source_verification_deadline_is_checked_before_reading(self):
        with patch.object(history.time,'monotonic',side_effect=[0,11]),self.assertRaisesRegex(ValueError,'verification timeout'):
            history._source(self.store,self.sid,self.file['id'])
        self.assertEqual(Path(self.file['path']).read_bytes(),self.raw)

    def test_actual_timeout_kills_worker_and_ocr_like_descendant(self):
        pid_file=self.root/'descendant.pid'
        code="import subprocess,sys,time,pathlib; child=subprocess.Popen([sys.executable,'-c','import time; time.sleep(30)'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); pathlib.Path(sys.argv[1]).write_text(str(child.pid)); time.sleep(30)"
        original_popen=subprocess.Popen;workers=[]
        def launch(_command,**kwargs):
            if list(_command[1:3])!=['-m','engineering.local_app.region_process']:
                return original_popen(_command,**kwargs)
            child=original_popen([sys.executable,'-c',code,str(pid_file)],**kwargs)
            workers.append(child)
            return child
        started=time.monotonic()
        try:
            with patch.object(history,'PROCESS_TIMEOUT',1),patch.object(history.subprocess,'Popen',side_effect=launch):
                with self.assertRaisesRegex(ValueError,'REGION_TIMEOUT: no result saved'):
                    history._run(self.file,self.request)
            self.assertLess(time.monotonic()-started,11 if os.name=='nt' else 4)
            self.assertIsNotNone(workers[0].poll())
            self.assertTrue(pid_file.is_file(),'The real descendant must have started before timeout')
            descendant=int(pid_file.read_text())
            stop=time.monotonic()+2
            while self._active(descendant) and time.monotonic()<stop:time.sleep(.02)
            self.assertFalse(self._active(descendant),'Process-tree timeout must terminate descendants')
            self.assertEqual(self.stored_count(),0)
        finally:
            if workers:
                self._terminate_tree(workers[0].pid)
                if workers[0].poll() is None:workers[0].kill()
                workers[0].wait(timeout=5)
            if pid_file.exists():self._terminate_tree(int(pid_file.read_text()))

    @staticmethod
    def _terminate_tree(pid):
        if os.name=='nt':
            command=[str(Path(os.environ.get('SYSTEMROOT',r'C:\Windows'))/'System32'/'taskkill.exe'),'/PID',str(pid),'/T','/F']
            subprocess.run(command,shell=False,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=5,check=False)
        else:
            try:os.killpg(pid,signal.SIGKILL)
            except ProcessLookupError:
                try:os.kill(pid,signal.SIGKILL)
                except ProcessLookupError:pass

    @staticmethod
    def _active(pid):
        if os.name=='nt':
            import ctypes
            from ctypes import wintypes
            kernel=ctypes.WinDLL('kernel32',use_last_error=True)
            query=kernel.OpenProcess
            query.argtypes=(wintypes.DWORD,wintypes.BOOL,wintypes.DWORD)
            query.restype=wintypes.HANDLE
            exit_code=kernel.GetExitCodeProcess
            exit_code.argtypes=(wintypes.HANDLE,ctypes.POINTER(wintypes.DWORD))
            exit_code.restype=wintypes.BOOL
            close=kernel.CloseHandle;close.argtypes=(wintypes.HANDLE,);close.restype=wintypes.BOOL
            handle=query(0x1000,False,pid)
            if not handle:
                error=ctypes.get_last_error()
                if error==87:return False
                raise ctypes.WinError(error)
            try:
                code=wintypes.DWORD()
                if not exit_code(handle,ctypes.byref(code)):raise ctypes.WinError(ctypes.get_last_error())
                return code.value==259
            finally:close(handle)
        # An orphan zombie is terminated and consumes no CPU; Linux PID 1 may
        # reap it later. Checking kill(pid,0) alone would falsely report it live.
        status=Path('/proc')/str(pid)/'stat'
        if status.exists():
            try:return status.read_text().rsplit(')',1)[1].split()[0]!='Z'
            except FileNotFoundError:return False
        try:os.kill(pid,0);return True
        except ProcessLookupError:return False

    def test_actual_hung_native_worker_returns_with_no_partial_history(self):
        original_popen=subprocess.Popen
        def launch(_command,**kwargs):
            if list(_command[1:3])!=['-m','engineering.local_app.region_process']:
                return original_popen(_command,**kwargs)
            return original_popen([sys.executable,'-c','import time; time.sleep(30)'],**kwargs)
        started=time.monotonic()
        with patch.object(history,'PROCESS_TIMEOUT',.3),patch.object(history.subprocess,'Popen',side_effect=launch):
            with self.assertRaisesRegex(ValueError,'REGION_TIMEOUT: no result saved'):
                history.read_region(self.store,self.sid,self.file['id'],self.request)
        self.assertLess(time.monotonic()-started,11 if os.name=='nt' else 3)
        self.assertEqual(self.stored_count(),0)
        self.assertEqual(Path(self.file['path']).read_bytes(),self.raw)

"""Synthetic DXF workers: resource containment and immutable source identity."""
import hashlib
import importlib.util
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

@unittest.skipUnless(importlib.util.find_spec('ezdxf'),'Optional CAD profile absent')
class CadWorkerTests(unittest.TestCase):
    def setUp(self):
        import ezdxf
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/'source.dxf'
        doc=ezdxf.new('R2010',units=4);doc.modelspace().add_line((0,0),(10,0));doc.saveas(self.path)
        self.raw=self.path.read_bytes();self.sha=hashlib.sha256(self.raw).hexdigest()
    def run_cad(self,**changes):
        try:from engineering.local_app.cad_process import run_cad
        except ImportError:self.fail('Bounded CAD worker unavailable')
        request=dict(tool='CAD_INVENTORY',sources=[(self.path,self.sha)],stop=threading.Event());request.update(changes)
        return run_cad(**request)
    def test_real_inventory_is_bounded_and_never_accepts(self):
        result=self.run_cad();self.assertEqual(result['entity_counts'],{'LINE':1})
        self.assertEqual(result['data_class'],'PROJECT');self.assertFalse(result['acceptance_granted'])
        self.assertTrue(result['resource_boundary']['child_isolated']);self.assertEqual(self.path.read_bytes(),self.raw)
        self.assertEqual(result['entities'][0]['type'],'LINE')
    def test_real_difference_locates_changed_handle(self):
        import ezdxf
        other=self.path.with_name('changed.dxf');doc=ezdxf.readfile(self.path);doc.modelspace()[0].dxf.end=(11,0,0);doc.saveas(other)
        result=self.run_cad(tool='CAD_DIFF',sources=[(self.path,self.sha),(other,hashlib.sha256(other.read_bytes()).hexdigest())])
        self.assertEqual(result['status'],'BLOCK');self.assertEqual(result['changed_by_type'],{'LINE':1})
        self.assertFalse(result['dwg_equivalence_verified']);self.assertFalse(result['acceptance_granted'])
    def test_wrong_hash_count_format_or_cancel_does_not_launch(self):
        with patch('engineering.local_app.calculation_process._run_request') as child:
            stop=threading.Event();stop.set()
            for changes in ({'sources':[(self.path,'0'*64)]},{'sources':[]},{'tool':'DWG_CONVERT'},{'stop':stop}):
                with self.subTest(changes=changes),self.assertRaises(ValueError):self.run_cad(**changes)
            child.assert_not_called()
    def test_change_during_child_is_rejected(self):
        def child(*args,**kwargs):self.path.write_bytes(b'changed');return {'acceptance_granted':False}
        with patch('engineering.local_app.calculation_process._run_request',side_effect=child):
            with self.assertRaises(ValueError):self.run_cad()
    def test_intake_rechecks_size_during_read(self):
        import io
        from engineering.cad.intake import inspect_cad
        small=self.path.with_name('growing.dxf');small.write_bytes(b'x')
        with patch('engineering.cad.intake.MAX_BYTES',64),patch.object(Path,'open',return_value=io.BytesIO(b'x'*65)):
            with self.assertRaises(ValueError):inspect_cad(small)
    def test_child_receives_copy_and_not_original_path(self):
        def child(tool,data,stop,**kwargs):
            staged=Path(data['sources'][0]['path']);self.assertNotEqual(staged,self.path)
            self.assertEqual(staged.read_bytes(),self.raw);self.assertEqual(kwargs['timeout_seconds'],30)
            return {'acceptance_granted':False}
        with patch('engineering.local_app.calculation_process._run_request',side_effect=child):self.run_cad()
    def test_real_child_output_limit_fails_closed(self):
        with patch('engineering.local_app.calculation_process.MAX_OUTPUT',100):
            with self.assertRaises(ValueError):self.run_cad()
    def test_census_limit_never_reports_complete(self):
        from engineering.local_app.cad_process import evaluate_staged
        with patch('engineering.cad.dxf_workflow.MAX_INVENTORY_ENTITIES',0):
            result=evaluate_staged('CAD_INVENTORY',dict(sources=[dict(path=str(self.path),sha256=self.sha)]))
        self.assertEqual(result['status'],'BLOCK');self.assertFalse(result.get('inventory_read_complete',False))
        self.assertFalse(result['acceptance_granted'])
    def test_parent_hash_is_bounded_even_if_file_grows(self):
        try:from engineering.local_app.cad_process import _checked_hash
        except ImportError:self.fail('Bounded CAD worker unavailable')
        import io
        with patch('engineering.local_app.cad_process.MAX_SOURCE_BYTES',len(self.raw)),patch.object(Path,'open',return_value=io.BytesIO(self.raw+b'x')):
            with self.assertRaisesRegex(ValueError,'CAD_SOURCE_SIZE_LIMIT'):_checked_hash(self.path,self.sha)

class CadQueueTests(unittest.TestCase):
    def test_queue_inventory_and_difference_preserve_project_scope(self):
        if importlib.util.find_spec('ezdxf') is None:self.skipTest('Optional CAD profile absent')
        import ezdxf
        from engineering.local_app.store import Store
        from engineering.local_app.files import preserve_file
        from engineering.local_app.engineering_jobs import enqueue_engineering,revision
        from engineering.local_app.worker import Worker
        with tempfile.TemporaryDirectory() as tmp:
            store=Store(Path(tmp)/'data');sid=store.create_session()['id'];path=Path(tmp)/'a.dxf'
            doc=ezdxf.new('R2010',units=4);doc.modelspace().add_line((0,0),(10,0));doc.saveas(path)
            source=preserve_file(store,sid,'a.dxf',path.read_bytes())
            try:enqueue_engineering(store,sid,tool='CAD_INVENTORY',input_file_ids=[source['id']],options={},expected_revision=revision(store,sid))
            except ValueError as exc:self.fail('CAD queue unavailable: '+str(exc))
            Worker(store,None).run_once();snap=store.snapshot(sid);job=snap['jobs'][0];self.assertEqual(job['state'],'SUCCEEDED',job)
            self.assertEqual(job['result']['engineering_run']['input_data_class'],'PROJECT');self.assertEqual(snap['evidence'],[])
            self.assertTrue(job['result']['engineering_run']['result']['resource_boundary']['child_isolated'])
            other=preserve_file(store,sid,'b.dxf',path.read_bytes())
            enqueue_engineering(store,sid,tool='CAD_DIFF',input_file_ids=[source['id'],other['id']],options={},expected_revision=revision(store,sid))
            Worker(store,None).run_once();job=store.snapshot(sid)['jobs'][0]
            self.assertEqual(job['state'],'SUCCEEDED',job);self.assertEqual(job['result']['engineering_run']['result']['status'],'PASS')
            self.assertFalse(job['result']['acceptance_granted'])
            for changes in (dict(tool='DWG_CONVERT'),dict(options={'units':'mm'}),dict(input_file_ids=[source['id'],other['id']])):
                request=dict(tool='CAD_INVENTORY',input_file_ids=[source['id']],options={},expected_revision=revision(store,sid));request.update(changes)
                with self.assertRaises(ValueError):enqueue_engineering(store,sid,**request)

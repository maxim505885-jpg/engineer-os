"""Real disposable IFC parsing plus source/boundary negatives."""
import hashlib
import importlib.util
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch


@unittest.skipUnless(importlib.util.find_spec('ifcopenshell'), 'Optional IFC profile absent')
class IfcWorkerTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/'model.ifc'
        self.raw=(Path(__file__).parent/'fixtures/bim/reference.ifc').read_bytes()
        self.path.write_bytes(self.raw);self.sha=hashlib.sha256(self.raw).hexdigest()

    def run_ifc(self, **changes):
        from engineering.local_app.ifc_process import run_ifc
        request=dict(tool='IFC_INVENTORY',sources=[(self.path,self.sha)],stop=threading.Event())
        request.update(changes)
        return run_ifc(**request)

    def test_real_inventory_uses_resource_boundary_and_preserves_source(self):
        result=self.run_ifc()
        self.assertEqual(result['status'],'UNCERTAINTY',result)
        self.assertTrue(result['elements'])
        self.assertFalse(result['acceptance_granted'])
        self.assertEqual(result['data_class'],'PROJECT')
        self.assertTrue(result['resource_boundary']['child_isolated'])
        self.assertFalse(result['resource_boundary']['network_isolation_verified'])
        self.assertEqual(self.path.read_bytes(),self.raw)

    def test_wrong_identity_or_count_refused_before_child(self):
        for changes in ({'sources':[(self.path,'0'*64)]},{'sources':[]},{'tool':'IFC_EXECUTE'}):
            with self.subTest(changes=changes),self.assertRaises(ValueError):self.run_ifc(**changes)

    def test_growth_after_stat_is_bounded_during_parent_hash(self):
        import io
        from engineering.local_app.ifc_process import _checked_hash
        small=Path(self.tmp.name)/'growing.ifc';small.write_bytes(b'x'*32)
        with patch('engineering.local_app.ifc_process.MAX_SOURCE_BYTES',64),patch.object(Path,'open',return_value=io.BytesIO(b'x'*65)):
            with self.assertRaisesRegex(ValueError,'IFC_SOURCE_SIZE_LIMIT'):
                _checked_hash(small,hashlib.sha256(b'x'*32).hexdigest())

    def test_actual_low_memory_child_fails_closed(self):
        from engineering.local_app.calculation_process import probe_memory_limit
        with patch('engineering.local_app.calculation_process.MEMORY_BYTES',16*1024**2):
            with self.assertRaises(ValueError):probe_memory_limit(threading.Event())
        self.assertEqual(self.path.read_bytes(),self.raw)

    def test_same_fixed_allocation_succeeds_at_normal_limit(self):
        from engineering.local_app.calculation_process import probe_memory_limit
        result=probe_memory_limit(threading.Event())
        self.assertEqual(result['allocated_bytes'],64*1024**2)
        self.assertFalse(result['acceptance_granted'])

    def test_pre_cancelled_request_never_launches_child(self):
        stop=threading.Event();stop.set()
        with patch('engineering.local_app.calculation_process._run_request') as child:
            with self.assertRaisesRegex(ValueError,'IFC_CANCELLED'):self.run_ifc(stop=stop)
            child.assert_not_called()

    def test_original_change_during_child_invalidates_result(self):
        def changed(*args):
            self.path.write_bytes(b'changed')
            return {'status':'UNCERTAINTY','acceptance_granted':False}
        with patch('engineering.local_app.calculation_process._run_request',side_effect=changed):
            with self.assertRaisesRegex(ValueError,'IFC_SOURCE_CHANGED'):self.run_ifc()

    def test_http_and_queue_cannot_start_parallel_native_workers(self):
        from concurrent.futures import ThreadPoolExecutor
        started=threading.Event();release=threading.Event()
        def hold(*args):
            started.set();release.wait(5)
            return {'status':'UNCERTAINTY','acceptance_granted':False}
        with patch('engineering.local_app.calculation_process._run_request',side_effect=hold),ThreadPoolExecutor(max_workers=1) as executor:
            future=executor.submit(self.run_ifc)
            try:
                self.assertTrue(started.wait(3))
                with self.assertRaisesRegex(ValueError,'IFC_WORKER_BUSY'):self.run_ifc()
            finally:release.set();future.result(timeout=5)

    def test_source_bound_queue_keeps_project_class_without_acceptance(self):
        from engineering.local_app.store import Store
        from engineering.local_app.files import preserve_file
        from engineering.local_app.engineering_jobs import enqueue_engineering,revision
        from engineering.local_app.worker import Worker
        store=Store(Path(self.tmp.name)/'data');sid=store.create_session()['id']
        source=preserve_file(store,sid,'model.ifc',self.raw)
        enqueue_engineering(store,sid,tool='IFC_INVENTORY',input_file_ids=[source['id']],options={},expected_revision=revision(store,sid))
        Worker(store,None).run_once();snap=store.snapshot(sid);job=snap['jobs'][0]
        self.assertEqual(job['state'],'SUCCEEDED',job)
        run=job['result']['engineering_run']
        self.assertEqual(run['input_data_class'],'PROJECT')
        self.assertEqual(run['result']['source_sha256'],source['sha256'])
        self.assertFalse(run['acceptance_granted']);self.assertEqual(snap['evidence'],[])

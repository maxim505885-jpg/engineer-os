import tempfile
import threading
import unittest
from pathlib import Path


class EngineeringJobTests(unittest.TestCase):
    def setUp(self):
        from engineering.local_app.store import Store
        from engineering.local_app.files import preserve_file
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.store=Store(Path(self.tmp.name));self.sid=self.store.create_session()['id']
        self.source=preserve_file(self.store,self.sid,'dimensions.txt',b'User input: width 0.2 m, height 0.4 m. Unverified.')

    def enqueue(self,**changes):
        from engineering.local_app.engineering_jobs import enqueue_engineering,revision
        request=dict(tool='RECTANGLE',input_file_ids=[self.source['id']],options={'width_m':.2,'height_m':.4,'units':'N_m_Pa'},expected_revision=revision(self.store,self.sid))
        request.update(changes)
        return enqueue_engineering(self.store,self.sid,**request)

    def test_foreign_file_or_changed_config_refused(self):
        from engineering.local_app.files import preserve_file
        sid=self.store.create_session()['id'];foreign=preserve_file(self.store,sid,'foreign.txt',b'Other')
        with self.assertRaises(ValueError):self.enqueue(input_file_ids=[foreign['id']])
        with self.assertRaises(ValueError):self.enqueue(expected_revision='0'*64)
        self.assertEqual(self.store.snapshot(self.sid)['jobs'],[])

    def test_result_never_creates_accepted_evidence(self):
        from engineering.local_app.worker import Worker
        job=self.enqueue();Worker(self.store,None).run_once()
        snapshot=self.store.snapshot(self.sid);result=snapshot['jobs'][0]['result']
        self.assertEqual(snapshot['jobs'][0]['state'],'SUCCEEDED')
        self.assertEqual(result['engineering_run']['result']['status'],'PASS')
        self.assertAlmostEqual(result['engineering_run']['result']['results']['area_m2'],.08)
        self.assertFalse(result['acceptance_granted']);self.assertEqual(snapshot['evidence'],[])
        self.assertEqual(result['engineering_run']['input_data_class'],'ASSUMED')

    def test_source_change_blocks_before_calculation(self):
        from engineering.local_app.worker import Worker
        self.enqueue();Path(self.store.get_file(self.source['id'])['path']).write_bytes(b'Changed')
        Worker(self.store,None).run_once()
        job=self.store.snapshot(self.sid)['jobs'][0]
        self.assertEqual(job['state'],'FAILED')

    def test_cancel_preserves_source_and_request(self):
        from engineering.local_app.engineering_jobs import request_for
        job=self.enqueue();self.store.cancel(self.sid,job['id'])
        self.assertEqual(request_for(self.store,self.sid,job['id'])['options']['height_m'],.4)
        self.assertTrue(Path(self.store.get_file(self.source['id'])['path']).is_file())
        self.assertEqual(self.store.snapshot(self.sid)['jobs'][0]['state'],'CANCELLED')

    def test_request_tampering_is_detected(self):
        from engineering.local_app.engineering_jobs import request_for
        job=self.enqueue()
        with self.store.connection() as db:db.execute("UPDATE engineering_inputs SET record='{}' WHERE job_id=?",(job['id'],))
        with self.assertRaises(ValueError):request_for(self.store,self.sid,job['id'])

    def test_generic_enqueue_cannot_create_unbound_engineering_job(self):
        with self.assertRaises(ValueError):self.store.enqueue(self.sid,'Run',[self.source['id']],mode='ENGINEERING_RUN')

    def test_real_beam_child_matches_analytic_reactions(self):
        import importlib.util
        if importlib.util.find_spec('Pynite') is None:self.skipTest('Optional calculation profile absent')
        if __import__('os').name=='nt' and importlib.util.find_spec('win32job') is None:self.skipTest('Windows Job Object adapter absent')
        from engineering.local_app.worker import Worker
        self.enqueue(tool='BEAM',options=dict(length_m=6.,elastic_modulus_pa=210e9,inertia_m4=8e-6,area_m2=.003,load_n_m=1000.,units='N_m_Pa'))
        Worker(self.store,None).run_once()
        job=self.store.snapshot(self.sid)['jobs'][0]
        self.assertEqual(job['state'],'SUCCEEDED',job)
        result=job['result']['engineering_run']['result']
        self.assertEqual(result['status'],'PASS',result)
        self.assertAlmostEqual(result['results']['reaction_left_n'],3000.)
        self.assertTrue(result['resource_boundary']['child_isolated'])

    def test_context_change_and_nan_options_refused(self):
        from engineering.local_app.engineering_jobs import revision
        from engineering.local_app.files import preserve_file
        old=revision(self.store,self.sid)
        preserve_file(self.store,self.sid,'added.txt',b'New context')
        with self.assertRaises(ValueError):self.enqueue(expected_revision=old)
        with self.assertRaises(ValueError):self.enqueue(options={'width_m':float('nan')})

    def test_planar_child_preserves_independent_cantilever_solution(self):
        import importlib.util
        if importlib.util.find_spec('Pynite') is None:self.skipTest('Optional calculation profile absent')
        if __import__('os').name=='nt' and importlib.util.find_spec('win32job') is None:self.skipTest('Windows Job Object adapter absent')
        from engineering.local_app.worker import Worker
        data=dict(nodes=[dict(name='a',x_m=0.,y_m=0.,fix_x=True,fix_y=True,fix_rz=True),dict(name='b',x_m=2.,y_m=0.)],
            members=[dict(name='ab',start='a',end='b',elastic_modulus_pa=200e9,area_m2=.01,iz_m4=1e-5)],
            loads=[['b',0.,-1000.,0.]],kind='frame',units='N_m_Pa')
        self.enqueue(tool='PLANAR',options=data);Worker(self.store,None).run_once()
        job=self.store.snapshot(self.sid)['jobs'][0]
        self.assertEqual(job['state'],'SUCCEEDED',job)
        result=job['result']['engineering_run']['result']
        self.assertEqual(result['status'],'PASS',result)
        self.assertAlmostEqual(result['results']['nodes']['b']['dy_m'],-1000*8/(3*200e9*1e-5),places=10)

    @unittest.skipUnless(__import__('os').name=='nt','Windows kernel memory boundary')
    def test_windows_job_memory_limit_fails_closed(self):
        import importlib.util
        if importlib.util.find_spec('win32job') is None:self.skipTest('Windows Job Object adapter absent')
        from engineering.local_app.calculation_process import run_calculation
        from unittest.mock import patch
        data=dict(length_m=6.,elastic_modulus_pa=210e9,inertia_m4=8e-6,area_m2=.003,load_n_m=1000.,units='N_m_Pa',source_sha256='a'*64,evidence_ids=['synthetic'])
        with patch('engineering.local_app.calculation_process.MEMORY_BYTES',16*1024**2):
            with self.assertRaises((ValueError,__import__('pywintypes').error)):run_calculation('BEAM',data,threading.Event())

    def test_interrupted_calculation_retains_request_and_progress(self):
        from engineering.local_app.engineering_jobs import execute_engineering,request_for
        job=self.enqueue();claimed=self.store.claim();stop=threading.Event();stop.set()
        execute_engineering(self.store,claimed,stop);self.store.fail(job['id'],'Interrupted')
        snapshot=self.store.snapshot(self.sid)
        self.assertIsNone(snapshot['jobs'][0]['result']['engineering_run']['result'])
        self.assertEqual(request_for(self.store,self.sid,job['id'])['tool'],'RECTANGLE')

    def test_v1_migration_backed_up_before_new_job_schema(self):
        from engineering.local_app.store import Store
        import sqlite3
        with self.store.connection() as db:db.execute('DROP TABLE engineering_inputs');db.execute('PRAGMA user_version=1')
        upgraded=Store(self.store.root)
        with upgraded.connection() as db:self.assertEqual(db.execute('PRAGMA user_version').fetchone()[0],2)
        backup=sqlite3.connect(self.store.root/'history.pre-migration-v1.sqlite3')
        try:
            self.assertEqual(backup.execute('PRAGMA user_version').fetchone()[0],1)
            self.assertIsNone(backup.execute("SELECT name FROM sqlite_master WHERE name='engineering_inputs'").fetchone())
        finally:backup.close()

    def test_backup_restore_preserves_bound_request(self):
        from engineering.local_app.engineering_jobs import request_for
        from engineering.local_app.backup import create_backup,restore_backup
        from engineering.local_app.store import Store
        job=self.enqueue();self.store.cancel(self.sid,job['id'])
        destination=tempfile.TemporaryDirectory();self.addCleanup(destination.cleanup)
        archive=Path(destination.name)/'saved.zip';target=Path(destination.name)/'restored'
        create_backup(self.store.root,archive);restore_backup(archive,target)
        restored=Store(target)
        self.assertEqual(request_for(restored,self.sid,job['id']),request_for(self.store,self.sid,job['id']))

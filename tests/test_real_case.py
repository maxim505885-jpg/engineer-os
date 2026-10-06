import json
import tempfile
import unittest
from pathlib import Path

from engineering.local_app.store import Store,ReviewConflict
from engineering.local_app.files import preserve_file
from engineering.local_app.worker import Worker


class Model:
    def chat(self,messages):
        return json.dumps(dict(status='UNCERTAINTY',summary='Controlled stage-7 draft',observations=[],limitations=['Not accepted']))


class RealCaseTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.store=Store(Path(self.tmp.name));self.sid=self.store.create_session()['id']
        self.file=preserve_file(self.store,self.sid,'source.txt',b'Controlled real-case source')

    def core(self,checks=None):
        checks=checks or ['report']
        job=self.store.enqueue(self.sid,'Real engineering case',[self.file['id']],mode='CORE_RUN',requested_checks=checks)
        Worker(self.store,Model()).run_once()
        return self.store.snapshot(self.sid)['jobs'][0]

    def module(self):
        from engineering.local_app import real_case
        return real_case

    def test_case_snapshot_is_immutable_blocked_and_persistent(self):
        job=self.core()
        event=self.module().build(self.store,self.sid,job_id=job['id'],expected_revision=0)
        self.assertEqual(event['scope'],'REAL_ENGINEERING_CASE_SNAPSHOT')
        self.assertEqual(event['engineering_status'],'BLOCK')
        self.assertFalse(event['acceptance_granted']);self.assertEqual(event['final_audit'],'NOT_RUN')
        self.assertEqual(len(event['case_sha256']),64)
        report=self.module().report(self.store,self.sid)
        self.assertTrue(report['current_fresh']);self.assertEqual(report['revision'],1)
        self.assertIn('TZ_CHECKLIST_MISSING',event['stages']['requirements']['reasons'])
        restarted=self.module().report(Store(self.store.root),self.sid)
        self.assertEqual(restarted['cases'][0]['case_sha256'],event['case_sha256'])

    def test_source_role_manifest_is_validated_and_persisted(self):
        job=self.core()
        manifest={'TOR':[self.file['id']],'REPORT':[self.file['id']]}
        event=self.module().build(self.store,self.sid,job_id=job['id'],expected_revision=0,manifest=manifest)
        self.assertEqual(event['source_manifest'],manifest)
        self.assertNotIn('CASE_SOURCE_ROLES_NOT_DECLARED',event['stages']['source_identity']['reasons'])
        with self.assertRaises(ValueError):
            self.module().build(self.store,self.sid,job_id=job['id'],expected_revision=1,
                                manifest={'MODEL':['00000000-0000-0000-0000-000000000000']})

    def test_normative_case_discloses_deferred_point6_dependency(self):
        job=self.core(['normative'])
        event=self.module().build(self.store,self.sid,job_id=job['id'],expected_revision=0)
        self.assertIn('NORMATIVE_DOMAIN_PACKET_MISSING',event['stages']['domain_prerequisites']['reasons'])
        self.assertEqual(event['point7_readiness'],'BLOCK')

    def test_case_becomes_stale_when_tz_state_changes(self):
        job=self.core();self.module().build(self.store,self.sid,job_id=job['id'],expected_revision=0)
        from engineering.local_app.requirements import create_set
        create_set(self.store,self.sid,text='Check the roof')
        report=self.module().report(self.store,self.sid)
        self.assertFalse(report['current_fresh'])
        self.assertIn('TZ_STATE_CHANGED',report['cases'][-1]['stale_reasons'])

    def test_revision_guard_and_non_core_job(self):
        job=self.core();self.module().build(self.store,self.sid,job_id=job['id'],expected_revision=0)
        with self.assertRaises(ReviewConflict):
            self.module().build(self.store,self.sid,job_id=job['id'],expected_revision=0)
        other=self.store.enqueue(self.sid,'Chat',[self.file['id']],mode='CHAT')
        Worker(self.store,Model()).run_once()
        with self.assertRaises(ValueError):
            self.module().build(self.store,self.sid,job_id=other['id'],expected_revision=1)


if __name__=='__main__':
    unittest.main()

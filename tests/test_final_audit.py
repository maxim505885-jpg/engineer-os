import json
import tempfile
import unittest
from pathlib import Path

from engineering.local_app.final_audit import evaluate_case,acceptance_gate
from engineering.local_app.files import preserve_file
from engineering.local_app.store import Store,ReviewConflict
from engineering.local_app.worker import Worker


class Model:
    def chat(self,messages):
        return json.dumps(dict(status='UNCERTAINTY',summary='Controlled audit fixture',observations=[],limitations=['Not accepted']))


def ready_case():
    return dict(
        id='case-1',case_sha256='a'*64,revision=1,point7_readiness='READY_FOR_REAL_CASE_REVIEW',
        engineering_status='READY_FOR_FINAL_AUDIT',acceptance_granted=False,final_audit='NOT_RUN',
        identity=dict(core_job_id='job-1',originals=[dict(id='f1',sha256='b'*64,size=1)]),
        evidence=[dict(candidate_id='e1')],
        domain_packets=dict(packets=[]),
        stages=dict(
            source_identity=dict(status='READY',reasons=[]),
            requirements=dict(status='READY_FOR_ENGINEERING_REVIEW',reasons=[]),
            evidence=dict(status='READY_FOR_ENGINEERING_REVIEW',reasons=[]),
            specialists=dict(status='READY_FOR_CASE_QC',reasons=[]),
            domain_prerequisites=dict(status='READY_FOR_CASE_QC',reasons=[]),
            qc=dict(status='READY_FOR_REAL_CASE_REVIEW',reasons=[]),
        ),
    )


class FinalAuditContractTests(unittest.TestCase):
    def test_only_clean_fresh_case_can_be_accepted(self):
        r=evaluate_case(ready_case(),fresh=True)
        self.assertEqual(r['decision'],'ACCEPTED');self.assertTrue(r['acceptance_granted'])
        self.assertTrue(r['engineering_verified']);self.assertIsNotNone(r['acceptance_certificate'])
        self.assertEqual(len(r['audit_sha256']),64)

    def test_any_block_or_stale_case_fails_closed(self):
        case=ready_case();case['stages']['domain_prerequisites']={'status':'BLOCK','reasons':['POINT6_SOLVER_DECISION_PENDING']}
        r=evaluate_case(case,fresh=True)
        self.assertEqual(r['decision'],'BLOCK');self.assertFalse(r['acceptance_granted'])
        self.assertIn('POINT6_SOLVER_DECISION_PENDING',r['blocker_codes'])
        stale=evaluate_case(ready_case(),fresh=False,stale_reasons=['DOMAIN_STATE_CHANGED'])
        self.assertEqual(stale['decision'],'BLOCK');self.assertIn('DOMAIN_STATE_CHANGED',stale['blocker_codes'])

    def test_preexisting_acceptance_or_missing_basis_is_rejected(self):
        case=ready_case();case['acceptance_granted']=True;case['evidence']=[]
        r=evaluate_case(case,fresh=True)
        self.assertEqual(r['decision'],'BLOCK')
        self.assertIn('PREEXISTING_ACCEPTANCE_NOT_ALLOWED',r['blocker_codes'])
        self.assertIn('EVIDENCE_ACCEPTANCE_BASIS_MISSING',r['blocker_codes'])


class FinalAuditStoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.store=Store(Path(self.tmp.name));self.sid=self.store.create_session()['id']
        self.file=preserve_file(self.store,self.sid,'source.txt',b'Controlled source')
        job=self.store.enqueue(self.sid,'Stage 8 blocked case',[self.file['id']],mode='CORE_RUN',requested_checks=['report'])
        Worker(self.store,Model()).run_once()
        self.job=self.store.snapshot(self.sid)['jobs'][0]
        from engineering.local_app.real_case import build
        self.case=build(self.store,self.sid,job_id=self.job['id'],expected_revision=0,
                        manifest={'TOR':[self.file['id']],'REPORT':[self.file['id']]})

    def test_blocked_case_audit_is_persistent_and_never_accepts(self):
        from engineering.local_app.final_audit import build,report
        event=build(self.store,self.sid,case_id=self.case['id'],expected_revision=0)
        self.assertEqual(event['decision'],'BLOCK');self.assertFalse(event['acceptance_granted'])
        self.assertEqual(event['final_audit'],'COMPLETED')
        state=report(self.store,self.sid)
        self.assertEqual(state['status'],'BLOCK');self.assertFalse(state['acceptance_granted'])
        self.assertFalse(acceptance_gate(self.store,self.sid))
        restarted=report(Store(self.store.root),self.sid)
        self.assertEqual(restarted['audits'][0]['audit_sha256'],event['audit_sha256'])

    def test_revision_guard_and_case_change_invalidate_audit(self):
        from engineering.local_app.final_audit import build,report
        build(self.store,self.sid,case_id=self.case['id'],expected_revision=0)
        with self.assertRaises(ReviewConflict):
            build(self.store,self.sid,case_id=self.case['id'],expected_revision=0)
        from engineering.local_app.requirements import create_set
        create_set(self.store,self.sid,text='Changed requirement')
        state=report(self.store,self.sid)
        self.assertFalse(state['current_fresh']);self.assertFalse(state['acceptance_granted'])
        self.assertIn('TZ_STATE_CHANGED',state['audits'][-1]['stale_reasons'])


if __name__=='__main__':
    unittest.main()

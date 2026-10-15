"""Readiness and caller JSON are not an engineering acceptance authority."""
import copy
import json
import unittest

from tests import test_final_audit as fixtures
ready_case = fixtures.ready_case
from engineering.local_app.final_audit import evaluate_case, evaluate_offline_stage7, report
from engineering.local_app.real_case import _domain_stage


class AcceptanceTrustBoundaryTests(unittest.TestCase):
    def test_source_only_readiness_cannot_issue_certificate(self):
        result = evaluate_case(ready_case(), fresh=True)
        self.assertEqual(result['decision'], 'BLOCK')
        self.assertFalse(result['engineering_verified'])
        self.assertIsNone(result['acceptance_certificate'])

    def test_review_metadata_in_caller_json_is_not_authority(self):
        result=evaluate_case(fixtures.verified_case(),fresh=True)
        self.assertFalse(result['acceptance_granted'])
        self.assertIn('CASE_NOT_STORE_REVALIDATED',result['blocker_codes'])

    def test_verified_content_change_invalidates_review(self):
        case=fixtures.verified_case()
        case['evidence'][0]['source_sha256']='c'*64
        result=evaluate_case(case,fresh=True,store_revalidated=True,verification_key=fixtures.TEST_VERIFICATION_KEY)
        self.assertFalse(result['acceptance_granted'])
        self.assertIn('EVIDENCE_ENGINEERING_VERIFICATION_REQUIRED',result['blocker_codes'])

    def test_unsigned_review_metadata_is_not_verified_provenance(self):
        case=fixtures.verified_case()
        del case['requirements']['engineering_verification']['signature']
        result=evaluate_case(case,fresh=True,store_revalidated=True,verification_key=fixtures.TEST_VERIFICATION_KEY)
        self.assertFalse(result['acceptance_granted'])

    def test_wrong_issuer_key_rejects_signed_records(self):
        result=evaluate_case(fixtures.verified_case(),fresh=True,store_revalidated=True,verification_key=b'x'*32)
        self.assertFalse(result['acceptance_granted'])

    def test_malformed_signature_fails_closed(self):
        case=fixtures.verified_case()
        case['requirements']['engineering_verification']['signature']='подделка'
        self.assertFalse(evaluate_case(case,fresh=True,store_revalidated=True,
            verification_key=fixtures.TEST_VERIFICATION_KEY)['acceptance_granted'])

    def test_signed_review_metadata_change_rejects_record(self):
        case=fixtures.verified_case()
        case['requirements']['engineering_verification']['reviewer']='different reviewer'
        self.assertFalse(evaluate_case(case,fresh=True,store_revalidated=True,
            verification_key=fixtures.TEST_VERIFICATION_KEY)['acceptance_granted'])

    def test_ready_stage_with_blocker_cannot_pass(self):
        case = ready_case()
        case['stages']['source_identity']['reasons'] = ['SOURCE_CHANGED']
        result = evaluate_case(case, fresh=True)
        self.assertEqual(result['checks'][1]['status'], 'BLOCK')
        self.assertIn('SOURCE_CHANGED', result['blocker_codes'])

    def test_domain_readiness_does_not_hide_unaccepted_decision(self):
        domains = {'packets': [dict(kind='NORMATIVE', revision=1,
            point6_readiness='READY_FOR_ENGINEERING_DECISION', status='BLOCK',
            reasons=['NORMATIVE_APPLICABILITY_NOT_ACCEPTED'],
            engineering_verified=False, acceptance_granted=False)]}
        result = _domain_stage({'requested_checks':['normative']}, domains)
        self.assertEqual(result['status'], 'BLOCK')
        self.assertIn('NORMATIVE_APPLICABILITY_NOT_ACCEPTED', result['reasons'])

    def test_all_pass_offline_json_never_issues_certificate(self):
        case = dict(schema='ENGINEER_OS_STAGE7_REAL_CASE_V1', case_sha256='a'*64,
            stage7_completion='COMPLETE', source_identity_status='PASS', missing_roles=[],
            workflow_complete=True, engineering_status='READY_FOR_FINAL_AUDIT', block_reasons=[],
            tz_traceability_status='PASS', evidence_review_status='PASS',
            specialist_coverage_status='PASS', domain_prerequisites_status='PASS', case_qc_status='PASS')
        result = evaluate_offline_stage7(case)
        self.assertEqual(result['decision'], 'BLOCK')
        self.assertFalse(result['acceptance_granted'])
        self.assertIsNone(result['acceptance_certificate'])


class PersistedAcceptanceIntegrityTests(unittest.TestCase):
    setUp=fixtures.FinalAuditStoreTests.setUp

    def test_verification_key_is_never_created_implicitly(self):
        self.assertIsNone(self.store.verification_key())
        path=self.store.root/'engineering-verification.key'
        self.assertFalse(path.exists())
        path.write_bytes(b'bad')
        self.assertIsNone(self.store.verification_key())
        path.write_bytes(fixtures.TEST_VERIFICATION_KEY)
        self.assertEqual(self.store.verification_key(),fixtures.TEST_VERIFICATION_KEY)
    def test_forged_persisted_audit_is_not_effective(self):
        from engineering.local_app.final_audit import build
        event = build(self.store,self.sid,case_id=self.case['id'],expected_revision=0)
        forged = copy.deepcopy(event)
        forged.update(decision='ACCEPTED', acceptance_granted=True, engineering_verified=True,
                      acceptance_certificate={'case_id':self.case['id']})
        with self.store.connection() as db:
            db.execute('UPDATE final_audits SET record=? WHERE id=?',
                       (json.dumps(forged), event['id']))
        self.assertFalse(report(self.store,self.sid)['acceptance_granted'])

    def test_case_metadata_change_invalidates_snapshot(self):
        from engineering.local_app.real_case import report as cases
        with self.store.connection() as db:
            altered = copy.deepcopy(self.case)
            altered['stages']['qc']['status'] = 'READY_FOR_REAL_CASE_REVIEW'
            db.execute('UPDATE real_case_snapshots SET record=? WHERE id=?',
                       (json.dumps(altered), self.case['id']))
        self.assertFalse(cases(self.store,self.sid)['current_fresh'])

    def test_job_scope_change_invalidates_snapshot(self):
        from engineering.local_app.real_case import report as cases
        with self.store.connection() as db:
            db.execute('UPDATE jobs SET prompt=? WHERE id=?',('Different engineering scope',self.job['id']))
        self.assertFalse(cases(self.store,self.sid)['current_fresh'])


if __name__ == '__main__':
    unittest.main()

import json
import unittest
from pathlib import Path

from engineering.local_app.final_audit import evaluate_offline_stage7

ROOT=Path(__file__).resolve().parents[1]

class Stage8OfflineFinalAuditTests(unittest.TestCase):
    def test_real_stage7_snapshot_audits_deterministically_and_blocks(self):
        case=json.loads((ROOT/'docs/qa/2026-10-07-stage7-naberezhnaya-real-case.json').read_text(encoding='utf-8'))
        first=evaluate_offline_stage7(case);second=evaluate_offline_stage7(case)
        self.assertEqual(first,second)
        self.assertEqual(first['decision'],'BLOCK')
        self.assertFalse(first['acceptance_granted']);self.assertEqual(first['final_audit'],'COMPLETED')
        self.assertEqual(first['case_sha256'],case['case_sha256'])
        self.assertIn('POINT6_SOLVER_DECISION_PENDING',first['blocker_codes'])
        self.assertIn('V4_DOCUMENT_COMPLETENESS_BLOCK',first['blocker_codes'])
        saved=json.loads((ROOT/'docs/qa/2026-10-07-stage8-naberezhnaya-final-audit.json').read_text(encoding='utf-8'))
        self.assertEqual(saved,first)

    def test_no_upstream_blocks_is_only_offline_acceptance_path(self):
        case=dict(schema='ENGINEER_OS_STAGE7_REAL_CASE_V1',case_sha256='a'*64,
                  stage7_completion='COMPLETE',source_identity_status='PASS',missing_roles=[],
                  workflow_complete=True,engineering_status='READY_FOR_FINAL_AUDIT',block_reasons=[],
                  tz_traceability_status='PASS',evidence_review_status='PASS',specialist_coverage_status='PASS',
                  domain_prerequisites_status='PASS',case_qc_status='PASS')
        result=evaluate_offline_stage7(case)
        self.assertEqual(result['decision'],'ACCEPTED');self.assertTrue(result['acceptance_granted'])
        self.assertIsNotNone(result['acceptance_certificate'])

if __name__=='__main__':
    unittest.main()

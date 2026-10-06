import unittest

from engineering.calculation.solver_receipt import SolverReceipt
from engineering.calculation.execution_identity import SolverExecutionIdentity,audit_execution_identity
from engineering.calculation.result_verification import SolverResultVerification,audit_solver_results
from engineering.calculation.structure_correlation import StructureCorrelationItem,audit_structure_correlation
from engineering.normative.source_verification import NormativeSourceVerification,audit_normative_source
from engineering.local_app.data_classification import DataClassReview,audit_data_classes


class Point6CompletionGateTests(unittest.TestCase):
    def receipt(self):
        return SolverReceipt(
            solver_name='TEST',solver_version='1',
            input_sha256='a'*64,output_sha256='b'*64,log_sha256='c'*64,
            exit_code=0,started_at='2026-10-06T20:00:00Z',finished_at='2026-10-06T20:01:00Z')

    def test_execution_identity_is_bound_to_receipt(self):
        r=self.receipt()
        identity=SolverExecutionIdentity('TEST','1','d'*64,'e'*64,'a'*64,'b'*64,'c'*64)
        result=audit_execution_identity(identity,r)
        self.assertEqual(result['status'],'READY_FOR_RESULT_INTEGRITY_REVIEW')
        bad=SolverExecutionIdentity('TEST','1','d'*64,'e'*64,'f'*64,'b'*64,'c'*64)
        self.assertEqual(audit_execution_identity(bad,r)['status'],'BLOCK')

    def test_result_hashes_and_reviews_gate_progress(self):
        r=self.receipt()
        review=SolverResultVerification(
            'a'*64,'b'*64,'c'*64,'file:result','file:log',
            'VERIFIED','VERIFIED','VERIFIED',())
        result=audit_solver_results(review,r)
        self.assertEqual(result['status'],'READY_FOR_STRUCTURE_CORRELATION')
        bad=SolverResultVerification(
            'a'*64,'f'*64,'c'*64,'file:result','file:log',
            'VERIFIED','VERIFIED','VERIFIED',())
        self.assertEqual(audit_solver_results(bad,r)['status'],'BLOCK')

    def test_structure_correlation_requires_all_roles(self):
        items=tuple(
            StructureCorrelationItem(role,('calc',),('actual',),'Matched','Controlled basis','VERIFIED')
            for role in ('GEOMETRY','MATERIALS_SECTIONS','LOADS_COMBINATIONS','SUPPORTS_RELEASES'))
        result=audit_structure_correlation(items)
        self.assertEqual(result['status'],'READY_FOR_ENGINEERING_REVIEW')
        self.assertFalse(result['acceptance_granted'])
        self.assertEqual(audit_structure_correlation(items[:-1])['status'],'BLOCK')

    def test_normative_source_identity_is_not_applicability_acceptance(self):
        review=NormativeSourceVerification(
            candidate_id='candidate',document='TEST',edition='2026',
            authority='Controlled authority',source_ref='authority:test',
            source_sha256='a'*64,verification_method='Controlled verification',
            decision='VERIFIED')
        result=audit_normative_source(review)
        self.assertEqual(result['status'],'READY_FOR_APPLICABILITY_REVIEW')
        self.assertFalse(result['acceptance_granted'])

    def test_data_classes_require_every_candidate(self):
        reviews=(DataClassReview('a','F','VERIFIED','Checked'),DataClassReview('b','M','VERIFIED','Checked'))
        result=audit_data_classes(reviews,('a','b'))
        self.assertEqual(result['status'],'READY_FOR_DOMAIN_REVIEW')
        self.assertEqual(audit_data_classes(reviews[:1],('a','b'))['status'],'BLOCK')


if __name__=='__main__':
    unittest.main()

import unittest
from engineering.normative.substantive_review import NormativeSubstantiveReview,evaluate_substantive_review

class SubstantiveReviewTests(unittest.TestCase):
    def decide(self,**changes):
        data=dict(reviewer='Unverified reviewer',reviewed_at='2026-10-08',assessment_date='2026-07-28',edition_basis='Registry and edition',applicability='APPLIES',applicability_basis='Declared concrete test',input_status='DOCUMENTED',outcome='WARNING',rationale='Recorded conclusion',limitations=['Field truth not verified'])
        data.update(changes)
        return evaluate_substantive_review(NormativeSubstantiveReview(**data),source_linked=True,edition_verified=True,authority_verified=True,basis_current=True)

    def test_positive_or_proven_error_never_becomes_expert_acceptance(self):
        for outcome in ['PASS','ERROR']:
            with self.subTest(outcome=outcome):
                r=self.decide(outcome=outcome)
                self.assertEqual(r['status'],'UNCERTAINTY');self.assertIn('REVIEWER_AUTHORITY_NOT_VERIFIED',r['reasons'])
                self.assertFalse(r['acceptance_granted']);self.assertFalse(r['engineering_verified'])

    def test_missing_or_conflicting_inputs_block_even_with_valid_sources(self):
        for value in ['MISSING','CONFLICT']:
            with self.subTest(value=value):
                r=self.decide(input_status=value)
                self.assertEqual(r['status'],'BLOCK');self.assertIn('NORMATIVE_INPUT_'+value,r['reasons'])

    def test_unknown_or_excluded_scope_has_explained_uncertainty(self):
        for value in ['UNKNOWN','OUT_OF_SCOPE']:
            with self.subTest(value=value):
                r=self.decide(applicability=value)
                self.assertEqual(r['status'],'UNCERTAINTY');self.assertIn('NORMATIVE_APPLICABILITY_'+value,r['reasons'])

    def test_documented_warning_keeps_content_without_acceptance(self):
        r=self.decide()
        self.assertEqual(r['status'],'WARNING');self.assertEqual(r['rationale'],'Recorded conclusion')
        self.assertFalse(r['acceptance_granted'])

"""Synthetic normative registry contracts; no real clause or edition asserted."""
import unittest
from dataclasses import replace
from engineering.normative.rule_registry import Rule, RuleRegistry, ActualQuantity, AssessmentReceipt, assess_rule, rule_digest
from engineering.normative.source_verification import NormativeSourceVerification
from engineering.normative.authority import NormativeAuthorityReview
from engineering.normative.substantive_review import NormativeSubstantiveReview

class RegistryTests(unittest.TestCase):
 def sample(self):
  rule=Rule('SYNTHETIC-R1','1','SYNTHETIC DOCUMENT','test-edition','synthetic length comparison','SYNTHETIC-CLAUSE','Synthetic length shall be <= 2 m','a'*64,'2026-01-01','2026-12-31','<=','2','m')
  actual=ActualQuantity('1500','mm',('synthetic:evidence',),'b'*64,'test:measurement','MEASURED')
  source=NormativeSourceVerification(rule.rule_id,rule.document,rule.edition,'synthetic authority','test:norm','a'*64,'synthetic test','VERIFIED')
  authority=NormativeAuthorityReview(rule.document,rule.edition,rule.clause,'synthetic authority','test:norm','synthetic scope review','VERIFIED')
  substantive=NormativeSubstantiveReview('synthetic reviewer','2026-10-15','2026-10-15','synthetic edition basis','APPLIES','synthetic scope basis','DOCUMENTED','UNCERTAINTY','arithmetic test only',['not a normative truth claim'])
  receipt=AssessmentReceipt(rule.rule_id,rule.rule_version,rule_digest(rule),'2026-10-15',actual,source,authority,substantive)
  return rule,receipt
 def run_case(self,rule=None,receipt=None):
  r,a=self.sample();return assess_rule(RuleRegistry((rule or r,)),receipt or a)
 def test_ready_only_arithmetic(self):
  r=self.run_case();self.assertEqual(r['status'],'UNCERTAINTY');self.assertTrue(r['comparison_ready']);self.assertTrue(r['comparison']['satisfied']);self.assertFalse(r['acceptance_granted']);self.assertFalse(r['engineering_verified'])
 def test_false_comparison_is_not_normative_error(self):
  r,a=self.sample();x=self.run_case(receipt=replace(a,actual=replace(a.actual,value='3',unit='m')));self.assertFalse(x['comparison']['satisfied']);self.assertEqual(x['status'],'UNCERTAINTY')
 def test_stale_interval(self):
  r,a=self.sample()
  for day in ('2025-12-31','2027-01-01'):
   self.assertEqual(self.run_case(receipt=replace(a,assessment_date=day))['status'],'BLOCK')
 def test_version_and_digest_mismatch(self):
  r,a=self.sample()
  for changes in ({'rule_version':'2'},{'rule_sha256':'c'*64},{'rule_id':'other'}):self.assertEqual(self.run_case(receipt=replace(a,**changes))['status'],'BLOCK')
  r=replace(r,requirement='changed exact requirement');self.assertEqual(self.run_case(rule=r,receipt=a)['status'],'BLOCK')
 def test_units_and_values(self):
  r,a=self.sample()
  for changes in ({'unit':'N'},{'unit':'guess'},{'value':'NaN'},{'value':True}):self.assertEqual(self.run_case(receipt=replace(a,actual=replace(a.actual,**changes)))['status'],'BLOCK')
 def test_source_identity_and_decisions(self):
  r,a=self.sample()
  for changes in ({'source_sha256':'c'*64},{'document':'different'},{'edition':'other'},{'decision':'NOT_VERIFIED'},{'decision':'REJECTED'}):self.assertEqual(self.run_case(receipt=replace(a,source_review=replace(a.source_review,**changes)))['status'],'BLOCK')
 def test_missing_receipts(self):
  r,a=self.sample()
  for key in ('actual','source_review','authority_review','substantive_review'):self.assertEqual(self.run_case(receipt=replace(a,**{key:None}))['status'],'BLOCK')
 def test_applicability_and_documented_inputs(self):
  r,a=self.sample()
  for state in ('UNKNOWN','OUT_OF_SCOPE'):
   x=self.run_case(receipt=replace(a,substantive_review=replace(a.substantive_review,applicability=state)));self.assertEqual(x['status'],'UNCERTAINTY');self.assertFalse(x['comparison_ready'])
  for state in ('MISSING','CONFLICT'):
   self.assertEqual(self.run_case(receipt=replace(a,substantive_review=replace(a.substantive_review,input_status=state)))['status'],'BLOCK')
 def test_evidence_provenance(self):
  r,a=self.sample()
  for changes in ({'evidence_ids':()},{'evidence_ids':('x','x')},{'source_sha256':''},{'locator':''},{'data_class':'UNKNOWN'}):self.assertEqual(self.run_case(receipt=replace(a,actual=replace(a.actual,**changes)))['status'],'BLOCK')
 def test_authority_binding(self):
  r,a=self.sample()
  for changes in ({'clause':'other'},{'source_ref':'different'},{'authority':'different'},{'decision':'NOT_VERIFIED'}):self.assertEqual(self.run_case(receipt=replace(a,authority_review=replace(a.authority_review,**changes)))['status'],'BLOCK')
 def test_duplicate_registry_and_invalid_interval(self):
  r,a=self.sample()
  self.assertEqual(assess_rule(RuleRegistry((r,r)),a)['status'],'BLOCK')
  self.assertEqual(self.run_case(rule=replace(r,effective_until='2025-01-01'))['status'],'BLOCK')
 def test_review_date_binding(self):
  r,a=self.sample();self.assertEqual(self.run_case(receipt=replace(a,assessment_date='2026-10-14'))['status'],'BLOCK')
 def test_unverified_inputs_and_reviewer_warning(self):
  r,a=self.sample()
  for changes in ({'input_status':'UNVERIFIED'},{'outcome':'WARNING'}):
   x=self.run_case(receipt=replace(a,substantive_review=replace(a.substantive_review,**changes)));self.assertFalse(x['comparison_ready']);self.assertEqual(x['status'],'UNCERTAINTY')
 def test_absent_currentness_or_scope_blocks(self):
  r,a=self.sample()
  for changes in ({'effective_until':''},{'effective_from':'20260101'},{'scope':''},{'normative_source_sha256':'bad'},{'limit_unit':'invented'},{'operator':'!='}):self.assertEqual(self.run_case(rule=replace(r,**changes))['status'],'BLOCK')
 def test_receipt_and_rule_digests(self):
  r,a=self.sample();x=self.run_case();self.assertEqual(len(x['receipt_sha256']),64)
  y=self.run_case(receipt=replace(a,actual=replace(a.actual,source_sha256='c'*64)))
  self.assertNotEqual(x['receipt_sha256'],y['receipt_sha256']);self.assertEqual(x['actual']['data_class'],'MEASURED')
  self.assertNotEqual(rule_digest(r),rule_digest(replace(r,rule_version='2')))
 def test_review_pass_never_grants_acceptance(self):
  r,a=self.sample();x=self.run_case(receipt=replace(a,substantive_review=replace(a.substantive_review,outcome='PASS')))
  self.assertEqual(x['status'],'UNCERTAINTY');self.assertFalse(x['normative_truth_verified']);self.assertFalse(x['current_edition_verified']);self.assertFalse(x['engineering_verified']);self.assertFalse(x['acceptance_granted'])

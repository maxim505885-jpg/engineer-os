"""Synthetic local catalog tests; no real norm or legal currency is asserted."""
import hashlib
import json
import tempfile
import unittest
from dataclasses import asdict, replace
from pathlib import Path
from engineering.normative.catalog import load_rule_catalog
from engineering.normative.rule_registry import assess_rule, rule_digest
from tests import test_normative_rule_registry as registry_tests

class CatalogTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
  self.rule,self.receipt=registry_tests.RegistryTests().sample()
  text='SYNTHETIC DOCUMENT\ntest-edition\nSYNTHETIC-CLAUSE\nSynthetic length shall be <= 2 m\n'
  raw=text.encode();(self.root/'source.txt').write_bytes(raw)
  self.entry=dict(asdict(self.rule),normative_source_sha256=hashlib.sha256(raw).hexdigest(),source_path='source.txt',source_locator='SYNTHETIC-CLAUSE',clause_text='SYNTHETIC-CLAUSE\nSynthetic length shall be <= 2 m',accepted_data_classes=['MEASURED','TESTED'])
  self.catalog=dict(format_version=1,registry_version='synthetic-v1',rules=[self.entry]);self.path=self.root/'catalog.json'
 def load(self):
  self.path.write_text(json.dumps(self.catalog),encoding='utf-8');return load_rule_catalog(self.path)
 def test_exact_source_bound_immutable_catalog(self):
  registry=self.load();r=registry.rules[0]
  self.assertEqual(r.clause_text,self.entry['clause_text']);self.assertEqual(r.accepted_data_classes,('MEASURED','TESTED'))
  self.assertEqual(r.normative_source_sha256,hashlib.sha256((self.root/'source.txt').read_bytes()).hexdigest())
  with self.assertRaises(AttributeError):r.scope='changed'
 def test_metadata_without_clause_text_is_not_rule(self):
  for key in ('clause_text','source_path','source_locator','accepted_data_classes'):
   with self.subTest(key=key):
    old=self.entry.pop(key)
    with self.assertRaises(ValueError):self.load()
    self.entry[key]=old
 def test_source_change_and_wrong_quote_fail_closed(self):
  for changes in ({'normative_source_sha256':'0'*64},{'clause_text':'invented clause'},{'requirement':'invented requirement'},{'edition':'absent edition'},{'document':'absent title'},{'source_locator':'absent clause'},{'limit':'9'}):
   with self.subTest(changes=changes):
    original=self.entry.copy();self.entry.update(changes)
    with self.assertRaises(ValueError):self.load()
    self.entry.clear();self.entry.update(original)
 def test_path_escape_and_unsupported_source_are_rejected(self):
  for value in ('../outside.txt','/outside.txt','C:\\outside.txt','source.pdf','source.txt/../source.txt'):
   with self.subTest(path=value):
    self.entry['source_path']=value
    with self.assertRaises(ValueError):self.load()
 def test_duplicate_keys_versions_and_nonfinite_values_are_rejected(self):
  self.path.write_text('{"format_version":1,"format_version":1}',encoding='utf-8')
  with self.assertRaises(ValueError):load_rule_catalog(self.path)
  self.catalog['rules']=[self.entry,self.entry.copy()]
  with self.assertRaises(ValueError):self.load()
  self.catalog['rules']=[self.entry];self.entry['limit']=float('nan')
  with self.assertRaises(ValueError):self.load()
 def test_project_dimension_cannot_substitute_measured_value(self):
  r=self.load().rules[0];a=replace(self.receipt,rule_sha256=rule_digest(r),source_review=replace(self.receipt.source_review,source_sha256=r.normative_source_sha256))
  ok=assess_rule(self.load(),a);self.assertTrue(ok['comparison_ready']);self.assertFalse(ok['acceptance_granted'])
  bad=assess_rule(self.load(),replace(a,actual=replace(a.actual,data_class='PROJECT')))
  self.assertEqual(bad['status'],'BLOCK');self.assertIn('ACTUAL_INPUT_DATA_CLASS_NOT_ALLOWED_BY_RULE',bad['reasons'])
 def test_rule_change_invalidates_previous_digest(self):
  r=self.load().rules[0];first=rule_digest(r);self.entry['accepted_data_classes']=['MEASURED']
  self.assertNotEqual(first,rule_digest(self.load().rules[0]))
 def test_invalid_units_dates_or_classes_are_rejected(self):
  for changes in ({'limit_unit':'imaginary'},{'effective_until':'2025-01-01'},{'accepted_data_classes':['ASSUMED']},{'accepted_data_classes':['MEASURED','MEASURED']},{'scope':''}):
   with self.subTest(changes=changes):
    original=self.entry.copy();self.entry.update(changes)
    with self.assertRaises(ValueError):self.load()
    self.entry.clear();self.entry.update(original)


class CatalogPacketTests(unittest.TestCase):
 from tests.test_domain_packets import DomainPacketTests as _Base
 setUp=_Base.setUp
 candidate=_Base.candidate
 module=_Base.module
 packet=_Base.packet
 save=_Base.save
 report=_Base.report
 def configured(self):
  from engineering.local_app.evidence import register
  from engineering.local_app.review import record_review
  from engineering.normative.rule_registry import Rule
  item=register(self.store,self.sid,file_id=self.actual['id'],quote='Height 2500 mm',statement='Declared measurement',data_class='M')
  record_review(self.store,self.sid,item['id'],expected_revision=0,decision='SOURCE_CONFIRMED',note='Source only',actor='Test')
  packet=self.packet();packet['actual_ids']=[item['id']];packet['quantities']['actual']['candidate_id']=item['id']
  rule=Rule('synthetic','1','TEST','2026','Scope declaration','clause1','Limit 2.5 m',self.norm['sha256'],'2026-01-01','2026-12-31','<=','2.5','m','clause1 Limit 2.5 m','clause1',('MEASURED',))
  packet['catalog_rule']=dict(registry_version='synthetic',rule=asdict(rule),rule_sha256=rule_digest(rule),assessment_date='2026-10-15')
  return packet
 def test_catalog_packet_preserves_rule_digest_without_acceptance(self):
  p=self.configured();self.save(p);row=self.report()['packets'][0]
  self.assertEqual(row['catalog_rule']['rule_sha256'],p['catalog_rule']['rule_sha256']);self.assertFalse(row['acceptance_granted'])
 def test_wrong_scope_date_digest_units_or_class_blocks_packet(self):
  import copy
  from engineering.local_app.evidence import register
  p=self.configured()
  for mutation in ('scope','date','digest','units','class'):
   x=copy.deepcopy(p)
   if mutation=='scope':x['chain']['scope']='Other scope'
   elif mutation=='date':x['catalog_rule']['assessment_date']='2027-01-01'
   elif mutation=='digest':x['catalog_rule']['rule_sha256']='0'*64
   elif mutation=='units':x['quantities']['limit']['unit']='mm'
   else:
    item=register(self.store,self.sid,file_id=self.actual['id'],quote='Height 2500 mm',statement='Project declaration',data_class='P')
    x['actual_ids']=[item['id']];x['quantities']['actual']['candidate_id']=item['id']
   with self.subTest(mutation=mutation),self.assertRaises(ValueError):self.save(x)

 def test_changed_catalog_source_is_not_current_after_save(self):
  p=self.configured();self.save(p)
  Path(self.store.get_file(self.norm['id'])['path']).write_bytes(b'changed source')
  row=self.report()['packets'][0]
  self.assertIn('CATALOG_RULE_BINDING_INVALID',row['reasons']);self.assertIsNone(row['catalog_rule'])

import json,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from engineering.local_app.store import Store
from engineering.local_app.files import preserve_file
from engineering.local_app.worker import Worker
from engineering.local_app.requirements import create_set,assess
from engineering.local_app.evidence import register
from engineering.local_app.review import record_review
from engineering.local_app.core_run import parse_draft

class EngineeringCoreTraceabilityTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.store=Store(Path(self.temp.name));self.session=self.store.create_session()['id']
  self.file=preserve_file(self.store,self.session,'report.txt','Высота 4 м'.encode());tor=preserve_file(self.store,self.session,'tor.txt','Проверить высоту'.encode());source=register(self.store,self.session,file_id=tor['id'],quote='Проверить высоту',statement='Исходное ТЗ');record_review(self.store,self.session,source['id'],expected_revision=0,decision='SOURCE_CONFIRMED',note='Native ToR source',actor='Source reader');self.tor_id=tor['id'];self.tz=create_set(self.store,self.session,text='Проверить высоту',source_evidence_ids=[source['id']]);self.rid=self.tz['requirements'][0]['id']
  self.candidate=register(self.store,self.session,file_id=self.file['id'],quote='Высота 4 м',statement='Высота по источнику',data_class='P')
  record_review(self.store,self.session,self.candidate['id'],expected_revision=0,decision='SOURCE_CONFIRMED',note='Точная цитата сверена',actor='Test reviewer')
 def reply(self,relation='SUPPORTS',mapped=True):
  item=dict(text='В источнике указана высота 4 м; фактическая высота не подтверждена',source_ids=[self.candidate['id']])
  if mapped:item.update(requirement_ids=[self.rid],relation=relation)
  return json.dumps(dict(status='UNCERTAINTY',summary='Непроверенный инженерный черновик',observations=[item],limitations=['P не подтверждает F']),ensure_ascii=False)
 def execute(self,replies):
  job=self.store.enqueue(self.session,'Проверить высоту',[self.file['id'],self.tor_id],mode='CORE_RUN',requested_checks=['report']);values=iter(replies)
  class Model:
   def chat(inner,messages):return next(values)
  Worker(self.store,Model()).run_once();return self.store.snapshot(self.session)['jobs'][0]
 def assessed(self):
  assess(self.store,self.session,set_id=self.tz['id'],requirement_id=self.rid,expected_revision=0,conclusion='Исходник содержит проектную высоту; F не проверена',evidence_ids=[self.candidate['id']],relation='SUPPORTS',actor='Test assessor')
 def test_explicit_requirement_relation_contract(self):
  parsed,_=parse_draft(SimpleNamespace(task_id='task',agent='report-audit-agent'),self.reply(),{self.candidate['id']},allowed_requirement_ids={self.rid})
  self.assertEqual(parsed.findings[0]['requirement_ids'],[self.rid])
 def test_foreign_requirement_reference_refused(self):
  with self.assertRaises(ValueError):parse_draft(SimpleNamespace(task_id='task',agent='report-audit-agent'),self.reply(),{self.candidate['id']},allowed_requirement_ids={'foreign'})
 def test_completed_old_roles_do_not_hide_unassessed_tz(self):
  job=self.execute([self.reply(mapped=False)]*2)
  self.assertEqual(job['state'],'SUCCEEDED');self.assertEqual(job['result']['engineering_status'],'BLOCK');self.assertTrue(job['result']['core_run']['analysis_complete']);self.assertEqual(job['result']['core_run']['status'],'BLOCK')
  review=job['result']['core_run']['engineering_review'];self.assertIn('NOT_ASSESSED',review['requirements'][0]['reasons']);self.assertIn('REQUIREMENT_NOT_ADDRESSED',review['requirements'][0]['reasons'])
 def test_linked_requirement_is_reproducible_without_acceptance(self):
  self.assessed();job=self.execute([self.reply()]*2);review=job['result']['core_run']['engineering_review']
  self.assertEqual(review['status'],'UNCERTAINTY');self.assertEqual(review['requirements'][0]['traceability'],'SOURCE_LINKED');self.assertEqual(review['requirements'][0]['observations'][0]['sources'][0]['source_sha256'],self.file['sha256'])
  self.assertFalse(review['acceptance_granted']);self.assertFalse(review['engineering_verified']);self.assertTrue(review['snapshot_sha256'])
  self.assertEqual(Store(self.store.root).snapshot(self.session)['jobs'][0]['result']['core_run']['engineering_review'],review)
 def test_declared_cross_role_contradiction_blocks(self):
  self.assessed();job=self.execute([self.reply(),self.reply('CONTRADICTS')]);review=job['result']['core_run']['engineering_review']
  self.assertEqual(review['status'],'BLOCK');self.assertIn('ROLE_RELATION_CONFLICT',review['requirements'][0]['reasons']);self.assertEqual(job['result']['core_run']['status'],'BLOCK')
 def test_original_only_reference_does_not_establish_finding(self):
  self.assessed();raw=json.loads(self.reply());raw['observations'][0]['source_ids']=[self.file['id']];job=self.execute([json.dumps(raw)]*2)
  self.assertEqual(job['result']['core_run']['engineering_review']['status'],'BLOCK')

 def test_later_tz_version_does_not_rewrite_saved_review(self):
  self.assessed();job=self.execute([self.reply()]*2);saved=job['result']['core_run']['engineering_review']
  create_set(self.store,self.session,text='Проверить фундамент')
  self.assertEqual(self.store.snapshot(self.session)['jobs'][0]['result']['core_run']['engineering_review'],saved)
 def test_case_qc_consumes_saved_requirement_gate(self):
  from engineering.local_app.real_case import build
  job=self.execute([self.reply(mapped=False)]*2)
  case=build(self.store,self.session,job_id=job['id'],expected_revision=0,manifest={'TOR':[self.file['id']],'REPORT':[self.file['id']]})
  self.assertEqual(case['stages']['specialists']['status'],'BLOCK')
  self.assertIn('ENGINEERING_REVIEW_BLOCKED',case['stages']['specialists']['reasons'])
 def test_invalid_relation_and_duplicate_requirement_ids_rejected(self):
  for field,value in [('relation',[]),('relation','ACCEPTED'),('requirement_ids',[self.rid,self.rid])]:
   body=json.loads(self.reply());body['observations'][0][field]=value
   with self.assertRaises(ValueError):parse_draft(SimpleNamespace(task_id='task',agent='report-audit-agent'),json.dumps(body),{self.candidate['id']},allowed_requirement_ids={self.rid})

 def test_automatic_summary_cannot_erase_part_gates(self):
  import fitz
  for variant in ('CONTRADICTS','UNKNOWN','UNMAPPED','ORIGINAL_ONLY'):
   with self.subTest(variant=variant):
    self.setUp();self.assessed()
    with fitz.open() as doc:
     for _ in range(4):
      page=doc.new_page();page.insert_textbox((30,30,570,800),'native source '*450,fontsize=8)
     pdf=preserve_file(self.store,self.session,'large.pdf',doc.tobytes())
    job=self.store.enqueue(self.session,'Проверить высоту',[self.file['id'],self.tor_id,pdf['id']],mode='CORE_RUN',requested_checks=['report'])
    outer=self
    class Model:
     def chat(inner,messages):
      payload=json.loads(messages[-1]['content'].split('\n',1)[1])
      if 'drafts' in payload:return outer.reply()
      raw=json.loads(outer.reply(variant if variant in {'CONTRADICTS','UNKNOWN'} else 'SUPPORTS',mapped=variant!='UNMAPPED'))
      if variant=='ORIGINAL_ONLY':raw['observations'][0]['source_ids']=[pdf['id']]
      return json.dumps(raw)
    Worker(self.store,Model()).run_once();saved=self.store.snapshot(self.session)['jobs'][0]
    self.assertEqual(saved['state'],'SUCCEEDED')
    review=saved['result']['core_run']['engineering_review']
    self.assertEqual(review['status'],'BLOCK')
    gates=saved['result']['core_run']['results'][0]['intermediate_gates']
    self.assertTrue(gates);self.assertTrue(gates[0]['receipt_id']);self.assertTrue(gates[0]['response_sha256'])

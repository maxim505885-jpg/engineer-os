import tempfile,unittest,json,threading
from pathlib import Path
from engineering.local_app.store import Store
from engineering.local_app.files import preserve_file
from engineering.local_app.evidence import register
from engineering.local_app.review import record_review
from engineering.local_app.requirements import create_set,assess,report
from engineering.local_app.worker import Worker

class TorSourceResponsibilityTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.store=Store(Path(self.tmp.name));self.sid=self.store.create_session()['id']
  self.tor=preserve_file(self.store,self.sid,'TOR.txt','Проверить высоту'.encode());self.source=register(self.store,self.sid,file_id=self.tor['id'],quote='Проверить высоту',statement='Текст ТЗ')
  record_review(self.store,self.sid,self.source['id'],expected_revision=0,decision='SOURCE_CONFIRMED',note='Точная цитата',actor='Source reviewer')
 def setup_set(self):return create_set(self.store,self.sid,text='Проверить высоту',source_evidence_ids=[self.source['id']])
 def test_tor_source_binding_and_assessment_actor_persist(self):
  tz=self.setup_set();assess(self.store,self.sid,set_id=tz['id'],requirement_id=tz['requirements'][0]['id'],expected_revision=0,conclusion='Недостаточно данных',evidence_ids=[self.source['id']],relation='UNKNOWN',actor='Reviewer A')
  r=report(self.store,self.sid);self.assertEqual(r['tor_source_status'],'SOURCE_REVIEWED');self.assertEqual(r['requirements'][0]['assessment_actor'],'Reviewer A');self.assertFalse(r['requirements'][0]['assessment_actor_verified'])
  self.assertEqual(Store(self.store.root).requirements_state(self.sid),self.store.requirements_state(self.sid))
 def test_later_tor_source_review_invalidates_bound_basis(self):
  self.setup_set();record_review(self.store,self.sid,self.source['id'],expected_revision=1,decision='SOURCE_CONFIRMED',note='Новое решение',actor='B')
  r=report(self.store,self.sid);self.assertEqual(r['tor_source_status'],'BLOCK');self.assertIn('SOURCE_REVIEW_CHANGED',r['tor_sources'][0]['reasons'])
 def test_missing_original_tor_and_author_block_core(self):
  tz=create_set(self.store,self.sid,text='Проверить высоту');rid=tz['requirements'][0]['id']
  assess(self.store,self.sid,set_id=tz['id'],requirement_id=rid,expected_revision=0,conclusion='Источник содержит задание, не фактическую высоту',evidence_ids=[self.source['id']],relation='SUPPORTS')
  class Model:
   def chat(inner,m):return json.dumps(dict(status='UNCERTAINTY',summary='Draft',observations=[dict(text='Неподтверждённый вывод',source_ids=[self.source['id']],requirement_ids=[rid],relation='SUPPORTS')],limitations=[]))
  self.store.enqueue(self.sid,'Проверить высоту',[self.tor['id']],mode='CORE_RUN',requested_checks=['report']);Worker(self.store,Model()).run_once()
  r=self.store.snapshot(self.sid)['jobs'][0]['result']['core_run']['engineering_review'];self.assertEqual(r['status'],'BLOCK');self.assertIn('TZ_SOURCE_NOT_BOUND',r['reasons']);self.assertIn('ASSESSMENT_REVIEWER_MISSING',r['requirements'][0]['reasons'])
 def test_foreign_tor_candidate_rejected(self):
  other=self.store.create_session()['id']
  with self.assertRaises(ValueError):create_set(self.store,other,text='ТЗ',source_evidence_ids=[self.source['id']])
 def test_invalid_actor_rejected(self):
  tz=self.setup_set()
  for actor in ('',' '*2,'x'*121,[],True):
   with self.assertRaises(ValueError):assess(self.store,self.sid,set_id=tz['id'],requirement_id=tz['requirements'][0]['id'],expected_revision=0,conclusion='x',evidence_ids=[],relation='UNKNOWN',actor=actor)
 def test_native_right_padding_is_not_location_ambiguity(self):
  import fitz
  with fitz.open() as d:
   d.new_page().insert_text((40,40),'Height 4m ')
   f=preserve_file(self.store,self.sid,'padding.pdf',d.tobytes())
  from unittest.mock import patch
  # Reproduce the exact native bbox output observed in V4 page13.
  with patch.object(fitz.Page,'get_textbox',return_value='Height 4m '):
   candidate=register(self.store,self.sid,file_id=f['id'],page=1,quote='Height 4m',statement='Claim')
   self.assertEqual(candidate['provenance']['status'],'UNIQUE')
   record_review(self.store,self.sid,candidate['id'],expected_revision=0,decision='SOURCE_CONFIRMED',note='Native source only',actor='Reader')
  self.assertFalse(candidate['acceptance_granted'])

 def test_tor_basis_rejects_duplicates_and_invalid_shapes(self):
  for ids in ([self.source['id']]*2,'candidate',[True],[],['missing']):
   if ids==[]:continue
   with self.assertRaises(ValueError):create_set(self.store,self.sid,text='ТЗ',source_evidence_ids=ids)
 def test_native_padding_fix_does_not_accept_extra_text_or_lines(self):
  import fitz
  from unittest.mock import patch
  with fitz.open() as d:
   d.new_page().insert_text((40,40),'Height 4m ');f=preserve_file(self.store,self.sid,'strict.pdf',d.tobytes())
  for text in ('Height 5m ','Height 4mX','Height 4m\nOther','Height  4m'):
   with patch.object(fitz.Page,'get_textbox',return_value=text):
    c=register(self.store,self.sid,file_id=f['id'],page=1,quote='Height 4m',statement='Claim')
    self.assertEqual(c['provenance']['status'],'AMBIGUOUS')
    with self.assertRaises(ValueError):record_review(self.store,self.sid,c['id'],expected_revision=0,decision='SOURCE_CONFIRMED',note='Cannot confirm',actor='Reader')

import tempfile,unittest
from pathlib import Path
from engineering.local_app.store import Store
from engineering.local_app.files import preserve_file
from engineering.local_app.evidence import register
from engineering.local_app.review import record_review
from engineering.local_app.requirements import create_set,assess,report,context

class TorMatrixGlobalGatesTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
  self.store=Store(Path(self.tmp.name));self.sid=self.store.create_session()['id']
  self.file=preserve_file(self.store,self.sid,'original.txt',b'TOR and source quote')
  self.source=register(self.store,self.sid,file_id=self.file['id'],quote='source quote',statement='Author claim')
  record_review(self.store,self.sid,self.source['id'],expected_revision=0,decision='SOURCE_CONFIRMED',note='Exact original quote',actor='Source reader')
 def matrix(self,bound=True,actor='Assessment reader'):
  tz=create_set(self.store,self.sid,text='Check source',source_evidence_ids=[self.source['id']] if bound else [])
  assess(self.store,self.sid,set_id=tz['id'],requirement_id=tz['requirements'][0]['id'],expected_revision=0,conclusion='Quote is linked; engineering truth not checked',evidence_ids=[self.source['id']],relation='SUPPORTS',actor=actor)
 def test_missing_tor_basis_blocks_overall_even_with_linked_row(self):
  self.matrix(False);r=report(self.store,self.sid)
  self.assertEqual(r['requirements'][0]['traceability'],'SOURCE_LINKED')
  self.assertEqual(r['status'],'BLOCK');self.assertIn('TZ_SOURCE_NOT_BOUND',r['reasons'])
 def test_missing_actor_blocks_overall_even_with_reviewed_tor(self):
  self.matrix(actor=None);r=report(self.store,self.sid)
  self.assertEqual(r['tor_source_status'],'SOURCE_REVIEWED')
  self.assertEqual(r['status'],'BLOCK');self.assertIn('ASSESSMENT_REVIEWER_MISSING',r['reasons'])
 def test_reviewed_basis_and_declared_actor_remain_uncertainty(self):
  self.matrix();r=report(self.store,self.sid)
  self.assertEqual(r['status'],'UNCERTAINTY');self.assertEqual(r['reasons'],[])
  self.assertFalse(r['engineering_verified']);self.assertFalse(r['tor_transcription_verified']);self.assertFalse(r['acceptance_granted'])
 def test_stale_tor_blocks_even_after_assessment_rebound_to_new_review(self):
  self.matrix();record_review(self.store,self.sid,self.source['id'],expected_revision=1,decision='SOURCE_CONFIRMED',note='Another source review',actor='Other')
  state=self.store.requirements_state(self.sid);tz=state['sets'][-1]
  assess(self.store,self.sid,set_id=tz['id'],requirement_id=tz['requirements'][0]['id'],expected_revision=1,conclusion='Assessment updated only',evidence_ids=[self.source['id']],relation='SUPPORTS',actor='Reader')
  r=report(self.store,self.sid);self.assertEqual(r['requirements'][0]['traceability'],'SOURCE_LINKED')
  self.assertEqual(r['status'],'BLOCK');self.assertIn('SOURCE_REVIEW_CHANGED',r['reasons'])
 def test_model_context_carries_global_gate(self):
  self.matrix(False);r=context(self.store,self.sid,[self.file['id']])
  self.assertEqual(r['status'],'BLOCK');self.assertIn('TZ_SOURCE_NOT_BOUND',r['reasons'])

import json,tempfile,unittest
from pathlib import Path
from engineering.local_app.store import Store
from engineering.local_app.files import preserve_file
from engineering.local_app.evidence import register
from engineering.local_app.review import record_review
from engineering.local_app.requirements import create_set,assess,context
from engineering.local_app.worker import Worker

class TorContextIndexTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.store=Store(Path(self.tmp.name));self.sid=self.store.create_session()['id']
  self.f=preserve_file(self.store,self.sid,'tor.txt',b'Original TOR and source')
  self.c=register(self.store,self.sid,file_id=self.f['id'],quote='Original TOR',statement='Source only')
  record_review(self.store,self.sid,self.c['id'],expected_revision=0,decision='SOURCE_CONFIRMED',note='Quote',actor='Reader')
  self.tz=create_set(self.store,self.sid,text='\n'.join(f'{i}: '+('long source requirement '*40) for i in range(50)),source_evidence_ids=[self.c['id']])
  for row in self.tz['requirements']:assess(self.store,self.sid,set_id=self.tz['id'],requirement_id=row['id'],expected_revision=0,conclusion='Source claim only',evidence_ids=[self.c['id']],relation='SUPPORTS',actor='Assessor')
 def test_all_ids_survive_detail_budget_without_claiming_full_text(self):
  r=context(self.store,self.sid,[self.f['id']]);index=r.get('requirement_index',[])
  self.assertEqual([x['id'] for x in index],[x['id'] for x in self.tz['requirements']])
  self.assertTrue(all(x['text_truncated'] for x in index));self.assertTrue(r['context_truncated'])
  self.assertLessEqual(len(json.dumps(index,ensure_ascii=False))+sum(len(json.dumps(x,ensure_ascii=False)) for x in r['requirements']),14000)
  self.assertTrue(all(len(x['text'])<=120 for x in index));self.assertFalse(r['acceptance_granted'])
 def test_escaped_excerpt_index_respects_serialized_budget(self):
  for char in ('"','\\','\x00','\t'):
   tz=create_set(self.store,self.sid,text='\n'.join(f'{i}: '+char*120+' end' for i in range(50)))
   r=context(self.store,self.sid,[self.f['id']]);index=r['requirement_index']
   self.assertEqual([x['id'] for x in index],[x['id'] for x in tz['requirements']])
   self.assertLessEqual(len(json.dumps(index,ensure_ascii=False))+sum(len(json.dumps(x,ensure_ascii=False)) for x in r['requirements']),14000)
   self.assertTrue(r['context_truncated']);self.assertTrue(all(x['text_truncated'] for x in index))
 def test_core_accepts_indexed_last_requirement_but_unaddressed_rows_block(self):
  self.run_core(False)
 def test_automatic_analysis_accepts_indexed_last_requirement(self):
  self.run_core(True)
 def run_core(self,automatic):
  import fitz
  files=[self.f['id']]
  if automatic:
   with fitz.open() as d:
    for _ in range(4):d.new_page().insert_textbox((30,30,570,800),'native source '*450,fontsize=8)
    files.append(preserve_file(self.store,self.sid,'large.pdf',d.tobytes())['id'])
  rid=self.tz['requirements'][-1]['id'];cid=self.c['id'];seen=[]
  class Model:
   def chat(inner,messages):
    data=json.loads(messages[-1]['content'].split('\n',1)[1])
    if 'sources' in data:
     req=data['sources']['requirements'];seen.append(rid in {x['id'] for x in req.get('requirement_index',[])})
    return json.dumps(dict(status='UNCERTAINTY',summary='Partial index replay',observations=[dict(text='Source claim only',source_ids=[cid],requirement_ids=[rid],relation='SUPPORTS')],limitations=['No engineering acceptance']))
  self.store.enqueue(self.sid,'Check last indexed requirement',files,mode='CORE_RUN',requested_checks=['report']);Worker(self.store,Model()).run_once()
  job=self.store.snapshot(self.sid)['jobs'][0];self.assertEqual(job['state'],'SUCCEEDED')
  review=job['result']['core_run']['engineering_review'];last=review['requirements'][-1]
  self.assertTrue(all(seen));self.assertTrue(last['observations']);self.assertNotIn('REQUIREMENT_NOT_ADDRESSED',last['reasons'])
  self.assertIn('REQUIREMENT_NOT_ADDRESSED',review['requirements'][0]['reasons']);self.assertEqual(review['status'],'BLOCK');self.assertFalse(review['acceptance_granted'])

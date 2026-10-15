"""Source-bound per-object reference comparison never grants document acceptance."""
import copy
import unittest
from engineering.document_intelligence.qualification import qualify_document

class DocumentQualificationTests(unittest.TestCase):
 def sample(self):
  identity=dict(source_sha256='a'*64,reference_sha256='b'*64,parser_sha256='c'*64)
  obj=dict(object_id='table-1-r2-c3',kind='table_cell',source_locator='word/document.xml#table[1]/row[2]/cell[3]',reference_locator='page=12;cell=2,3',payload_sha256='d'*64,critical_numeric=True)
  manifest=dict(schema=1,**identity,objects=[obj]);observation=dict(**identity,**obj)
  return manifest,[observation]
 def test_matching_reference_payload_is_ready_for_review_only(self):
  m,o=self.sample();r=qualify_document(m,o)
  self.assertEqual(r['comparison_status'],'PASS');self.assertEqual(r['status'],'READY_FOR_INDEPENDENT_REVIEW')
  self.assertEqual(r['unaccounted_objects'],[]);self.assertEqual(r['critical_numeric_mismatches'],[])
  self.assertFalse(r['acceptance_granted']);self.assertFalse(r['engineering_verified']);self.assertEqual(r['document_completeness'],'NOT_QUALIFIED')
 def test_missing_cell_blocks_instead_of_using_aggregate_count(self):
  m,o=self.sample();r=qualify_document(m,[])
  self.assertEqual(r['status'],'BLOCK');self.assertEqual(r['unaccounted_objects'],['table-1-r2-c3'])
 def test_numeric_payload_mismatch_cannot_be_normalized_away(self):
  m,o=self.sample();o[0]['payload_sha256']='e'*64;r=qualify_document(m,o)
  self.assertEqual(r['critical_numeric_mismatches'],['table-1-r2-c3']);self.assertEqual(r['status'],'BLOCK')
 def test_formula_or_image_mismatch_also_blocks(self):
  for kind in ('formula','image','embedded_object','paragraph'):
   m,o=self.sample();m['objects'][0].update(kind=kind,critical_numeric=False);o[0].update(kind=kind,critical_numeric=False,payload_sha256='e'*64)
   r=qualify_document(m,o);self.assertEqual(r['status'],'BLOCK');self.assertEqual(r['critical_numeric_mismatches'],[])
 def test_changed_source_reference_or_parser_cannot_reuse_result(self):
  for key in ('source_sha256','reference_sha256','parser_sha256'):
   m,o=self.sample();o[0][key]='e'*64;r=qualify_document(m,o)
   self.assertEqual(r['status'],'BLOCK');self.assertIn('IDENTITY_MISMATCH',r['objects'][0]['reasons'])
 def test_changed_locator_or_kind_or_critical_flag_blocks(self):
  for key,value in (('source_locator','different-cell'),('reference_locator','page=99'),('kind','formula'),('critical_numeric',False)):
   m,o=self.sample();o[0][key]=value;self.assertEqual(qualify_document(m,o)['status'],'BLOCK')
 def test_duplicate_or_foreign_observations_are_rejected(self):
  m,o=self.sample()
  with self.assertRaises(ValueError):qualify_document(m,o+copy.deepcopy(o))
  o[0]['object_id']='other'
  with self.assertRaises(ValueError):qualify_document(m,o)
 def test_duplicate_manifest_or_empty_scope_is_rejected(self):
  m,o=self.sample();m['objects']*=2
  with self.assertRaises(ValueError):qualify_document(m,o)
  m['objects']=[]
  with self.assertRaises(ValueError):qualify_document(m,[])
 def test_invalid_identity_unknown_fields_and_unbounded_input_are_rejected(self):
  m,o=self.sample()
  for invalid in ('',None,'Z'*64,'a'*63):
   bad=copy.deepcopy(m);bad['source_sha256']=invalid
   with self.assertRaises(ValueError):qualify_document(bad,o)
  o[0]['engineering_verified']=True
  with self.assertRaises(ValueError):qualify_document(m,o)
  m,o=self.sample();m['objects'][0]['source_locator']='x'*2001
  with self.assertRaises(ValueError):qualify_document(m,o)
 def test_no_mutation_and_deterministic_manifest_identity(self):
  m,o=self.sample();before=copy.deepcopy((m,o));r=qualify_document(m,o)
  self.assertEqual((m,o),before);self.assertEqual(r,qualify_document(m,list(reversed(o))))
  m['objects'][0]['payload_sha256']='e'*64
  self.assertNotEqual(r['manifest_sha256'],qualify_document(m,o)['manifest_sha256'])

class QualificationFileTests(unittest.TestCase):
 def setUp(self):
  import tempfile,json,hashlib
  from pathlib import Path
  from engineering.local_app.analysis_identity import digest,parser_identity
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
  self.source=self.root/'source.docx';self.source.write_bytes(b'SYNTHETIC SOURCE BYTES')
  self.reference=self.root/'reference.pdf';self.reference.write_bytes(b'SYNTHETIC INDEPENDENT REFERENCE BYTES')
  self.manifest,self.observations=DocumentQualificationTests().sample()
  identity=dict(source_sha256=hashlib.sha256(self.source.read_bytes()).hexdigest(),reference_sha256=hashlib.sha256(self.reference.read_bytes()).hexdigest(),parser_sha256=digest(parser_identity('docx')))
  self.manifest.update(identity);self.observations[0].update(identity)
  self.manifest_path=self.root/'manifest.json';self.manifest_path.write_text(json.dumps(self.manifest),encoding='utf-8')
  self.observation_path=self.root/'observations.json';self.observation_path.write_text(json.dumps(self.observations),encoding='utf-8')
  self.output=self.root/'result.json'
 def run_files(self,**kwargs):
  from scripts.qualify_document_corpus import compare_files
  return compare_files(self.source,self.reference,self.manifest_path,self.observation_path,self.output,backend='docx',**kwargs)
 def test_files_and_current_parser_are_checked_before_comparison(self):
  r=self.run_files();self.assertTrue(r['source_files_identity_verified']);self.assertEqual(r['comparison_status'],'PASS');self.assertFalse(r['acceptance_granted'])
 def test_changed_actual_file_blocks_before_output(self):
  self.source.write_bytes(b'changed')
  with self.assertRaisesRegex(ValueError,'IDENTITY'):self.run_files()
  self.assertFalse(self.output.exists())
 def test_changed_reference_or_parser_blocks(self):
  import json
  for field in ('reference_sha256','parser_sha256'):
   m=copy.deepcopy(self.manifest);m[field]='e'*64;self.manifest_path.write_text(json.dumps(m),encoding='utf-8')
   with self.assertRaisesRegex(ValueError,'IDENTITY'):self.run_files()
 def test_existing_output_or_input_alias_is_never_overwritten(self):
  self.output.write_text('KEEP')
  with self.assertRaises(ValueError):self.run_files()
  self.assertEqual(self.output.read_text(),'KEEP');self.output=self.source
  with self.assertRaises(ValueError):self.run_files()
  self.assertEqual(self.source.read_bytes(),b'SYNTHETIC SOURCE BYTES')
 def test_duplicate_json_key_is_rejected(self):
  self.manifest_path.write_text('{"schema":1,"schema":1}',encoding='utf-8')
  with self.assertRaisesRegex(ValueError,'DUPLICATE'):self.run_files()
 def test_source_change_during_comparison_prevents_receipt(self):
  from unittest.mock import patch
  import scripts.qualify_document_corpus as cli
  real=cli.qualify_document
  def change(*args):
   self.source.write_bytes(b'changed after start');return real(*args)
  with patch.object(cli,'qualify_document',side_effect=change):
   with self.assertRaisesRegex(ValueError,'CHANGED'):self.run_files()
  self.assertFalse(self.output.exists())
 def test_oversized_input_is_refused(self):
  from unittest.mock import patch
  with patch('scripts.qualify_document_corpus.MAX_JSON_BYTES',2):
   with self.assertRaisesRegex(ValueError,'SIZE'):self.run_files()
 def test_manifest_mutation_after_parsing_cannot_be_bound_to_new_bytes(self):
  from unittest.mock import patch
  import scripts.qualify_document_corpus as cli
  import json
  real=cli._json
  def changed(path):
   result=real(path);value=result[0] if isinstance(result,tuple) else result
   if path==self.manifest_path:
    other=copy.deepcopy(value);other['objects'][0]['payload_sha256']='f'*64;path.write_text(json.dumps(other),encoding='utf-8')
   return result
  with patch.object(cli,'_json',side_effect=changed):
   with self.assertRaisesRegex(ValueError,'CHANGED'):self.run_files()
  self.assertFalse(self.output.exists())

class NativeCellIdentityTests(unittest.TestCase):
 def test_table_native_identity_excludes_merge_metadata_and_preserves_numbers(self):
  import hashlib
  from tests.test_office_documents import docx
  from engineering.local_app.office import read
  extra='<w:tbl><w:tblGrid><w:gridCol/><w:gridCol/></w:tblGrid><w:tr><w:tc><w:tcPr><w:gridSpan w:val="2"/></w:tcPr><w:p><w:r><w:t>−1,25 кН</w:t></w:r></w:p><w:p><w:r><w:t>2,50 мм</w:t></w:r></w:p></w:tc></w:tr></w:tbl>'
  units,_=read(docx(extra=extra),'docx');cell=next(u for u in units if u['locator']['kind']=='table_cell' and '−1,25' in u['text']);identity=cell['locator'].get('native_text_identity')
  self.assertIsNotNone(identity,'Native cell identity is missing')
  value='−1,25 кН\n2,50 мм';self.assertEqual(identity['sha256'],hashlib.sha256(value.encode()).hexdigest());self.assertEqual(identity['chars'],len(value));self.assertEqual(identity['scope'],'XML_CELL_NATIVE_TEXT_BEFORE_ANNOTATIONS');self.assertFalse(identity['layout_verified']);self.assertIn('DECLARED_CELL_STRUCTURE_UNVERIFIED',cell['text'])
 def test_empty_merged_continuation_remains_empty_in_native_identity(self):
  import hashlib
  from tests.test_office_documents import docx
  from engineering.local_app.office import read
  extra='<w:tbl><w:tblGrid><w:gridCol/></w:tblGrid><w:tr><w:tc><w:tcPr><w:vMerge w:val="restart"/></w:tcPr><w:p><w:r><w:t>27</w:t></w:r></w:p></w:tc></w:tr><w:tr><w:tc><w:tcPr><w:vMerge/></w:tcPr><w:p/></w:tc></w:tr></w:tbl>'
  units,_=read(docx(extra=extra),'docx');cells=[u for u in units if u['locator']['kind']=='table_cell' and 'declared_merge' in u['locator']];self.assertIn('native_text_identity',cells[-1]['locator']);self.assertEqual(cells[-1]['locator']['native_text_identity']['sha256'],hashlib.sha256(b'').hexdigest());self.assertEqual(cells[-1]['locator']['native_text_identity']['chars'],0)

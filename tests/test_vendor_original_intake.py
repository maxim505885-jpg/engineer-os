"""Vendor originals remain inert, traceable and explicitly unparsed."""
import hashlib,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from engineering.local_app.files import preserve_file
from engineering.local_app.store import Store

class VendorOriginalIntakeTests(unittest.TestCase):
 def test_vendor_and_rich_text_originals_survive_restart_without_execution(self):
  with tempfile.TemporaryDirectory() as tmp:
   store=Store(Path(tmp));session=store.create_session()['id'];saved=[]
   payload=b'{\\rtf1 \\object \\objdata 0000} <script>untrusted()</script>\x00'
   with patch('subprocess.Popen',side_effect=AssertionError('Original intake must not launch vendor or Office')):
    for name in ('model.SPR','section.sec','results.rtf'):
     saved.append(preserve_file(store,session,name,payload))
   reopened=Store(Path(tmp));self.assertEqual(len(reopened.snapshot(session)['files']),3)
   for record in saved:
    stored=reopened.get_file(record['id']);self.assertEqual(Path(stored['path']).read_bytes(),payload)
    self.assertEqual(stored['sha256'],hashlib.sha256(payload).hexdigest());self.assertEqual(stored['text'],'')
    self.assertEqual(stored['extraction_status'],'UNAVAILABLE');self.assertTrue(stored['extraction_coverage']['stop_reasons'])
    with self.assertRaisesRegex(ValueError,'Unsupported original'):
     reopened.enqueue_extraction(session,record['id'],'native')
 def test_executable_extension_is_still_rejected(self):
  with tempfile.TemporaryDirectory() as tmp:
   store=Store(Path(tmp));session=store.create_session()['id']
   with self.assertRaises(ValueError):preserve_file(store,session,'model.spr.exe',b'MZuntrusted')
   self.assertEqual(store.snapshot(session)['files'],[])

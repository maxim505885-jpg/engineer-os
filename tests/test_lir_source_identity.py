import io,zipfile,hashlib,unittest
from engineering.local_app.files import extract_preview

class LirSourceIdentityTests(unittest.TestCase):
 def inspect(self,data):
  try:from engineering.calculation.native_source import inspect_lir
  except ImportError:self.fail('LIR source identity inspection unavailable')
  return inspect_lir(data)
 def test_native_header_records_declared_version_without_decoding(self):
  data=b'ULIRA-SAPR 2013 software ver.13.0.0.a\x00FileAnsiCP=1251 / 866\x00'+b'\x00'*100
  r=self.inspect(data)
  self.assertEqual(r['declared_format'],'LIRA-SAPR 2013');self.assertEqual(r['declared_version'],'13.0.0.a')
  self.assertEqual(r['source_sha256'],hashlib.sha256(data).hexdigest());self.assertEqual(r['status'],'BLOCK')
  self.assertFalse(r['semantics_decoded']);self.assertFalse(r['acceptance_granted'])
 def test_embedded_archive_not_misidentified_as_entire_model(self):
  stream=io.BytesIO();stream.write(b'<LIRA-SAPR 2013 software ver.13.0.0.a\x00')
  with zipfile.ZipFile(stream,'w') as z:z.writestr('0','environment');z.writestr('settings.sld','settings')
  r=self.inspect(stream.getvalue());self.assertEqual(r['embedded_archive']['member_count'],2)
  self.assertFalse(r['semantics_decoded']);self.assertIn('NATIVE_MODEL_EXPORT_REQUIRED',r['reasons'])
 def test_unrecognized_header_does_not_claim_vendor_version(self):
  r=self.inspect(b'ULIRA-SAPR synthetic container');self.assertIsNone(r['declared_version']);self.assertIn('NATIVE_HEADER_UNRECOGNIZED',r['reasons'])
 def test_preview_records_identity_but_remains_unavailable(self):
  r=extract_preview('model.lir',b'ULIRA-SAPR 2013 software ver.13.0.0.a\x00')
  self.assertEqual(r[1],'UNAVAILABLE');self.assertEqual(r[0],'')
  self.assertEqual(r[4]['model_metadata']['declared_version'],'13.0.0.a')

 def test_large_archive_inventory_is_bounded_before_member_parsing(self):
  stream=io.BytesIO();stream.write(b'<LIRA-SAPR 2013 software ver.13.0.0.a\x00')
  with zipfile.ZipFile(stream,'w') as z:
   for i in range(1001):z.writestr(str(i),'')
  r=self.inspect(stream.getvalue())
  self.assertIsNone(r['embedded_archive']);self.assertIn('EMBEDDED_ARCHIVE_INVENTORY_LIMIT',r['reasons'])

 def test_zip64_override_cannot_bypass_inventory_bounds(self):
  import struct
  stream=io.BytesIO();stream.write(b'<LIRA-SAPR 2013 software ver.13.0.0.a\x00')
  with zipfile.ZipFile(stream,'w') as z:
   for i in range(1001):z.writestr(str(i),'')
  data=stream.getvalue();at=data.rfind(b'PK\x05\x06');end=bytearray(data[at:]);fields=struct.unpack('<4s4H2LH',end[:22])
  zip64=struct.pack('<4sQHHIIQQQQ',b'PK\x06\x06',44,45,45,0,0,1001,1001,fields[5],fields[6])
  locator=struct.pack('<4sIQI',b'PK\x06\x07',0,at,1)
  end[8:16]=b'\x00'*8
  r=self.inspect(data[:at]+zip64+locator+end)
  self.assertIsNone(r['embedded_archive']);self.assertIn('EMBEDDED_ARCHIVE_INVENTORY_LIMIT',r['reasons'])

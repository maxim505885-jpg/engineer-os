import hashlib,struct,unittest
from unittest.mock import patch
from engineering.local_app import emf_text
from tests.test_emf_native_text import emf,record

def plus(kind,body=b'',flags=0):return struct.pack('<HHII',kind,flags,12+len(body),len(body))+body
HEADER=plus(0x4001,struct.pack('<4I',0xdbc01002,0,96,96))
EOF=plus(0x4002)
def comment(body):
    payload=b'EMF+'+body
    return record(70,struct.pack('<I',len(payload))+payload)
class PlusTests(unittest.TestCase):
    def read(self,records):return emf_text.read(emf(records))
    def test_inventory_offsets_hashes_and_unknown_gaps(self):
        body=HEADER+plus(0x400a,struct.pack('<II4f',1,1,0,0,2,3))+plus(0x4999)+EOF
        result=self.read([comment(body)])
        self.assertEqual(len(result.get('comment_records',[])),1)
        item=result['comment_records'][0];self.assertEqual(item['data_offset'],100);self.assertEqual(item['data_bytes'],len(body)+4)
        self.assertEqual(item['sha256'],hashlib.sha256(b'EMF+'+body).hexdigest())
        records=result['emfplus_records'];self.assertEqual(records[0]['record_offset'],104);self.assertEqual(records[1]['category'],'DRAWING')
        self.assertIn('UNKNOWN_RECORD',result['emfplus_summary']['coverage_gaps']);self.assertFalse(result['emfplus_summary']['content_verified'])
    def test_identified_invalid_framing_signature_nonfinite_counts_rejected(self):
        invalid=[b'',HEADER[:-1],plus(0x4001,struct.pack('<4I',0,0,96,96))+EOF,HEADER+plus(0x402a,struct.pack('<6f',1,0,0,1,float('nan'),0))+EOF,HEADER+plus(0x400a,struct.pack('<II',1,0xffffffff))+EOF]
        for body in invalid:
            with self.subTest(body=body),self.assertRaises(emf_text.EMFError):self.read([comment(body)])
    def test_legacy_opaque_comment_stays_unread(self):
        result=self.read([record(70,b'comment')]);self.assertEqual(result['comment_records'][0]['status'],'OPAQUE_UNREAD');self.assertIn('COMMENT_CONTENT_NOT_READ',result['limitations'])
    def test_infinite_region_and_continuation_metadata(self):
        region=struct.pack('<III',0xdbc01002,0,0x10000003)
        result=self.read([comment(HEADER+plus(0x4008,region,0x0401)+EOF)])
        self.assertEqual(result['emfplus_records'][1]['object_metadata']['region_kind'],'INFINITE')
        result=self.read([comment(HEADER+plus(0x4008,struct.pack('<I',8)+b'abcd',0x8102)),comment(plus(0x4008,b'efgh',0x0102)+EOF)])
        self.assertEqual(result['emfplus_records'][2]['continuation_status'],'COMPLETE')
    def test_bounded_comments_bytes_records_and_json(self):
        for attr in ['MAX_COMMENT_RECORDS','MAX_EMFPLUS_RECORDS','MAX_COMMENT_BYTES','MAX_REFERENCE_JSON_BYTES']:
            with patch.object(emf_text,attr,0),self.assertRaises(emf_text.EMFLimitError):self.read([comment(HEADER+EOF)])
    def test_comment_declared_span_eof_and_continuation_rejected(self):
        bad=bytearray(comment(HEADER+EOF));struct.pack_into('<I',bad,8,0xffffffff)
        variants=[[bytes(bad)],[comment(HEADER)],[comment(HEADER+EOF+plus(0x4003))],[comment(HEADER+plus(0x4008,struct.pack('<I',12)+b'abcd',0x8102)+EOF)],[comment(HEADER+plus(0x4008,b'x'*4,0x0100|64)+EOF)]]
        for records in variants:
            with self.subTest(records=records),self.assertRaises(emf_text.EMFError):self.read(records)
    def test_inventory_category_counts_distinguish_coverage(self):
        result=self.read([comment(HEADER+plus(0x4008,b'unknown!',0x7f01)+EOF)])
        summary=result['emfplus_summary']
        self.assertEqual(summary.get('category_counts'),{'CONTROL':2,'OBJECT':1})
        self.assertIn('UNKNOWN_OBJECT_TYPE',summary['coverage_gaps'])

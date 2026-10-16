import hashlib,io,tempfile,threading,unittest
from pathlib import Path
from runtime.office_input import write_input_disk,read_input_stream,OfficeInputError,HEADER_SIZE,MAX_INPUT

class OfficeInputTests(unittest.TestCase):
    def disk(self,data):
        with tempfile.TemporaryDirectory() as tmp:
            source=Path(tmp)/'source';target=Path(tmp)/'input.raw';source.write_bytes(data)
            sha=hashlib.sha256(data).hexdigest();write_input_disk(source,target,sha,stop=threading.Event())
            self.assertEqual(source.read_bytes(),data)
            return target.read_bytes(),sha
    def test_source_roundtrip_and_sector_alignment(self):
        for data in (b'x',b'a'*512,b'b'*100001):
            raw,sha=self.disk(data);self.assertEqual(len(raw)%512,0)
            self.assertEqual(read_input_stream(io.BytesIO(raw),sha),data)
    def test_truncated_tampered_or_trailing_data_rejected(self):
        raw,sha=self.disk(b'owned')
        for bad in (raw[:HEADER_SIZE-1],raw[:-1],raw+b'x',raw[:HEADER_SIZE]+b'X'+raw[HEADER_SIZE+1:],raw[:-1]+b'x'):
            with self.subTest(size=len(bad)),self.assertRaises(OfficeInputError):read_input_stream(io.BytesIO(bad),sha)
        with self.assertRaises(OfficeInputError):read_input_stream(io.BytesIO(raw),'a'*64)
    def test_oversized_header_rejected_before_payload_read(self):
        import struct
        raw,sha=self.disk(b'owned');offset=len(b'ENGINEER_OFFICE_INPUT_V1\0')
        bad=raw[:offset]+struct.pack('>Q',MAX_INPUT+1)+raw[offset+8:]
        with self.assertRaises(OfficeInputError):read_input_stream(io.BytesIO(bad),sha)
    def test_cancelled_writer_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'source';p.write_bytes(b'owned');stop=threading.Event();stop.set()
            with self.assertRaises(OfficeInputError):write_input_disk(p,Path(tmp)/'raw',hashlib.sha256(b'owned').hexdigest(),stop=stop)
if __name__=='__main__':unittest.main()

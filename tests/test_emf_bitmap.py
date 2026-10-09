"""Recover hidden DIB pixels without claiming EMF playback or Word layout."""
import io
import struct
import unittest
from unittest.mock import patch
from PIL import Image
from engineering.local_app import office,preview,emf_text
from tests.test_emf_native_text import emf,vector_doc
from tests import test_office_documents as fixtures


def bitmap_record(kind=81,depth=24,top_down=True):
    width,height=2,2;stride=((width*depth+31)//32)*4
    # Top row red,green; bottom blue,white; 32-bit fourth byte deliberately nonzero, never alpha.
    rows=[[(255,0,0),(0,255,0)],[(0,0,255),(255,255,255)]]
    if not top_down:rows.reverse()
    bits=b''
    for row in rows:
        raw=b''.join(bytes((b,g,r))+(b'\xff' if depth==32 else b'') for r,g,b in row)
        bits+=raw+b'\0'*(stride-len(raw))
    fixed=80 if kind==81 else 100
    header=struct.pack('<IiiHH6I',40,width,-height if top_down else height,1,depth,0,len(bits),0,0,0,0)
    out=bytearray(fixed);struct.pack_into('<II',out,0,kind,fixed+40+len(bits))
    struct.pack_into('<4I',out,48 if kind==81 else 84,fixed,40,fixed+40,len(bits))
    struct.pack_into('<I',out,68 if kind==81 else 40,0xcc0020)
    return bytes(out)+header+bits


class BitmapReaderTests(unittest.TestCase):
    def test_docx_exposes_pixels_identity_and_exact_record_offsets(self):
        units,_=office.read(vector_doc(emf([bitmap_record()])),'docx')
        records=units[0]['locator']['images'][0]['native_emf'].get('bitmap_records',[])
        self.assertEqual(len(records),1,'EMF embedded raster currently omitted')
        b=records[0];self.assertEqual(b['status'],'AVAILABLE')
        self.assertEqual((b['record_offset'],b['bmi_offset'],b['bits_offset']),(88,168,208))
        self.assertEqual((b['width'],b['height'],b['top_down']),(2,2,True))
        self.assertFalse(b['layout_verified']);self.assertFalse(b['content_verified'])

    def test_orientation_padding_and_reserved_alpha_are_source_pixels(self):
        from engineering.local_app import emf_bitmap
        for kind in [76,81]:
            for depth in [24,32]:
                for top in [True,False]:
                    data=emf([bitmap_record(kind,depth,top)])
                    b=emf_text.read(data)['bitmap_records'][0];im=emf_bitmap.decode(data,b)
                    self.assertEqual(im.mode,'RGB');self.assertEqual(im.size,(2,2))
                    self.assertEqual([im.getpixel((x,y)) for y in range(2) for x in range(2)],[(255,0,0),(0,255,0),(0,0,255),(255,255,255)])

    def test_malformed_spans_and_unsupported_compression_cannot_preview(self):
        from engineering.local_app import emf_bitmap
        good=bytearray(emf([bitmap_record()]));variants=[]
        for where,value in [(88+48,4),(88+56,80),(88+60,0xffffffff),(168+16,1),(168+32,1)]:
            bad=good.copy();struct.pack_into('<I',bad,where,value);variants.append(bad)
        for data in variants:
            b=emf_text.read(bytes(data))['bitmap_records'][0]
            self.assertEqual(b['status'],'UNAVAILABLE')
            with self.assertRaises(ValueError):emf_bitmap.decode(bytes(data),b)

    def test_pixel_and_record_budgets_are_enforced_before_decode(self):
        from engineering.local_app import emf_bitmap
        data=emf([bitmap_record()])
        with patch.object(emf_bitmap,'MAX_PIXELS',1):self.assertEqual(emf_text.read(data)['bitmap_records'][0]['status'],'UNAVAILABLE')
        with patch.object(emf_bitmap,'MAX_BITMAP_RECORDS',0),self.assertRaises(emf_text.EMFLimitError):emf_text.read(data)

    def test_source_free_and_unsupported_or_unaligned_payloads_stay_unread(self):
        free=bytearray(100);struct.pack_into('<II',free,0,76,100)
        self.assertEqual(emf_text.read(emf([bytes(free)]))['bitmap_records'],[])
        for where,value in [(88+48,81),(168,108)]:
            bad=bytearray(emf([bitmap_record()]));struct.pack_into('<I',bad,where,value)
            self.assertEqual(emf_text.read(bytes(bad))['bitmap_records'][0]['status'],'UNAVAILABLE')
        from engineering.local_app import emf_bitmap
        data=emf([bitmap_record()])
        with patch.object(emf_bitmap,'MAX_BITMAP_BYTES',16):self.assertEqual(emf_text.read(data)['bitmap_records'][0]['status'],'AVAILABLE')
        with patch.object(emf_bitmap,'MAX_BITMAP_BYTES',15):self.assertEqual(emf_text.read(data)['bitmap_records'][0]['status'],'UNAVAILABLE')


class BitmapPipelineTests(unittest.TestCase):
    setUp=fixtures.OfficeTests.setUp
    run_doc=fixtures.OfficeTests.run_doc
    def test_source_bound_embedded_preview_keeps_original_and_no_acceptance(self):
        data=vector_doc(emf([bitmap_record()]));f,job,_,result=self.run_doc('bitmap.docx',data)
        ref=self.store.analysis_receipts(self.session,job['id'])['records'][0]['refs'][0]
        png=preview.render_office_image(self.store,self.session,ref['source_job'],1,1,bitmap=1)
        with Image.open(io.BytesIO(png)) as im:self.assertEqual(im.getpixel((0,0)),(255,0,0))
        with self.assertRaises(ValueError):preview.render_office_image(self.store,self.session,ref['source_job'],1,1)
        with self.assertRaises(ValueError):preview.render_office_image(self.store,self.session,ref['source_job'],1,1,bitmap=2)
        with self.assertRaises(ValueError):preview.render_office_image(self.store,self.store.create_session()['id'],ref['source_job'],1,1,bitmap=1)
        from pathlib import Path
        p=Path(self.store.get_file(f['id'])['path']);self.assertEqual(p.read_bytes(),data)
        p.write_bytes(b'changed')
        with self.assertRaises(ValueError):preview.render_office_image(self.store,self.session,ref['source_job'],1,1,bitmap=1)
        self.assertFalse(result['result']['acceptance_granted'])


class BitmapHTTPTests(unittest.TestCase):
    def test_authenticated_http_preview_uses_exact_bitmap_ordinal(self):
        import threading
        from http.client import HTTPConnection
        from engineering.local_app.server import make_server
        from engineering.local_app.files import preserve_file
        from engineering.local_app.worker import Worker
        fixtures.OfficeTests.setUp(self)
        data=vector_doc(emf([bitmap_record(),bitmap_record(depth=32)]))
        f=preserve_file(self.store,self.session,'bitmap.docx',data)
        job=self.store.enqueue(self.session,'Read',[f['id']]);model=fixtures.Model();Worker(self.store,model).run_once()
        ref=self.store.analysis_receipts(self.session,job['id'])['records'][0]['refs'][0]
        server=make_server(self.store,model,drive_client=None);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        def request(session,bitmap='1',token=True):
            conn=HTTPConnection('127.0.0.1',server.server_port,timeout=5)
            try:
                path=f'/api/sessions/{session}/jobs/{ref["source_job"]}/images?unit=1&image=1&bitmap={bitmap}'
                conn.request('GET',path,headers={'X-Engineer-Token':server.token} if token else {})
                res=conn.getresponse();return res.status,res.getheader('Content-Type'),res.read()
            finally:conn.close()
        try:
            for index in ['1','2']:
                status,kind,png=request(self.session,index);self.assertEqual((status,kind),(200,'image/png'))
                with Image.open(io.BytesIO(png)) as im:self.assertEqual(im.getpixel((0,1)),(0,0,255))
            self.assertEqual(request(self.session,token=False)[0],403)
            for index in ['0','-1','3','abc']:self.assertEqual(request(self.session,index)[0],400)
            self.assertEqual(request(self.store.create_session()['id'])[0],400)
            self.assertEqual(self.store.snapshot(self.session)['evidence'],[])
        finally:server.shutdown();server.server_close();thread.join()

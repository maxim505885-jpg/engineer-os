"""Masked DIB source colors must come from declared masks, never guessed RGB."""
import io
import struct
import unittest
from PIL import Image
from engineering.local_app import emf_text,emf_bitmap,office,preview
from tests.test_emf_native_text import emf,vector_doc,text_record
from tests import test_office_documents as fixtures


def masked_bitmap_record(depth=32,masks=None,kind=76,top_down=True):
    masks=masks or ((0xff0000,0xff00,0xff) if depth==32 else (0xf800,0x7e0,0x1f))
    width=2;height=2;stride=((width*depth+31)//32)*4
    # Original four source pixels: red,green / blue,white.
    values=[masks[0],masks[1],masks[2],masks[0]|masks[1]|masks[2]]
    rows=[values[:2],values[2:]]
    if not top_down:rows.reverse()
    bits=b''
    for row in rows:
        raw=b''.join(v.to_bytes(depth//8,'little') for v in row);bits+=raw+b'\0'*(stride-len(raw))
    fixed=100 if kind==76 else 80
    header=struct.pack('<IiiHH6I',40,width,-height if top_down else height,1,depth,3,len(bits),0,0,0,0)+struct.pack('<3I',*masks)
    out=bytearray(fixed);struct.pack_into('<II',out,0,kind,fixed+52+len(bits))
    struct.pack_into('<4I',out,84 if kind==76 else 48,fixed,52,fixed+52,len(bits))
    struct.pack_into('<I',out,40 if kind==76 else 68,0xcc0020)
    return bytes(out)+header+bits


class BitfieldsTests(unittest.TestCase):
    def test_actual_missing_format_is_read_as_declared_masked_source(self):
        data=emf([masked_bitmap_record()]);b=emf_text.read(data)['bitmap_records'][0]
        self.assertEqual(b['status'],'AVAILABLE','Actual image465 BI_BITFIELDS payload omitted')
        self.assertEqual(b['color_masks'],[0xff0000,0xff00,0xff])
        self.assertEqual((b['bmi_offset'],b['bmi_bytes'],b['bits_offset']),(188,52,240))
        im=emf_bitmap.decode(data,b);self.assertEqual(im.mode,'RGB')
        self.assertEqual([im.getpixel((x,y)) for y in range(2) for x in range(2)],[(255,0,0),(0,255,0),(0,0,255),(255,255,255)])

    def test_standard_16_and_32_masks_orientation_match_independent_bmp_decoder(self):
        for depth,masks in [(32,(0xff0000,0xff00,0xff)),(16,(0xf800,0x7e0,0x1f)),(16,(0x7c00,0x3e0,0x1f))]:
            for top in [True,False]:
                for kind in [76,81]:
                    data=emf([masked_bitmap_record(depth,masks,kind,top)])
                    b=emf_text.read(data)['bitmap_records'][0];self.assertEqual(b['status'],'AVAILABLE')
                    bmi=data[b['bmi_offset']:b['bmi_offset']+b['bmi_bytes']];bits=data[b['bits_offset']:b['bits_offset']+b['bits_bytes']]
                    raw=struct.pack('<2sIHHI',b'BM',14+len(bmi)+len(bits),0,0,14+len(bmi))+bmi+bits
                    expected=Image.open(io.BytesIO(raw)).convert('RGB');actual=emf_bitmap.decode(data,b)
                    self.assertEqual(actual.tobytes(),expected.tobytes())

    def test_invalid_or_unimplemented_masks_stay_unavailable(self):
        cases=[((0,0xff00,0xff),'INVALID_COLOR_MASKS'),((0xff00,0xff00,0xff),'INVALID_COLOR_MASKS'),((0x550000,0xff00,0xff),'INVALID_COLOR_MASKS'),((0x3ff00000,0xffc00,0x3ff),'UNSUPPORTED_COLOR_MASKS')]
        for masks,reason in cases:
            data=emf([masked_bitmap_record(masks=masks)]);b=emf_text.read(data)['bitmap_records'][0]
            self.assertEqual((b['status'],b['reason']),('UNAVAILABLE',reason))
            with self.assertRaises(ValueError):emf_bitmap.decode(data,b)

    def test_missing_masks_and_out_of_depth_masks_are_not_guessed(self):
        for depth in [24,16]:
            data=bytearray(emf([masked_bitmap_record()]));struct.pack_into('<H',data,188+14,depth)
            b=emf_text.read(bytes(data))['bitmap_records'][0];self.assertEqual(b['status'],'UNAVAILABLE')
        data=bytearray(emf([masked_bitmap_record()]));struct.pack_into('<I',data,88+88,40)
        self.assertEqual(emf_text.read(bytes(data))['bitmap_records'][0]['status'],'UNAVAILABLE')

    def test_mask_tamper_cannot_reuse_a_payload_descriptor(self):
        data=bytearray(emf([masked_bitmap_record()]));b=emf_text.read(bytes(data))['bitmap_records'][0]
        struct.pack_into('<I',data,188+40,0xff)
        with self.assertRaises(ValueError):emf_bitmap.decode(bytes(data),b)


class BitfieldsPipelineTests(unittest.TestCase):
    setUp=fixtures.OfficeTests.setUp
    run_doc=fixtures.OfficeTests.run_doc
    def test_controlled_source_reaches_receipt_and_safe_preview(self):
        data=vector_doc(emf([masked_bitmap_record()]));f,job,_,result=self.run_doc('masked.docx',data)
        ref=self.store.analysis_receipts(self.session,job['id'])['records'][0]['refs'][0]
        self.assertIsNone(ref['page']);b=ref['locator']['images'][0]['native_emf']['bitmap_records'][0]
        self.assertEqual(b['color_masks'],[0xff0000,0xff00,0xff])
        png=preview.render_office_image(self.store,self.session,ref['source_job'],1,1,bitmap=1)
        with Image.open(io.BytesIO(png)) as im:self.assertEqual(im.getpixel((0,0)),(255,0,0))
        self.assertFalse(result['result']['acceptance_granted'])
        from pathlib import Path
        self.assertEqual(Path(self.store.get_file(f['id'])['path']).read_bytes(),data)

    def test_clipped_parent_text_does_not_hide_exact_source_image_or_confirm_quote(self):
        from engineering.local_app.source_binding import office_location
        from unittest.mock import patch
        data=vector_doc(emf([text_record('Источник '*4000),masked_bitmap_record()]))
        f,job,_,result=self.run_doc('long-masked.docx',data)
        ref=self.store.analysis_receipts(self.session,job['id'])['records'][0]['refs'][0]
        source_job=ref['source_job'];file=self.store.get_file(f['id'])
        checkpoint=self.store.extraction_page(self.session,source_job,1)
        self.assertTrue(checkpoint['text_truncated']);self.assertIn('TEXT_LIMIT',checkpoint['limitations'])
        with self.assertRaises(ValueError):office_location(self.store,self.session,file,source_job,1,'Источник')
        png=preview.render_office_image(self.store,self.session,source_job,1,1,bitmap=1)
        with Image.open(io.BytesIO(png)) as im:self.assertEqual(im.getpixel((0,0)),(255,0,0))
        self.assertFalse(result['result']['acceptance_granted'])
        import copy
        for kind in ['text','locator','truncation']:
            bad=copy.deepcopy(checkpoint)
            if kind=='text':bad['blocks'][0]['text']='FORGED'+bad['blocks'][0]['text']
            elif kind=='locator':bad['locator']['images'][0]['sha256']='0'*64
            else:bad['text_truncated']=False
            with patch.object(self.store,'extraction_page',return_value=bad):
                with self.assertRaises(ValueError):preview.render_office_image(self.store,self.session,source_job,1,1,bitmap=1)

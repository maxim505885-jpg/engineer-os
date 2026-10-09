import importlib
import io
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import fitz
from PIL import Image,ImageDraw,ImageFont
from engineering.local_app.files import preserve_file
from engineering.local_app.store import Store
from engineering.local_app.worker import Worker


class LocalOCRTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.store=Store(Path(self.tmp.name));self.session=self.store.create_session()['id']

    def test_missing_engine_is_explicit_and_does_not_claim_ocr(self):
        module=importlib.import_module('engineering.local_app.ocr')
        with patch.dict(os.environ,{'ENGINEER_OS_TESSERACT_BIN':str(Path(self.tmp.name)/'missing')}):
            self.assertFalse(module.identity()['available'])
            with self.assertRaises(module.OCRError):module.TesseractOCR()

    def test_missing_language_models_are_not_silently_replaced(self):
        module=importlib.import_module('engineering.local_app.ocr')
        with patch.dict(os.environ,{'ENGINEER_OS_TESSDATA_DIR':self.tmp.name}):
            self.assertFalse(module.identity()['available'])

    def test_scanned_cyrillic_and_english_have_source_boxes(self):
        module=importlib.import_module('engineering.local_app.ocr')
        if not module.identity()['available']:self.skipTest('Local rus+eng models unavailable; live corpus checks separately')
        image=Image.new('RGB',(1400,400),'white');draw=ImageDraw.Draw(image)
        font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',60)
        draw.text((60,100),'Высота здания 4 метра. Height 4 metres.',font=font,fill='black')
        buffer=io.BytesIO();image.save(buffer,format='PNG')
        file=preserve_file(self.store,self.session,'scan.png',buffer.getvalue())
        job=self.store.enqueue_extraction(self.session,file['id'],'ocr');Worker(self.store,None).run_once()
        snap=self.store.snapshot(self.session);self.assertEqual(snap['jobs'][0]['state'],'SUCCEEDED')
        record=self.store.extraction_page(self.session,job['id'],1)
        text=' '.join(b['text'] for b in record['blocks'])
        self.assertIn('Высота',text);self.assertIn('Height',text)
        self.assertTrue(all(b['provenance'][0]['bbox'] for b in record['blocks']))
        self.assertEqual(record['ocr'],'EXECUTED_UNVERIFIED')
        self.assertFalse(record['acceptance_granted'])
        self.assertEqual(Path(self.store.get_file(file['id'])['path']).read_bytes(),buffer.getvalue())

    def test_timeout_is_fixed_failure_without_private_stderr(self):
        module=importlib.import_module('engineering.local_app.ocr')
        if not module.identity()['available']:self.skipTest('Local rus+eng models unavailable')
        import subprocess
        recognizer=module.TesseractOCR()
        with fitz.open() as document:
            page=document.new_page()
            with patch.object(module.subprocess,'run',side_effect=subprocess.TimeoutExpired('private',1)):
                with self.assertRaisesRegex(module.OCRError,'OCR_TIMEOUT'):recognizer.page_blocks(page,1)

    def test_oversized_image_is_refused_before_ocr_for_manual_and_automatic_tasks(self):
        image=Image.new('RGB',(4001,4000),'white');data=io.BytesIO();image.save(data,format='PNG')
        for automatic in (False,True):
            session=self.store.create_session()['id'];file=preserve_file(self.store,session,'large.png',data.getvalue())
            job=self.store.enqueue(session,'Read',[file['id']]) if automatic else self.store.enqueue_extraction(session,file['id'],'ocr')
            with patch('engineering.local_app.ocr.TesseractOCR.page_blocks') as recognize:
                Worker(self.store,None).run_once();recognize.assert_not_called()
            self.assertEqual(self.store.snapshot(session)['jobs'][0]['state'],'FAILED')

    def test_rotated_cropped_ocr_coordinates_remain_unrotated(self):
        module=importlib.import_module('engineering.local_app.ocr')
        if not module.identity()['available']:self.skipTest('Local rus+eng models unavailable')
        for rotation in (0,90,180,270):
            with self.subTest(rotation=rotation),fitz.open() as document:
                page=document.new_page(width=600,height=800);page.insert_text((160,220),'Height 4 metres',fontsize=30)
                page.set_cropbox(fitz.Rect(100,100,500,700));page.set_rotation(rotation)
                blocks=module.TesseractOCR().page_blocks(page,1)
                block=next(b for b in blocks if 'Height' in b['text']);box=block['provenance'][0]['bbox']
                self.assertTrue(50<=box['left']<=80 and 90<=box['top']<=130,box)
                self.assertTrue(200<=box['right']<=350 and 115<=box['bottom']<=140,box)
                self.assertEqual(page.rotation,rotation)

    def test_ocr_cancel_resume_reuses_page_and_rejects_changed_models(self):
        module=importlib.import_module('engineering.local_app.ocr')
        if not module.identity()['available']:self.skipTest('Local rus+eng models unavailable')
        with fitz.open() as document:
            for _ in range(2):document.new_page().insert_text((60,120),'Height 4 metres',fontsize=30)
            file=preserve_file(self.store,self.session,'scan.pdf',document.tobytes())
        job=self.store.enqueue_extraction(self.session,file['id'],'ocr');original=module.TesseractOCR.page_blocks;calls=[]
        def cancel(parser,page,number):
            calls.append(number);blocks=original(parser,page,number);self.store.cancel(self.session,job['id']);return blocks
        with patch.object(module.TesseractOCR,'page_blocks',cancel):Worker(self.store,None).run_once()
        saved=self.store.extraction_page(self.session,job['id'],1)
        with patch.dict(os.environ,{'ENGINEER_OS_TESSDATA_DIR':self.tmp.name}):
            with self.assertRaisesRegex(ValueError,'Parser identity changed'):self.store.resume_extraction(self.session,job['id'])
        self.store.resume_extraction(self.session,job['id'])
        def capture(parser,page,number):calls.append(number);return original(parser,page,number)
        with patch.object(module.TesseractOCR,'page_blocks',capture):Worker(self.store,None).run_once()
        self.assertEqual(calls,[1,2]);self.assertEqual(self.store.extraction_page(self.session,job['id'],1),saved)

    def test_tsv_literal_quote_never_consumes_following_rows(self):
        module=importlib.import_module('engineering.local_app.ocr')
        header='level\tpage_num\tblock_num\tpar_num\tline_num\tword_num\tleft\ttop\twidth\theight\tconf\ttext\n'
        tsv=header+'5\t1\t1\t1\t1\t1\t10\t10\t10\t10\t90\t"\n'+'5\t1\t1\t1\t1\t2\t30\t10\t30\t10\t90\tHeight\n'
        blocks=module.TesseractOCR._blocks(tsv,1,1,100,100)
        self.assertEqual(blocks[0]['text'],'" Height');self.assertNotIn('\t',blocks[0]['text'])

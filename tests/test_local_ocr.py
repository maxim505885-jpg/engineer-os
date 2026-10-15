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

    def test_region_mode_preserves_whole_pass_and_cropped_rotated_coordinates(self):
        module=importlib.import_module('engineering.local_app.ocr')
        if not module.identity()['available']:self.skipTest('Local rus+eng models unavailable')
        with patch.dict(os.environ,{'ENGINEER_OS_OCR_LAYOUT':'regions'}),fitz.open() as document:
            page=document.new_page(width=600,height=800)
            page.insert_text((160,220),'Height 4 metres',fontsize=30)
            page.insert_text((320,580),'Width 8 metres',fontsize=30)
            page.set_cropbox(fitz.Rect(100,100,550,700));page.set_rotation(90)
            crop=list(page.cropbox);recognizer=module.TesseractOCR()
            blocks=recognizer.page_blocks(page,1)
            self.assertTrue({'whole','r1'}<={b.get('ocr_region') for b in blocks})
            self.assertTrue({b.get('ocr_region') for b in blocks}<={'whole','r1','r2','r3','r4'})
            regional=[b for b in blocks if b.get('ocr_region')!='whole' and 'Height' in b['text']]
            self.assertTrue(regional)
            box=regional[0]['provenance'][0]['bbox']
            self.assertTrue(50<=box['left']<=80 and 90<=box['top']<=130,box)
            self.assertEqual(page.rotation,90);self.assertEqual(list(page.cropbox),crop)
            self.assertEqual(len({b['block_id'] for b in blocks}),len(blocks))
            dossier=recognizer.last_page_dossier
            self.assertEqual(dossier['completed_passes'],5)
            self.assertEqual(dossier['coverage'],'WHOLE_PAGE_AND_REGIONS_EXECUTED')
            self.assertFalse(dossier['quality_verified'])
            self.assertFalse(dossier['acceptance_granted'])

    def test_region_worker_persists_coverage_but_never_claims_acceptance(self):
        module=importlib.import_module('engineering.local_app.ocr')
        if not module.identity()['available']:self.skipTest('Local rus+eng models unavailable')
        with patch.dict(os.environ,{'ENGINEER_OS_OCR_LAYOUT':'regions'}):
            with fitz.open() as document:
                document.new_page().insert_text((60,120),'Height 4 metres',fontsize=30)
                original=document.tobytes()
            file=preserve_file(self.store,self.session,'regions.pdf',original)
            job=self.store.enqueue_extraction(self.session,file['id'],'ocr');Worker(self.store,None).run_once()
            record=self.store.extraction_page(self.session,job['id'],1)
            self.assertEqual(record['ocr_dossier']['completed_passes'],5)
            self.assertIn('OCR_REGION_CANDIDATES_UNMERGED',record['limitations'])
            self.assertFalse(record['acceptance_granted'])
            self.assertEqual(Path(self.store.get_file(file['id'])['path']).read_bytes(),original)
            with patch.dict(os.environ,{'ENGINEER_OS_OCR_LAYOUT':'whole'}):
                from engineering.local_app.analysis_identity import parser_identity
                self.assertNotEqual(self.store.extraction_job(self.session,job['id'])['result']['extraction']['parser_identity'],parser_identity('ocr'))

    def test_layout_is_part_of_parser_identity_and_invalid_layout_is_rejected(self):
        module=importlib.import_module('engineering.local_app.ocr')
        if not module.identity()['available']:self.skipTest('Local rus+eng models unavailable')
        with patch.dict(os.environ,{'ENGINEER_OS_OCR_LAYOUT':'whole'}):whole=module.identity()
        with patch.dict(os.environ,{'ENGINEER_OS_OCR_LAYOUT':'regions'}):regional=module.identity()
        self.assertNotEqual(whole,regional)
        with patch.dict(os.environ,{'ENGINEER_OS_OCR_LAYOUT':'unexpected'}):
            with self.assertRaisesRegex(module.OCRError,'OCR_INVALID_LAYOUT'):module.TesseractOCR()

    def _fake_tesseract(self,command,**kwargs):
        from types import SimpleNamespace
        header='level\tpage_num\tblock_num\tpar_num\tline_num\tword_num\tleft\ttop\twidth\theight\tconf\ttext\n'
        text=header+'5\t1\t1\t1\t1\t1\t10\t10\t10\t10\t90\tHeight\n'
        Path(command[2]).with_suffix('.tsv').write_text(text)
        return SimpleNamespace(returncode=0)

    def test_region_output_budget_is_shared_and_partial_page_is_not_success(self):
        module=importlib.import_module('engineering.local_app.ocr')
        if not module.identity()['available']:self.skipTest('Local rus+eng models unavailable')
        with patch.dict(os.environ,{'ENGINEER_OS_OCR_LAYOUT':'regions'}),fitz.open() as document:
            recognizer=module.TesseractOCR();page=document.new_page();page.set_rotation(180)
            with patch.object(module,'MAX_OUTPUT',220),patch.object(module.subprocess,'run',side_effect=self._fake_tesseract):
                with self.assertRaisesRegex(module.OCRError,'OCR_OUTPUT_LIMIT'):recognizer.page_blocks(page,1)
            self.assertEqual(page.rotation,180)
            self.assertLess(recognizer.last_page_dossier['completed_passes'],5)
            self.assertEqual(recognizer.last_page_dossier['coverage'],'INCOMPLETE')

    def test_region_word_budget_is_shared(self):
        module=importlib.import_module('engineering.local_app.ocr')
        if not module.identity()['available']:self.skipTest('Local rus+eng models unavailable')
        with patch.dict(os.environ,{'ENGINEER_OS_OCR_LAYOUT':'regions'}),fitz.open() as document:
            recognizer=module.TesseractOCR();page=document.new_page()
            with patch.object(module,'MAX_WORDS',2),patch.object(module.subprocess,'run',side_effect=self._fake_tesseract):
                with self.assertRaisesRegex(module.OCRError,'OCR_WORD_LIMIT'):recognizer.page_blocks(page,1)

    def test_region_timeout_is_shared_between_passes(self):
        module=importlib.import_module('engineering.local_app.ocr')
        if not module.identity()['available']:self.skipTest('Local rus+eng models unavailable')
        with patch.dict(os.environ,{'ENGINEER_OS_OCR_LAYOUT':'regions'}),fitz.open() as document:
            recognizer=module.TesseractOCR();page=document.new_page()
            clock=[0]
            def slow(command,**kwargs):
                result=self._fake_tesseract(command,**kwargs);clock[0]+=31;return result
            with patch.object(module.subprocess,'run',side_effect=slow),patch.object(module.time,'monotonic',side_effect=lambda:clock[0]):
                with self.assertRaisesRegex(module.OCRError,'OCR_TIMEOUT'):recognizer.page_blocks(page,1)
            self.assertEqual(recognizer.last_page_dossier['completed_passes'],1)

    def test_late_final_pass_cannot_claim_complete_coverage(self):
        module=importlib.import_module('engineering.local_app.ocr')
        if not module.identity()['available']:self.skipTest('Local rus+eng models unavailable')
        with patch.dict(os.environ,{'ENGINEER_OS_OCR_LAYOUT':'whole'}),fitz.open() as document:
            recognizer=module.TesseractOCR();page=document.new_page();clock=[0]
            def late(command,**kwargs):
                result=self._fake_tesseract(command,**kwargs);clock[0]=61;return result
            with patch.object(module.subprocess,'run',side_effect=late),patch.object(module.time,'monotonic',side_effect=lambda:clock[0]):
                with self.assertRaisesRegex(module.OCRError,'OCR_TIMEOUT'):recognizer.page_blocks(page,1)
            self.assertEqual(recognizer.last_page_dossier['coverage'],'INCOMPLETE')

    def test_region_pixel_budget_is_shared(self):
        module=importlib.import_module('engineering.local_app.ocr')
        if not module.identity()['available']:self.skipTest('Local rus+eng models unavailable')
        with patch.dict(os.environ,{'ENGINEER_OS_OCR_LAYOUT':'regions'}),fitz.open() as document:
            recognizer=module.TesseractOCR();page=document.new_page(width=100,height=100)
            with patch.object(module,'MAX_PAGE_PIXELS',70000),patch.object(module.subprocess,'run',side_effect=self._fake_tesseract):
                with self.assertRaisesRegex(module.OCRError,'OCR_PIXEL_LIMIT'):recognizer.page_blocks(page,1)

    def test_late_parsing_cannot_claim_complete_coverage(self):
        module=importlib.import_module('engineering.local_app.ocr')
        if not module.identity()['available']:self.skipTest('Local rus+eng models unavailable')
        with patch.dict(os.environ,{'ENGINEER_OS_OCR_LAYOUT':'whole'}),fitz.open() as document:
            recognizer=module.TesseractOCR();page=document.new_page();clock=[0]
            original=recognizer._blocks
            def late(*args,**kwargs):
                blocks=original(*args,**kwargs);clock[0]=61;return blocks
            with patch.object(module.subprocess,'run',side_effect=self._fake_tesseract),patch.object(module.time,'monotonic',side_effect=lambda:clock[0]),patch.object(recognizer,'_blocks',side_effect=late):
                with self.assertRaisesRegex(module.OCRError,'OCR_TIMEOUT'):recognizer.page_blocks(page,1)
            self.assertEqual(recognizer.last_page_dossier['coverage'],'INCOMPLETE')

"""Independent PDF fixtures for selected-region candidate readback."""
import base64
import hashlib
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import fitz
from engineering.local_app import region_readback as reader

TESSDATA=os.environ.get('ENGINEER_OS_TESSDATA_DIR','/usr/share/tesseract-ocr/5/tessdata')


class RegionReadbackTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.source=Path(self.tmp.name)/'source.pdf'

    def save(self,document):
        document.save(self.source)
        raw=self.source.read_bytes()
        return raw,hashlib.sha256(raw).hexdigest()

    def test_native_exact_selection_rotation_crop_and_png_provenance(self):
        with fitz.open() as doc:
            page=doc.new_page(width=600,height=800)
            page.insert_text((140,180),'56320',fontsize=12)
            page.insert_text((300,180),'OUTSIDE',fontsize=12)
            page.set_cropbox(fitz.Rect(100,100,500,700));page.set_rotation(90)
            raw,sha=self.save(doc)
        bbox=[30,60,100,90]
        result=reader.recognize(self.source,1,bbox,sha)
        self.assertEqual(result['source_bbox'],bbox)
        self.assertEqual(result['coordinate_space'],'UNROTATED_CROP_RELATIVE')
        self.assertEqual([w['text'] for w in result['native_words']],['56320'])
        self.assertEqual(result['native_blocks'][0]['text'],'56320')
        word=result['native_words'][0]['bbox']
        self.assertAlmostEqual(word['left'],40);self.assertAlmostEqual(word['top'],67.1,places=2)
        self.assertAlmostEqual(word['right'],73.36,places=2);self.assertAlmostEqual(word['bottom'],83.588,places=2)
        image=result['rendered_region'];png=base64.b64decode(image['png_base64'])
        self.assertEqual(image['source_sha256'],sha)
        self.assertEqual(image['page_no'],1)
        self.assertEqual(hashlib.sha256(png).hexdigest(),image['png_sha256'])
        with fitz.open(stream=raw,filetype='pdf') as independent:
            page=independent[0];page.set_rotation(0)
            expected=page.get_pixmap(matrix=fitz.Matrix(image['scale'],image['scale']),clip=fitz.Rect(bbox),alpha=False,colorspace=fitz.csRGB).tobytes('png')
        self.assertEqual(png,expected)
        self.assertEqual(self.source.read_bytes(),raw)
        for key in ('quality_verified','acceptance_granted','page_complete','document_complete'):
            self.assertFalse(result[key])

    def test_reject_invalid_geometry_hash_page_and_symlink(self):
        with fitz.open() as doc:
            doc.new_page(width=100,height=100);raw,sha=self.save(doc)
        for bbox in ([0,0,101,10],[0,0,0,10],[0,0,float('nan'),10],[True,0,10,10],None):
            with self.subTest(bbox=bbox),self.assertRaisesRegex(ValueError,'INVALID_REGION'):
                reader.recognize(self.source,1,bbox,sha)
        for number in (True,0,2,1.5):
            with self.assertRaisesRegex(ValueError,'INVALID_PAGE'):reader.recognize(self.source,number,[0,0,10,10],sha)
        with self.assertRaisesRegex(ValueError,'SHA256'):reader.recognize(self.source,1,[0,0,10,10],'0'*64)
        link=self.source.with_name('alias.pdf');link.symlink_to(self.source)
        with self.assertRaisesRegex(ValueError,'UNSAFE_SOURCE'):reader.recognize(link,1,[0,0,10,10],sha)

    def test_limits_checked_and_source_change_detected(self):
        with fitz.open() as doc:
            doc.new_page(width=100,height=100);raw,sha=self.save(doc)
        with patch.object(reader,'MAX_SOURCE_BYTES',len(raw)-1),self.assertRaisesRegex(ValueError,'SOURCE_SIZE_LIMIT'):
            reader.recognize(self.source,1,[0,0,10,10],sha)
        with patch.object(reader,'MAX_PIXELS',10),self.assertRaisesRegex(ValueError,'PIXEL_LIMIT'):
            reader.recognize(self.source,1,[0,0,10,10],sha)
        with patch.object(reader,'MAX_OUTPUT_BYTES',10),self.assertRaisesRegex(ValueError,'OUTPUT_LIMIT'):
            reader.recognize(self.source,1,[0,0,10,10],sha)
        original=reader._render
        def change(*args,**kwargs):
            result=original(*args,**kwargs);self.source.write_bytes(b'changed');return result
        with patch.object(reader,'_render',side_effect=change),self.assertRaisesRegex(ValueError,'SOURCE_CHANGED'):
            reader.recognize(self.source,1,[0,0,10,10],sha)

    def test_conflict_comparison_budget_and_normalization_preserve_source_text(self):
        native=[dict(block_id='n',text='Ａ  42',provenance=[dict(bbox=dict(left=0,top=0,right=10,bottom=10))])]
        ocr=[dict(block_id='o',text='A 43',provenance=[dict(bbox=dict(left=0,top=0,right=10,bottom=10))])]
        conflicts=reader._conflicts(native,ocr,float('inf'))
        self.assertEqual(conflicts[0]['native_text'],'Ａ  42')
        self.assertEqual(conflicts[0]['ocr_text'],'A 43')
        self.assertFalse(conflicts[0]['acceptance_granted'])
        with patch.object(reader,'MAX_CONFLICT_PAIRS',0),self.assertRaisesRegex(ValueError,'CONFLICT_LIMIT'):
            reader._conflicts(native,ocr,float('inf'))

    def test_word_deadline_and_nonregular_source_bounds(self):
        with fitz.open() as doc:
            page=doc.new_page(width=100,height=100)
            page.insert_text((10,40),'ONE TWO',fontsize=10)
            raw,sha=self.save(doc)
        with patch.object(reader,'MAX_WORDS',1),self.assertRaisesRegex(ValueError,'WORD_LIMIT'):
            reader.recognize(self.source,1,[0,0,100,100],sha)
        with patch.object(reader,'TIMEOUT',0),self.assertRaisesRegex(ValueError,'TIMEOUT'):
            reader.recognize(self.source,1,[0,0,100,100],sha)
        if not hasattr(os,'mkfifo'):return
        fifo=self.source.with_name('fifo.pdf');os.mkfifo(fifo)
        with self.assertRaisesRegex(ValueError,'UNSAFE_SOURCE'):
            reader.recognize(fifo,1,[0,0,10,10],sha)

    def test_real_scanned_and_mixed_table_values_remain_candidates(self):
        if not (Path(TESSDATA)/'rus.traineddata').is_file():self.skipTest('Local rus OCR model unavailable')
        with patch.dict(os.environ,{'ENGINEER_OS_TESSDATA_DIR':TESSDATA}):
            for mixed in (False,True):
                with self.subTest(mixed=mixed):
                    self.source.unlink(missing_ok=True)
                    with fitz.open() as raster_doc:
                        page=raster_doc.new_page(width=300,height=160)
                        for position,text in (((35,55),'56320'),((160,55),'12345'),((35,115),'67890'),((160,115),'24680')):
                            page.insert_text(position,text,fontsize=18)
                        raster=page.get_pixmap(matrix=fitz.Matrix(3,3)).tobytes('png')
                    with fitz.open() as doc:
                        page=doc.new_page(width=300,height=160);page.insert_image(page.rect,stream=raster)
                        if mixed:page.insert_text((35,55),'99999',fontsize=18,render_mode=3)
                        raw,sha=self.save(doc)
                    bbox=[20,20,270,140]
                    result=reader.recognize(self.source,1,bbox,sha,ocr_enabled=True)
                    text=' '.join(block['text'] for block in result['ocr_blocks'])
                    for expected in ('56320','12345','67890','24680'):self.assertIn(expected,text)
                    self.assertEqual(result['source_bbox'],bbox)
                    self.assertEqual(self.source.read_bytes(),raw)
                    self.assertFalse(result['acceptance_granted'])
                    self.assertEqual(result['ocr_dossier']['coverage'],'SELECTED_REGION_EXECUTED')
                    input_raster=result['ocr_dossier']['regions'][0]['input_raster']
                    with fitz.open(stream=raw,filetype='pdf') as independent:
                        expected=independent[0].get_pixmap(matrix=fitz.Matrix(6,6),clip=fitz.Rect(bbox),colorspace=fitz.csRGB,alpha=False).tobytes('png')
                    self.assertEqual(input_raster['png_sha256'],hashlib.sha256(expected).hexdigest())
                    self.assertEqual(input_raster['pixel_origin'],[120,120])
                    self.assertEqual(input_raster['width'],1500)
                    self.assertEqual(input_raster['height'],720)
                    for block in result['ocr_blocks']:
                        box=block['provenance'][0]['bbox']
                        self.assertTrue(bbox[0]<=box['left']<box['right']<=bbox[2])
                        self.assertTrue(bbox[1]<=box['top']<box['bottom']<=bbox[3])
                    if mixed:
                        self.assertEqual(result['native_words'][0]['text'],'99999')
                        self.assertTrue(result['conflicts'])
                        self.assertIn('99999',result['conflicts'][0]['native_text'])
                        self.assertIn('56320',result['conflicts'][0]['ocr_text'])
                    else:self.assertEqual(result['native_words'],[])

    def test_sparse_label_profile_is_explicit_and_rejects_other_modes(self):
        if not (Path(TESSDATA)/'rus.traineddata').is_file():self.skipTest('Local rus OCR model unavailable')
        with fitz.open() as doc:
            p=doc.new_page(width=300,height=160);p.insert_text((35,55),'-0,450',fontsize=18);p.insert_text((200,120),'44',fontsize=18)
            raw,sha=self.save(doc)
        with patch.dict(os.environ,{'ENGINEER_OS_TESSDATA_DIR':TESSDATA}):
            result=reader.recognize(self.source,1,[20,20,270,140],sha,ocr_enabled=True,ocr_psm=11)
        self.assertIn('-0,450',' '.join(b['text'] for b in result['ocr_blocks']))
        self.assertEqual(result['ocr_dossier']['regions'][0]['psm'],11)
        with self.assertRaisesRegex(ValueError,'INVALID_OCR_PROFILE'):reader.recognize(self.source,1,[20,20,270,140],sha,ocr_psm=99)

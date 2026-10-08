import hashlib
import io
import tempfile
import unittest
from pathlib import Path
import fitz
from PIL import Image
from engineering.local_app.files import preserve_file,extract_preview
from engineering.local_app.store import Store
from engineering.local_app.worker import Worker


class DocumentIntakeCoverageTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.store=Store(Path(self.tmp.name));self.session=self.store.create_session()['id']

    def test_lir_original_is_preserved_without_claiming_decoding(self):
        data=b'<LIRA-SAPR 2023>\x00\x81binary'
        file=preserve_file(self.store,self.session,'scheme.lir',data)
        self.assertEqual(file['sha256'],hashlib.sha256(data).hexdigest())
        self.assertEqual(Path(self.store.get_file(file['id'])['path']).read_bytes(),data)
        self.assertEqual(file['extraction_status'],'UNAVAILABLE')
        self.assertIn('MODEL_DECODER_UNAVAILABLE',file['extraction_coverage']['stop_reasons'])

    def test_image_original_requires_ocr_and_exports_are_not_calculations(self):
        data=io.BytesIO();Image.new('RGB',(100,100),'white').save(data,format='PNG')
        file=preserve_file(self.store,self.session,'scan.png',data.getvalue())
        self.assertIn('OCR_REQUIRED',file['extraction_coverage']['stop_reasons'])
        export=preserve_file(self.store,self.session,'export.json',b'{"nodes":[1]}')
        self.assertIn('CALCULATION_SEMANTICS_NOT_CHECKED',export['extraction_coverage']['stop_reasons'])

    def test_encrypted_pdf_is_reported_explicitly_and_original_retained(self):
        with fitz.open() as doc:
            doc.new_page();data=doc.tobytes(encryption=fitz.PDF_ENCRYPT_AES_256,user_pw='secret')
        file=preserve_file(self.store,self.session,'encrypted.pdf',data)
        self.assertIn('ENCRYPTED_PDF',file['extraction_coverage']['stop_reasons'])
        self.assertEqual(file['size'],len(data))

    def test_mixed_native_page_has_boxes_and_unread_visual_components(self):
        image=io.BytesIO();Image.new('RGB',(20,20),'red').save(image,format='PNG')
        with fitz.open() as doc:
            page=doc.new_page();page.insert_text((40,40),'Source height 4m')
            page.insert_image(fitz.Rect(40,100,200,200),stream=image.getvalue())
            page.draw_rect(fitz.Rect(40,220,200,300));data=doc.tobytes()
        file=preserve_file(self.store,self.session,'mixed.pdf',data)
        job=self.store.enqueue_extraction(self.session,file['id'],'native');Worker(self.store,None).run_once()
        page=self.store.extraction_page(self.session,job['id'],1)
        self.assertIsNotNone(page['blocks'][0]['provenance'][0]['bbox'])
        self.assertIn('IMAGE_CONTENT_UNVERIFIED',page['limitations'])
        self.assertIn('VECTOR_CONTENT_UNVERIFIED',page['limitations'])
        self.assertEqual(page['status'],'BLOCK');self.assertFalse(page['acceptance_granted'])

    def test_corrupt_pdf_has_explicit_reason(self):
        self.assertIn('CORRUPT_PDF',extract_preview('broken.pdf',b'broken')[4]['stop_reasons'])

    def test_missing_pdf_reader_is_not_called_corrupt_source(self):
        from unittest.mock import patch
        with patch.dict('sys.modules',{'fitz':None}):
            coverage=extract_preview('source.pdf',b'unknown')[4]
        self.assertNotIn('CORRUPT_PDF',coverage['stop_reasons'])

    def test_export_quotes_have_text_location_without_calculation_acceptance(self):
        from engineering.local_app.evidence import register
        for name,data,quote in [('export.json',b'{"nodes": []}','"nodes"'),('export.csv',b'node,x\n1,4','1,4')]:
            file=preserve_file(self.store,self.session,name,data)
            record=register(self.store,self.session,file_id=file['id'],quote=quote,statement='Unverified')
            self.assertEqual(record['source_match'],'MATCH');self.assertIsNone(record['page']);self.assertFalse(record['acceptance_granted'])
            with self.assertRaises(ValueError):register(self.store,self.session,file_id=file['id'],page=1,quote=quote,statement='Unverified')

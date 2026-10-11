"""Sparse native labels must not hide dense graphic pages from requested OCR."""
import hashlib
import importlib.util
import inspect
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import fitz


class SparseVisualCoverageTests(unittest.TestCase):
    def load(self):
        path=Path(__file__).resolve().parents[1]/'scripts/local_pdf_visual_coverage.py'
        spec=importlib.util.spec_from_file_location('sparse_visual_audit',path)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        return module

    def source(self,root):
        document=fitz.open()
        page=document.new_page();page.insert_text((30,30),'Sheet 532')
        for i in range(120):page.draw_rect(fitz.Rect(30+i%10*20,50+i//10*20,40+i%10*20,60+i//10*20))
        page=document.new_page();page.insert_text((30,30),'A normal short title')
        page=document.new_page();page.draw_rect(fitz.Rect(30,30,150,150))
        path=root/'source.pdf';document.save(path);document.close();return path

    def test_existing_native_gap_mode_misses_sparse_graphic_page(self):
        module=self.load()
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);source=self.source(root)
            with patch('engineering.local_app.ocr.TesseractOCR',side_effect=ValueError('missing models')):
                result=module.audit(source,root/'audit',ocr_gaps=True)
            self.assertEqual(result['native_text_missing_pages'],[3])
            self.assertEqual(result['ocr_selected_pages'],[3])
            self.assertGreater(result['pages'][0]['native_chars'],0)
            self.assertEqual(result['pages'][0]['ocr_status'],'NOT_RUN')

    def test_graphic_gap_mode_routes_sparse_and_empty_pages_with_source_evidence(self):
        module=self.load()
        self.assertIn('ocr_graphic_gaps',inspect.signature(module.audit).parameters,
                      'Explicit graphic-gap OCR routing is missing')
        class Reader:
            last_page_dossier={'quality_verified':False,'acceptance_granted':False}
            def page_blocks(self,page,number):
                return [{'text':'unverified candidate','ocr_confidence':50}]
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);source=self.source(root);before=source.read_bytes()
            with patch('engineering.local_app.ocr.TesseractOCR',Reader):
                result=module.audit(source,root/'audit',ocr_graphic_gaps=True)
            self.assertEqual(result['ocr_selected_pages'],[1,3])
            self.assertEqual(result['graphic_text_gap_candidate_pages'],[1])
            self.assertEqual(result['pages'][0]['drawing_count'],120)
            self.assertEqual(result['pages'][0]['ocr_selection_reasons'],['SPARSE_NATIVE_DENSE_DRAWINGS_CANDIDATE'])
            self.assertFalse(result['pages'][0]['graphic_text_gap_verified'])
            self.assertEqual(result['pages'][0]['ocr_status'],'CANDIDATES_RECORDED')
            self.assertEqual(result['pages'][1]['ocr_status'],'NOT_RUN')
            self.assertEqual(result['pages'][2]['ocr_status'],'CANDIDATES_RECORDED')
            detail=json.loads((root/'audit'/result['pages'][0]['ocr_file']).read_text())
            self.assertEqual(detail['source_sha256'],hashlib.sha256(before).hexdigest())
            self.assertEqual(detail['render_sha256'],result['pages'][0]['render_sha256'])
            self.assertFalse(detail['acceptance_granted'])
            self.assertEqual(source.read_bytes(),before)

    def test_missing_models_expose_selected_sparse_page_as_unavailable(self):
        module=self.load()
        self.assertIn('ocr_graphic_gaps',inspect.signature(module.audit).parameters,
                      'Explicit graphic-gap OCR routing is missing')
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);source=self.source(root)
            with patch('engineering.local_app.ocr.TesseractOCR',side_effect=ValueError('missing models')):
                result=module.audit(source,root/'audit',ocr_graphic_gaps=True)
            self.assertEqual(result['ocr_selected_pages'],[1,3])
            self.assertEqual(result['pages'][0]['ocr_status'],'UNAVAILABLE')
            self.assertTrue(result['render_cycle_complete'])
            self.assertFalse(result['content_completeness_verified'])
            self.assertIn('OCR_ENGINE_OR_LANGUAGE_MODELS_UNAVAILABLE',result['errors'])

    def test_expected_hash_rejects_wrong_source_before_output_creation(self):
        module=self.load()
        self.assertIn('expected_sha256',inspect.signature(module.audit).parameters)
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);source=self.source(root);before=source.read_bytes()
            with patch('fitz.open',side_effect=AssertionError('PDF opened before hash gate')), \
                    patch('engineering.local_app.ocr.TesseractOCR',side_effect=AssertionError('OCR started before hash gate')), \
                    self.assertRaisesRegex(ValueError,'SOURCE_SHA256_MISMATCH'):
                module.audit(source,root/'audit',expected_sha256='0'*64,ocr_graphic_gaps=True)
            self.assertFalse((root/'audit').exists())
            self.assertEqual(source.read_bytes(),before)

    def test_expected_hash_rejects_invalid_format_before_output_creation(self):
        module=self.load()
        self.assertIn('expected_sha256',inspect.signature(module.audit).parameters)
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);source=self.source(root)
            for invalid in ['not-a-hash','g'*64,123]:
                with self.subTest(invalid=invalid),self.assertRaisesRegex(ValueError,'INVALID_EXPECTED_SHA256'):
                    module.audit(source,root/'audit',expected_sha256=invalid)
                self.assertFalse((root/'audit').exists())

    def test_expected_hash_accepts_matching_source_and_records_preflight(self):
        module=self.load()
        self.assertIn('expected_sha256',inspect.signature(module.audit).parameters)
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);source=self.source(root);expected=hashlib.sha256(source.read_bytes()).hexdigest()
            result=module.audit(source,root/'audit',expected_sha256=expected)
            self.assertTrue(result['render_cycle_complete'])
            self.assertEqual(result['expected_source_sha256'],expected)
            self.assertTrue(result['expected_source_sha256_verified'])

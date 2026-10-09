"""A complete render inventory must expose text gaps without certifying content."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import fitz


class VisualAuditTests(unittest.TestCase):
    def load(self):
        path=Path(__file__).resolve().parents[1]/'scripts/local_pdf_visual_coverage.py'
        self.assertTrue(path.is_file(),'Full-document source-bound render audit is missing')
        spec=importlib.util.spec_from_file_location('visual_audit',path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        return module

    def source(self,root):
        d=fitz.open();d.new_page().insert_text((30,40),'Native source 123');p=d.new_page();p.draw_rect(fitz.Rect(30,30,150,150));source=root/'source.pdf';d.save(source);d.close();return source

    def test_all_pages_render_and_empty_text_page_stays_an_explicit_gap(self):
        module=self.load()
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);source=self.source(root);before=source.read_bytes();result=module.audit(source,root/'audit')
            self.assertTrue(result['render_cycle_complete']);self.assertEqual(result['page_count'],2)
            self.assertEqual(result['native_text_missing_pages'],[2])
            self.assertFalse(result['content_completeness_verified']);self.assertFalse(result['acceptance_granted'])
            self.assertEqual(result['source_sha256'],hashlib.sha256(before).hexdigest())
            for page in result['pages']:
                png=(root/'audit'/page['render_file']).read_bytes()
                self.assertEqual(hashlib.sha256(png).hexdigest(),page['render_sha256'])
                self.assertLessEqual(max(page['render_size']),1200)
            self.assertEqual(source.read_bytes(),before)
            self.assertEqual(json.loads((root/'audit/manifest.json').read_text())['source_sha256'],result['source_sha256'])

    def test_original_cannot_be_selected_as_output_directory(self):
        module=self.load()
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);source=self.source(root);before=source.read_bytes()
            with self.assertRaises(ValueError):module.audit(source,source)
            self.assertEqual(source.read_bytes(),before)

    def test_source_disappearance_keeps_final_completed_page_journal_and_explicit_identity_failure(self):
        module=self.load()
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);source=self.source(root);original=fitz.Page.get_text
            def disappear(page,*args,**kwargs):
                text=original(page,*args,**kwargs)
                if source.exists():source.unlink()
                return text
            with patch.object(fitz.Page,'get_text',disappear):result=module.audit(source,root/'audit')
            self.assertFalse(result['render_cycle_complete'])
            self.assertIn('SOURCE_IDENTITY_UNAVAILABLE',result['errors'])
            self.assertEqual(len(result['pages']),2)
            saved=json.loads((root/'audit/manifest.json').read_text())
            self.assertEqual(saved['pages'],result['pages'])

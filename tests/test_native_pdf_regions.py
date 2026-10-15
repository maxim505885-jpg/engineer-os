import copy
import hashlib
import importlib
import importlib.util
import tempfile
import subprocess
import sys
import unittest
from pathlib import Path


@unittest.skipUnless(importlib.util.find_spec('fitz'), 'PyMuPDF unavailable')
class NativePdfRegionTests(unittest.TestCase):
    def test_cli_failure_replaces_stale_candidates(self):
        script=Path(__file__).resolve().parents[1]/'scripts/recover_native_pdf_regions.py'
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            manifest=root/'map.json';manifest.write_text('invalid json')
            output=root/'result.json';output.write_text('{"status":"UNCERTAINTY","blocks":[{"text":"stale"}]}')
            run=subprocess.run([sys.executable,str(script),str(root/'missing.pdf'),str(manifest),
                '--project-id','p','--document-id','d','--output',str(output)],capture_output=True,text=True)
            self.assertEqual(run.returncode,2,run.stderr)
            import json
            result=json.loads(output.read_text())
            self.assertEqual(result['status'],'BLOCK')
            self.assertEqual(result['blocks'],[])
            self.assertFalse(result['acceptance_granted'])

    def test_original_grid_recovery_needs_no_neural_table_export(self):
        self.assertIsNotNone(importlib.util.find_spec('scripts.recover_native_pdf_regions'),
                             'native vector grids need an independent checked recovery route')
        module = importlib.import_module('scripts.recover_native_pdf_regions')
        import fitz
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory)/'source.pdf'
            with fitz.open() as pdf:
                page = pdf.new_page(width=100, height=100)
                page.draw_rect(fitz.Rect(10,20,90,60),width=.2)
                page.draw_line((10,40),(90,40),width=.2)
                page.draw_line((50,40),(50,60),width=.2)
                page.insert_text((12,35), 'Merged heading', fontsize=5)
                page.insert_text((52,55), '123.45', fontsize=5)
                pdf.save(source)
            sha = hashlib.sha256(source.read_bytes()).hexdigest()
            def fragment(bbox,text):
                return dict(source_sha256=sha,source_page=1,coordinate_origin='TOPLEFT',bbox=bbox,text=text)
            manifest = dict(schema_version=2,source_sha256=sha,status='UNCERTAINTY',
                evidentiary_status='NOT_EVIDENCE',acceptance_granted=False,
                review=dict(reviewer='automated native grid check',reviewed_at='2026-10-04T00:00:00Z',scope='selected physical region'),
                context_fragments=[fragment([10,20,90,60],'Merged heading 123.45')],
                tables=[dict(table_id='native',source_page=1,source_detection_clip=[0,0,100,100],
                    x_boundaries=[10,50,90],y_boundaries=[20,40,60],cells=[
                        dict(cell_id='heading',row_start=0,row_end=1,col_start=0,col_end=2,source_fragment=fragment([10,20,90,40],'Merged heading')),
                        dict(cell_id='blank',row_start=1,row_end=2,col_start=0,col_end=1,source_fragment=fragment([10,40,50,60],'')),
                        dict(cell_id='value',row_start=1,row_end=2,col_start=1,col_end=2,source_fragment=fragment([50,40,90,60],'123.45'))])])
            result = module.recover_native_regions(source,manifest,project_id='p',document_id='d')
            self.assertEqual(result['status'],'UNCERTAINTY')
            self.assertEqual(result['source_binding_audit']['verified_cells'],3)
            self.assertEqual(result['blocks'][-1]['text'],'123.45')
            self.assertEqual(result['blocks'][1]['grid_span']['col_end'],2)
            self.assertFalse(result['acceptance_granted'])
            self.assertFalse(result['complete_page'])
            self.assertEqual(result['document_status'],'BLOCK')
            invalid = copy.deepcopy(manifest)
            invalid['tables'][0]['cells'][0]['source_fragment']['text']='invented'
            self.assertEqual(module.recover_native_regions(source,invalid,project_id='p',document_id='d')['status'],'BLOCK')
            # Text-free cells with visible vector ink must not become blanks.
            ink = Path(directory)/'ink.pdf'
            with fitz.open(source) as pdf:
                pdf[0].draw_line((20,45),(30,55),width=.4)
                pdf.save(ink)
            changed = copy.deepcopy(manifest)
            ink_sha = hashlib.sha256(ink.read_bytes()).hexdigest()
            changed['source_sha256']=ink_sha
            for f in changed['context_fragments']: f['source_sha256']=ink_sha
            for c in changed['tables'][0]['cells']: c['source_fragment']['source_sha256']=ink_sha
            rejected = module.recover_native_regions(ink,changed,project_id='p',document_id='d')
            self.assertEqual(rejected['status'],'BLOCK')
            self.assertEqual(rejected['blocks'],[])
            self.assertIn('visible ink',rejected['reason'])

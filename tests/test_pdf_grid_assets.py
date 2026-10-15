import hashlib
import importlib
import importlib.util
import json
import tempfile
import subprocess
import sys
import unittest
from pathlib import Path


@unittest.skipUnless(importlib.util.find_spec('fitz'), 'PyMuPDF unavailable')
class PdfGridAssetsTests(unittest.TestCase):
    def test_image_cell_is_preserved_as_uninterpreted_source_asset(self):
        self.assertIsNotNone(importlib.util.find_spec('scripts.capture_pdf_grid_assets'),
                             'mixed tables need source visual assets rather than empty text cells')
        module=importlib.import_module('scripts.capture_pdf_grid_assets')
        import fitz
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);source=root/'source.pdf'
            image=fitz.Pixmap(fitz.csRGB,fitz.IRect(0,0,20,20),False)
            image.clear_with(40)
            with fitz.open() as pdf:
                p=pdf.new_page(width=100,height=100)
                p.draw_rect(fitz.Rect(10,20,90,60),width=.2)
                p.draw_line((50,20),(50,60),width=.2)
                p.insert_text((12,35),'Photo',fontsize=5)
                p.insert_image(fitz.Rect(55,25,85,55),stream=image.tobytes('png'))
                pdf.save(source)
            sha=hashlib.sha256(source.read_bytes()).hexdigest()
            def fragment(box,text):return dict(source_sha256=sha,source_page=1,coordinate_origin='TOPLEFT',bbox=box,text=text)
            manifest=dict(schema_version=2,source_sha256=sha,status='UNCERTAINTY',evidentiary_status='NOT_EVIDENCE',acceptance_granted=False,
                review=dict(reviewer='automated source capture',reviewed_at='2026-10-04T00:00:00Z',scope='physical region only'),
                context_fragments=[fragment([10,20,90,60],'Photo')],tables=[dict(table_id='photo',source_page=1,
                    source_detection_clip=[0,0,100,100],x_boundaries=[10,50,90],y_boundaries=[20,60],cells=[
                    dict(cell_id='label',row_start=0,row_end=1,col_start=0,col_end=1,source_fragment=fragment([10,20,50,60],'Photo')),
                    dict(cell_id='image',row_start=0,row_end=1,col_start=1,col_end=2,source_fragment=fragment([50,20,90,60],''))])])
            result=module.capture_grid_assets(source,manifest,root/'assets',project_id='p',document_id='d')
            self.assertEqual(result['status'],'UNCERTAINTY')
            self.assertEqual(result['visual_asset_count'],2)
            cell=result['tables'][0]['cells'][1]
            self.assertEqual(cell['source_fragment']['text'],'')
            self.assertTrue(cell['visual_asset']['contains_source_image'])
            self.assertEqual(cell['visual_asset']['interpretation_status'],'UNCERTAINTY')
            asset=root/'assets'/cell['visual_asset']['path']
            self.assertEqual(hashlib.sha256(asset.read_bytes()).hexdigest(),cell['visual_asset']['sha256'])
            self.assertEqual(cell['visual_asset']['source_sha256'],sha)
            self.assertEqual(cell['visual_asset']['source_page'],1)
            self.assertEqual(cell['visual_asset']['bbox'],[50,20,90,60])
            self.assertFalse(result['complete_page'])
            self.assertFalse(result['acceptance_granted'])
            self.assertEqual(result['document_status'],'BLOCK')
            self.assertEqual(result['evidentiary_status'],'NOT_EVIDENCE')
            self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),sha)
            # Existing pure-native route must still reject these image cells.
            from scripts.recover_native_pdf_regions import recover_native_regions
            self.assertEqual(recover_native_regions(source,manifest,project_id='p',document_id='d')['status'],'BLOCK')
            collision=root/'collision';collision.mkdir()
            input_manifest=collision/'table-00000-cell-00000.png'
            original_manifest=json.dumps(manifest).encode()
            input_manifest.write_bytes(original_manifest)
            run=subprocess.run([sys.executable,str(Path(module.__file__)),str(source),str(input_manifest),
                '--project-id','p','--document-id','d','--output-dir',str(collision)],capture_output=True,text=True)
            self.assertEqual(run.returncode,2,run.stderr)
            self.assertEqual(input_manifest.read_bytes(),original_manifest)
            # Break caught: recovery must retain actual image cell pixels,
            # never export a native-empty image as a verified blank cell.
            from scripts.recover_docling_export import recover_export, table_digest
            target=dict(prov=[dict(page_no=1,bbox=dict(l=10,t=20,r=90,b=80,coord_origin='TOPLEFT'))],
                        data=dict(num_rows=3,num_cols=2,table_cells=[]))
            grid=manifest['tables'][0]
            grid.update(docling_table_index=0,docling_table_sha256=table_digest(target),replacement_mode='SOURCE_MIXED_GRID_CONTEXT')
            mapped=recover_export(source,dict(tables=[target]),manifest,project_id='p',document_id='d')
            self.assertEqual(mapped['status'],'UNCERTAINTY',mapped.get('reason'))
            cells=[b for b in mapped['blocks'] if b['kind']=='table_cell']
            self.assertEqual(len(cells),2)
            visual=cells[1]['visual_asset']
            import base64
            payload=base64.b64decode(visual['png_base64'],validate=True)
            self.assertEqual(hashlib.sha256(payload).hexdigest(),visual['sha256'])
            self.assertTrue(visual['contains_source_image'])
            self.assertFalse(visual['native_empty_is_visual_blank'])
            self.assertEqual(cells[1]['content_interpretation_status'],'UNCERTAINTY')
            self.assertFalse(mapped['acceptance_granted'])
            self.assertFalse(mapped['complete_page'])
            self.assertEqual(mapped['document_status'],'BLOCK')
            grid['replacement_mode']='SOURCE_VECTOR_CONTEXT'
            self.assertEqual(recover_export(source,dict(tables=[target]),manifest,project_id='p',document_id='d')['status'],'BLOCK')
            grid['replacement_mode']='SOURCE_MIXED_GRID_CONTEXT'
            grid['source_detection_clip']=[0,0,9,9]
            rejected=recover_export(source,dict(tables=[target]),manifest,project_id='p',document_id='d')
            self.assertEqual(rejected['status'],'BLOCK')
            self.assertEqual(rejected['blocks'],[])
            grid['source_detection_clip']=[0,0,100,100]
            manifest['tables'][0]['cells'][1]['source_fragment']['text']='invented measurement'
            invalid=module.capture_grid_assets(source,manifest,root/'invalid',project_id='p',document_id='d')
            self.assertEqual(invalid['status'],'BLOCK')
            self.assertEqual(invalid['blocks'],[])

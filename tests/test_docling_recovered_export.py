import copy
import hashlib
import importlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class RecoveredExportTests(unittest.TestCase):
    def test_cli_launches_and_invalid_input_replaces_stale_success(self):
        script=Path(__file__).resolve().parents[1]/'scripts/recover_docling_export.py'
        help_result=subprocess.run([sys.executable,str(script),'--help'],capture_output=True,text=True)
        self.assertEqual(help_result.returncode,0,help_result.stderr)
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);source=root/'source.pdf';raw=root/'raw.json';manifest=root/'map.json';out=root/'result.json'
            source.write_bytes(b'not a pdf');raw.write_text('{}');manifest.write_text('invalid json')
            out.write_text('{"status":"UNCERTAINTY","blocks":[{"text":"stale"}]}')
            completed=subprocess.run([sys.executable,str(script),str(source),str(raw),str(manifest),'--project-id','p','--document-id','d','--output',str(out)],capture_output=True,text=True)
            self.assertEqual(completed.returncode,2,completed.stderr)
            result=json.loads(out.read_text())
            self.assertEqual(result['status'],'BLOCK')
            self.assertEqual(result['blocks'],[])
            manifest.write_text('{}');source.unlink()
            out.write_text('{"status":"UNCERTAINTY","blocks":[{"text":"stale"}]}')
            completed=subprocess.run([sys.executable,str(script),str(source),str(raw),str(manifest),'--project-id','p','--document-id','d','--output',str(out)],capture_output=True,text=True)
            self.assertEqual(completed.returncode,2,completed.stderr)
            self.assertEqual(json.loads(out.read_text())['blocks'],[])

    @unittest.skipUnless(importlib.util.find_spec('fitz'),'optional PyMuPDF source verifier unavailable')
    def test_real_source_merged_grid_replaces_only_its_target(self):
        # Catches a fallback that trusts an old audit, loses spans, or replaces
        # every failed table using one reviewed region.
        try:
            module = importlib.import_module('scripts.recover_docling_export')
        except ModuleNotFoundError:
            module = None
        self.assertIsNotNone(module, 'source-checked recovery is not integrated into normalization')
        import fitz
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory)/'source.pdf'
            pdf=fitz.open();p=pdf.new_page(width=100,height=100)
            p.draw_rect(fitz.Rect(0,10,30,30),width=.2)
            p.draw_line((0,20),(30,20),width=.2)
            for x in (10,20):p.draw_line((x,20),(x,30),width=.2)
            p.insert_text((5,8),'Context',fontsize=5)
            p.insert_text((2,18),'Header',fontsize=5)
            p.insert_text((12,28),'Value',fontsize=3)
            pdf.save(source);pdf.close()
            sha=hashlib.sha256(source.read_bytes()).hexdigest()
            def f(box,text):
                return dict(source_sha256=sha,source_page=1,coordinate_origin='TOPLEFT',bbox=box,text=text)
            cells=[dict(cell_id='h',row_start=0,row_end=1,col_start=0,col_end=3,source_fragment=f([0,10,30,20],'Header')),
                   *[dict(cell_id=str(i),row_start=1,row_end=2,col_start=i,col_end=i+1,source_fragment=f([i*10,20,(i+1)*10,30],'Value' if i==1 else '')) for i in range(3)]]
            table=dict(prov=[dict(page_no=1,bbox=dict(l=0,t=10,r=30,b=30,coord_origin='TOPLEFT'))],data=dict(num_rows=2,num_cols=3,table_cells=[dict(start_row_offset_idx=c['row_start'],end_row_offset_idx=c['row_end'],start_col_offset_idx=c['col_start'],end_col_offset_idx=c['col_end'],text=c['source_fragment']['text'],column_header=c['row_start']==0) for c in cells]))
            raw=dict(texts=[],tables=[table])
            grid=dict(table_id='source-table',source_page=1,x_boundaries=[0,10,20,30],y_boundaries=[10,20,30],cells=cells,docling_table_index=0,docling_table_sha256=hashlib.sha256(json.dumps(table,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest())
            manifest=dict(schema_version=2,source_sha256=sha,status='UNCERTAINTY',evidentiary_status='NOT_EVIDENCE',acceptance_granted=False,review=dict(reviewer='test',reviewed_at='2026-10-04T17:00:00Z',scope='Source grid'),context_fragments=[f([0,0,40,10],'Context')],tables=[grid])
            result=module.recover_export(source,raw,manifest,project_id='p',document_id='d')
            self.assertEqual(result['status'],'UNCERTAINTY')
            self.assertEqual(result['table_recovery']['resolved_table_indices'],[0])
            self.assertEqual(len([b for b in result['blocks'] if b['kind']=='table_cell']),4)
            self.assertFalse(result['complete_document'])
            self.assertFalse(result['acceptance_granted'])
            self.assertEqual(result['document_status'],'BLOCK')
            for mutation in ['changed_source','changed_raw','missing_target','unmapped_table','invalid_page','numeric_cell','scalar_target','unmapped_row_page']:
                with self.subTest(mutation=mutation):
                    m=copy.deepcopy(manifest);r=copy.deepcopy(raw)
                    if mutation=='changed_source':m['tables'][0]['cells'][0]['source_fragment']['text']='Wrong'
                    if mutation=='changed_raw':r['tables'][0]['data']['table_cells'][0]['text']='Wrong'
                    if mutation=='missing_target':m['tables'][0].pop('docling_table_sha256')
                    if mutation=='unmapped_table':r['tables'].append(copy.deepcopy(table))
                    if mutation=='invalid_page':r['texts']=[dict(text='Foreign',label='text',prov=[dict(page_no=999,bbox=dict(l=1,t=1,r=10,b=10,coord_origin='TOPLEFT'))])]
                    if mutation=='numeric_cell':r['tables'].append(dict(prov=table['prov'],data=dict(num_rows=3,num_cols=7,table_cells=[dict(text=123)])))
                    if mutation=='scalar_target':r['tables'][0]=42
                    if mutation=='unmapped_row_page':r['tables'].append(dict(prov=[dict(page_no=999)],data=dict(num_rows=2,num_cols=2,table_cells=[dict(start_row_offset_idx=i,end_row_offset_idx=i+1,start_col_offset_idx=j,end_col_offset_idx=j+1,text=[['A','B'],['1','2']][i][j],column_header=i==0) for i in range(2) for j in range(2)])))
                    failed=module.recover_export(source,r,m,project_id='p',document_id='d')
                    self.assertEqual(failed['status'],'BLOCK')
                    self.assertFalse(failed['acceptance_granted'])
                    self.assertFalse(failed['complete_document'])
            repaired_raw=copy.deepcopy(raw)
            repaired_raw['tables'][0]['data']['table_cells'][0]['text']='OCRWrong'
            corrected=copy.deepcopy(manifest)
            corrected['tables'][0].update(replacement_mode='SOURCE_VECTOR_GRID',source_detection_clip=[0,10,30,30],docling_table_sha256=hashlib.sha256(json.dumps(repaired_raw['tables'][0],sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest())
            corrected_result=module.recover_export(source,repaired_raw,corrected,project_id='p',document_id='d')
            self.assertEqual(corrected_result['status'],'UNCERTAINTY',corrected_result.get('reason'))
            self.assertTrue(any(b['kind']=='table_cell' and b['text']=='Header' for b in corrected_result['blocks']))
            self.assertFalse(corrected_result['complete_document'])
            oversized_raw=copy.deepcopy(repaired_raw)
            oversized_raw['tables'][0]['prov'][0]['bbox']['l']=10**400
            oversized_manifest=copy.deepcopy(corrected)
            oversized_manifest['tables'][0]['docling_table_sha256']=hashlib.sha256(json.dumps(oversized_raw['tables'][0],sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
            oversized_result=module.recover_export(source,oversized_raw,oversized_manifest,project_id='p',document_id='d')
            self.assertEqual(oversized_result['status'],'BLOCK')
            self.assertEqual(oversized_result['blocks'],[])
            invalid_clip=copy.deepcopy(corrected)
            invalid_clip['tables'][0]['source_detection_clip']=[0,11,29,29]
            self.assertEqual(module.recover_export(source,repaired_raw,invalid_clip,project_id='p',document_id='d')['status'],'BLOCK')
            ink_source=Path(directory)/'ink.pdf'
            with fitz.open(source) as ink_pdf:
                ink_pdf[0].draw_line((2,23),(7,28),width=.3)
                ink_pdf.save(ink_source)
            ink_manifest=copy.deepcopy(corrected)
            ink_sha=hashlib.sha256(ink_source.read_bytes()).hexdigest()
            ink_manifest['source_sha256']=ink_sha
            for fragment in ink_manifest['context_fragments']:
                fragment['source_sha256']=ink_sha
            for cell in ink_manifest['tables'][0]['cells']:
                cell['source_fragment']['source_sha256']=ink_sha
            ink_result=module.recover_export(ink_source,repaired_raw,ink_manifest,project_id='p',document_id='d')
            self.assertEqual(ink_result['status'],'BLOCK')
            self.assertIn('visible ink',ink_result['reason'])

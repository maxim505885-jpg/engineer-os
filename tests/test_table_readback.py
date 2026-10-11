"""Offline table contracts; optional genuine backend probe is explicitly gated."""
import hashlib
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import fitz
from engineering.local_app import table_readback as reader
from engineering.local_app import table_worker as worker


def synthetic():
    document=fitz.open(); page=document.new_page(width=400,height=300)
    for x in (40,140,240,340): page.draw_line((x,40),(x,240),color=(0,0,0),width=1)
    for y in (40,90,140,190,240): page.draw_line((40,y),(340,y),color=(0,0,0),width=1)
    for row in range(4):
        for column in range(3):
            page.insert_text((55+column*100,70+row*50),f'{row+1}-{column+1}',fontsize=14)
    raw=document.tobytes(); document.close(); return raw


def ruled_table(merged=False):
    document=fitz.open(); page=document.new_page(width=600,height=500)
    for x in (40,200,360,520):
        page.draw_line((x,120 if merged and x==200 else 40),(x,360),color=(0,0,0),width=1)
    for y in (40,120,200,280,360): page.draw_line((40,y),(520,y),color=(0,0,0),width=1)
    for row in range(4):
        for column in range(3):
            if merged and row==0 and column==1: continue
            value=['Number','Length','Width'][column] if row==0 else str((row+1)*100+column*10)
            page.insert_text((55+column*160,85+row*80),value,fontsize=16)
    raw=document.tobytes(); document.close(); return raw


class TableReadbackTests(unittest.TestCase):
    def test_unconfigured_is_unavailable(self):
        with patch.dict(os.environ,{},clear=True):
            result=reader.read_tables(synthetic(),1,[30,30,350,250],'img2table')
        self.assertEqual(result['status'],'UNAVAILABLE')
        self.assertFalse(result['acceptance_granted'])

    def test_invalid_arguments(self):
        for page,bbox,backend in [(True,[0,0,1,1],'img2table'),(1,[0,0,float('nan'),1],'img2table'),
                                  (1,[0,0,1,1],'cloud')]:
            with self.assertRaises(ValueError): reader.read_tables(synthetic(),page,bbox,backend)

    def test_exact_clip_geometry_and_candidate_status(self):
        raw=synthetic()
        fake=[dict(bbox=[40,40,240,240],confidence=None,cells=[dict(text='candidate',bbox=[40,40,240,140],
            row=0,column=0,row_span=1,column_span=2,confidence=None,span_basis='REPEATED_CELL_GEOMETRY')])]
        with tempfile.TemporaryDirectory() as tmp:
            source=Path(tmp)/'source.pdf'; source.write_bytes(raw)
            with patch.object(worker,'img_tables',return_value=(fake,None)), patch.object(worker.importlib.metadata,'version',return_value='1.4.2'):
                result=worker.execute(dict(source=str(source),source_sha256=hashlib.sha256(raw).hexdigest(),
                                          page=1,bbox=[30,30,350,250],backend='img2table'))
        self.assertEqual(result['source_sha256'],hashlib.sha256(raw).hexdigest())
        self.assertEqual(result['source_bbox'],[30,30,350,250])
        self.assertEqual(result['raster']['width'],1280)
        cell=result['tables'][0]['cells'][0]
        self.assertEqual(cell['source_bbox'],[40,40,90,65])
        self.assertEqual(cell['column_span'],2)
        self.assertIsNone(cell['confidence'])
        self.assertFalse(result['acceptance_granted'])

    def test_geometry_never_expands_selection(self):
        mapped=worker.geometry([0,0,10,10],dict(width=11,height=11,scale=4,pixel_origin=[1,1]),[.3,.3,2.5,2.5])
        self.assertEqual(mapped['source_bbox'],[.3,.3,2.5,2.5])
        self.assertTrue(mapped['selection_boundary_clipped'])
        with self.assertRaisesRegex(ValueError,'OUTSIDE_RASTER'):
            worker.geometry([0,0,12,10],dict(width=11,height=11,scale=4,pixel_origin=[0,0]),[0,0,3,3])

    def test_raster_rounding_cannot_create_inverted_source_geometry(self):
        with self.assertRaisesRegex(ValueError,'OUTSIDE_SELECTION'):
            worker.geometry([.8,.8,1,1],dict(width=1,height=1,pixel_origin=[1,1],scale=4),[.3,.3,.31,.31])

    def test_invalid_region_is_rejected_when_backend_absent(self):
        with patch.dict(os.environ,{},clear=True):
            result=reader.read_tables(synthetic(),1,[0,0,401,301],'img2table')
        self.assertEqual(result['status'],'ERROR')
        self.assertEqual(result['reason'],'INVALID_REGION')

    def test_paddle_models_absent(self):
        with patch.dict(os.environ,{},clear=True):
            self.assertEqual(worker.paddle_tables(b'', 'eng'),(None,'PADDLE_LOCAL_MODELS_NOT_CONFIGURED'))


    @unittest.skipIf(os.name=='nt','executable fixture uses POSIX shebang')
    def test_parent_enforces_timeout_and_noisy_worker_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            python=Path(tmp)/'fake-python'
            for body,expected in [("import time; time.sleep(10)", 'TABLE_TIMEOUT'),
                                  ("import sys; sys.stderr.buffer.write(b'x'*(4*1024*1024+1))", 'TABLE_OUTPUT_LIMIT')]:
                python.write_text('#!'+sys.executable+'\n'+body+'\n');python.chmod(0o700)
                with patch.dict(os.environ,{'ENGINEER_OS_TABLE_PYTHON':str(python)}), patch.object(reader,'TIMEOUT',.3):
                    with self.assertRaisesRegex(ValueError,expected):
                        reader.read_tables(synthetic(),1,[30,30,350,250],'img2table')

    @unittest.skipUnless(sys.platform=='linux','Linux seccomp only')
    def test_network_sandbox_denies_socket(self):
        import subprocess,sys
        process=subprocess.run([sys.executable,'-c',
            'from engineering.local_app.doc_sandbox import apply; apply(); import socket; socket.socket()'],capture_output=True)
        self.assertNotEqual(process.returncode,0)
        self.assertIn(b'Operation not permitted',process.stderr)

    @unittest.skipUnless(os.environ.get('ENGINEER_OS_TABLE_PYTHON'),'optional table environment not configured')
    def test_genuine_img2table_tesseract(self):
        result=reader.read_tables(ruled_table(),1,[30,30,530,370],'img2table')
        self.assertEqual(result['status'],'UNCERTAINTY',result)
        self.assertEqual(result['backend_version'],'1.4.2')
        self.assertEqual(result['table_count'],1)
        self.assertEqual(len(result['tables'][0]['cells']),12)
        texts=[cell['text'] for cell in result['tables'][0]['cells']]
        self.assertIn('Number',texts)
        self.assertFalse(result['acceptance_granted'])

    @unittest.skipUnless(os.environ.get('ENGINEER_OS_TABLE_PYTHON'),'optional table environment not configured')
    def test_genuine_merged_cell(self):
        result=reader.read_tables(ruled_table(merged=True),1,[30,30,530,370],'img2table')
        self.assertEqual(result['status'],'UNCERTAINTY',result)
        cells=result['tables'][0]['cells']
        self.assertEqual(len(cells),11)
        self.assertTrue(any(c['column_span']==2 and c['text']=='Number' for c in cells))

    @unittest.skipUnless(os.environ.get('ENGINEER_OS_TABLE_PYTHON'),'optional table environment not configured')
    def test_custom_tessdata_without_hocr_config_still_reads_exact_png(self):
        import re, shutil, subprocess
        langs=subprocess.run(['tesseract','--list-langs'],capture_output=True,text=True,check=True)
        directory=re.search(r'in "([^"]+)"',langs.stdout).group(1)
        with tempfile.TemporaryDirectory() as temp:
            shutil.copy(Path(directory)/'eng.traineddata',temp)
            with patch.dict(os.environ,{'TESSDATA_PREFIX':temp}):
                result=reader.read_tables(ruled_table(),1,[30,30,530,370],'img2table')
        self.assertEqual(result['status'],'UNCERTAINTY',result)
        self.assertEqual(result['table_count'],1,result)
        self.assertIn('Number',[c['text'] for c in result['tables'][0]['cells']])
        self.assertEqual(result['tables'][0]['ocr_input_png_sha256'],result['raster']['png_sha256'])

    @unittest.skipUnless(os.environ.get('ENGINEER_OS_TABLE_PYTHON'),'optional table environment not configured')
    @unittest.skipIf(os.name=='nt','controlled OCR executable uses POSIX shebang')
    def test_empty_ocr_preserves_detected_table_geometry(self):
        # A text-free image may not be detected upstream (character-height
        # estimation). Use a real detectable grid and an empty OCR response.
        with tempfile.TemporaryDirectory() as temp:
            binary=Path(temp)/'tesseract'
            binary.write_text('#!'+sys.executable+'\nimport sys\n'
                'if "--list-langs" in sys.argv: print("eng")\n'
                'elif "--version" in sys.argv: print("controlled empty OCR")\n'
                'else:\n'
                ' if "stdin" in sys.argv: sys.stdin.buffer.read()\n'
                ' print("<html><body></body></html>")\n')
            binary.chmod(0o700)
            with patch.dict(os.environ,{'PATH':temp+os.pathsep+os.environ.get('PATH','')}):
                result=reader.read_tables(ruled_table(),1,[30,30,530,370],'img2table')
        self.assertEqual(result['table_count'],1,result)
        self.assertEqual(len(result['tables'][0]['cells']),12)
        self.assertEqual(result['tables'][0]['ocr_status'],'TEXT_UNAVAILABLE')
        self.assertTrue(all(c['text'] is None for c in result['tables'][0]['cells']))
        self.assertFalse(result['acceptance_granted'])


if __name__=='__main__': unittest.main()

import unittest
import hashlib
import tempfile
import sys
from pathlib import Path
from unittest.mock import patch
import fitz
from engineering.local_app import ocr


class SelectedOCRTests(unittest.TestCase):
    def parser(self):
        with patch.object(ocr, '_paths', return_value=(None, None)):
            return ocr.TesseractOCR()

    def test_selected_pass_is_bounded_and_does_not_claim_full_page(self):
        with fitz.open() as doc:
            page=doc.new_page(width=600,height=800)
            page.set_cropbox(fitz.Rect(100,100,500,700));page.set_rotation(90)
            parser=self.parser()
            raw=b'level\tpage_num\tblock_num\tpar_num\tline_num\tword_num\tleft\ttop\twidth\theight\tconf\ttext\n5\t1\t1\t1\t1\t1\t60\t60\t120\t30\t90\t56320\n'
            with patch.object(parser,'_recognize',return_value=raw) as recognize:
                blocks=parser.page_blocks(page,1,bbox=[50,100,150,130])
            self.assertEqual(recognize.call_args.kwargs['psm'],6)
            self.assertEqual(blocks[0]['provenance'][0]['bbox'],dict(left=60,top=110,right=80,bottom=115))
            self.assertEqual(blocks[0]['ocr_region'],'selected')
            self.assertEqual(parser.last_page_dossier['coverage'],'SELECTED_REGION_EXECUTED')
            self.assertFalse(parser.last_page_dossier['acceptance_granted'])
            self.assertEqual(parser.last_page_dossier['planned_passes'],1)
            self.assertEqual(page.rotation,90)
            self.assertEqual(list(page.cropbox),[100,100,500,700])

    def test_invalid_selected_regions_rejected_before_render(self):
        with fitz.open() as doc:
            page=doc.new_page(width=100,height=100);page.set_rotation(90)
            for box in ([0,0,101,20],[0,0,0,20],[0,0,float('nan'),20],[True,0,10,20],[0,1,2],None):
                if box is None:continue
                with self.subTest(box=box),patch.object(page,'get_pixmap') as render:
                    with self.assertRaisesRegex(ocr.OCRError,'OCR_INVALID_REGION'):
                        self.parser().page_blocks(page,1,bbox=box)
                    render.assert_not_called();self.assertEqual(page.rotation,90)

    def test_selected_pass_uses_existing_output_budget(self):
        with fitz.open() as doc:
            page=doc.new_page(width=100,height=100);parser=self.parser()
            with patch.object(parser,'_recognize',side_effect=ocr.OCRError('OCR_OUTPUT_LIMIT')):
                with self.assertRaisesRegex(ocr.OCRError,'OCR_OUTPUT_LIMIT'):
                    parser.page_blocks(page,1,bbox=[10,10,30,30])
            self.assertEqual(parser.last_page_dossier['coverage'],'INCOMPLETE')
            self.assertEqual(parser.last_page_dossier['completed_passes'],0)

    def test_cli_checks_original_hash_and_never_overwrites_source(self):
        from scripts.local_ocr_region import recognize_region
        with tempfile.TemporaryDirectory() as root,fitz.open() as doc:
            doc.new_page();source=Path(root)/'source.pdf';doc.save(source)
            original=source.read_bytes();sha=hashlib.sha256(original).hexdigest()
            with self.assertRaisesRegex(ValueError,'SHA256'):
                recognize_region(source,1,[10,10,50,50],'0'*64)
            parser=self.parser()
            with patch('scripts.local_ocr_region.TesseractOCR',return_value=parser),patch.object(parser,'_recognize',return_value=b'level\ttext\n'):
                result=recognize_region(source,1,[10,10,50,50],sha)
            self.assertEqual(result['source_sha256'],sha)
            self.assertFalse(result['document_complete']);self.assertFalse(result['acceptance_granted'])
            self.assertEqual(source.read_bytes(),original)

    def test_real_engine_reads_small_numeric_selection_with_source_coordinates(self):
        if not ocr.identity()['available']:self.skipTest('Local rus+eng unavailable')
        with fitz.open() as doc:
            page=doc.new_page(width=600,height=800)
            page.insert_text((200,300),'56320',fontsize=8)
            blocks=ocr.TesseractOCR().page_blocks(page,1,bbox=[180,280,240,310])
            block=next(b for b in blocks if '56320' in b['text'])
            box=block['provenance'][0]['bbox']
            self.assertTrue(195<=box['left']<box['right']<=230)
            self.assertTrue(290<=box['top']<box['bottom']<=302)

    def test_cli_refuses_existing_alias_outputs_before_ocr(self):
        from scripts.local_ocr_region import main
        with tempfile.TemporaryDirectory() as root:
            source=Path(root)/'source.pdf';source.write_bytes(b'original')
            linked=Path(root)/'linked.json';linked.symlink_to(source)
            hard=Path(root)/'hard.json';hard.hardlink_to(source)
            for target in (source,linked,hard):
                argv=['ocr',str(source),'--page','1','--bbox','0','0','1','1','--sha256','unused','--output',str(target)]
                with patch.object(sys,'argv',argv),patch('scripts.local_ocr_region.recognize_region') as recognize:
                    with self.assertRaisesRegex(ValueError,'OUTPUT_ALREADY_EXISTS'):main()
                    recognize.assert_not_called()
            self.assertEqual(source.read_bytes(),b'original')

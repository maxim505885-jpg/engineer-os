"""Explicit selected-line OCR keeps exact source pixels and unverified status."""
import base64
import hashlib
import json
from pathlib import Path
import unittest
import tempfile
from unittest.mock import patch
import fitz
from engineering.local_app import ocr
from tests import test_local_app_http as http_fixture

FIXTURE=Path(__file__).parent/'fixtures'/'ocr'/'level-plus-46740.json'
FIXTURE_SHA='5100272ae3e15a7e397d946cd3dc8a3098ec66775e8729a8650455445a4ca9f6'


class SingleLineOCRTests(unittest.TestCase):
    def test_cli_line_profile_records_actual_scale_for_long_selection(self):
        from scripts.local_ocr_region import recognize_region
        with tempfile.TemporaryDirectory() as temp,fitz.open() as doc:
            doc.new_page(width=1000,height=50);source=Path(temp)/'wide.pdf';doc.save(source)
            raw=source.read_bytes();sha=hashlib.sha256(raw).hexdigest()
            with patch.object(ocr,'_paths',return_value=(None,None)):
                parser=ocr.TesseractOCR()
            with patch('scripts.local_ocr_region.TesseractOCR',return_value=parser),patch('scripts.local_ocr_region.identity',return_value={'engine':'controlled'}),patch.object(parser,'_recognize',return_value=b'level\ttext\n'):
                try:result=recognize_region(source,1,[0,0,1000,50],sha,psm=7)
                except TypeError as exc:self.fail('CLI does not support single-line selection: '+str(exc))
            self.assertEqual(result['engine_identity']['psm'],7)
            self.assertEqual(result['engine_identity']['render_scale'],3.0)
            self.assertEqual(result['ocr_dossier']['regions'][0]['render_scale'],3.0)
            self.assertFalse(result['acceptance_granted'])
            self.assertEqual(source.read_bytes(),raw)

    def test_selected_line_profile_reaches_recognizer_and_dossier(self):
        with patch.object(ocr,'_paths',return_value=(None,None)):
            parser=ocr.TesseractOCR()
        with fitz.open() as doc:
            page=doc.new_page(width=200,height=100)
            with patch.object(parser,'_recognize',return_value=b'level\ttext\n') as recognize:
                try:parser.page_blocks(page,1,bbox=[10,10,180,80],selected_psm=7)
                except ocr.OCRError as exc:self.fail('Selected single-line profile rejected: '+str(exc))
            self.assertEqual(recognize.call_args.kwargs['psm'],7)
            self.assertEqual(parser.last_page_dossier['regions'][0]['psm'],7)
            self.assertFalse(parser.last_page_dossier['acceptance_granted'])

    def test_real_source_numeric_label_retains_plus_without_duplicate(self):
        if not ocr.identity()['available']:self.skipTest('Local rus+eng models unavailable')
        raw=base64.b64decode(json.loads(FIXTURE.read_text())['png_base64'],validate=True);self.assertEqual(hashlib.sha256(raw).hexdigest(),FIXTURE_SHA)
        with fitz.open() as doc:
            page=doc.new_page(width=55,height=25)
            page.insert_image(page.rect,stream=raw)
            parser=ocr.TesseractOCR()
            try:blocks=parser.page_blocks(page,1,bbox=[0,0,55,25],selected_psm=7)
            except ocr.OCRError as exc:self.fail('Selected single-line profile rejected: '+str(exc))
            self.assertEqual(''.join(' '.join(b['text'] for b in blocks).split()),'+46,740')
            self.assertEqual(parser.last_page_dossier['regions'][0]['input_raster']['png_sha256'],FIXTURE_SHA)
            self.assertEqual(base64.b64decode(json.loads(FIXTURE.read_text())['png_base64'],validate=True),raw)


class SingleLineHTTPTests(unittest.TestCase):
    setUp=http_fixture.LocalHTTPTests.setUp
    close=http_fixture.LocalHTTPTests.close
    request=http_fixture.LocalHTTPTests.request
    create=http_fixture.LocalHTTPTests.create

    def test_single_line_request_survives_authenticated_history_reload(self):
        if not ocr.identity()['available']:self.skipTest('Local rus+eng models unavailable')
        sid=self.create()
        with fitz.open() as doc:
            page=doc.new_page(width=55,height=25);page.insert_image(page.rect,stream=base64.b64decode(json.loads(FIXTURE.read_text())['png_base64'],validate=True));raw=doc.tobytes()
        status,_,data=self.request('POST',f'/api/sessions/{sid}/files?name=label.pdf',raw,{'Content-Type':'application/octet-stream'})
        self.assertEqual(status,201);file=json.loads(data);route=f'/api/sessions/{sid}/files/{file["id"]}/regions'
        request=dict(page=1,bbox=[0,0,55,25],expected_sha256=file['sha256'],ocr=True,ocr_psm=7)
        status,_,data=self.request('POST',route,request);self.assertEqual(status,201,data)
        item=json.loads(data);result=item['result']
        self.assertEqual(''.join(' '.join(b['text'] for b in result['ocr_blocks']).split()),'+46,740')
        self.assertEqual(result['engine_identity']['psm'],7)
        self.assertEqual(result['ocr_dossier']['regions'][0]['psm'],7)
        self.assertEqual(result['request_binding'],request)
        self.assertFalse(result['quality_verified']);self.assertFalse(result['acceptance_granted'])
        status,_,reloaded=self.request('GET',route+'/'+item['id']);self.assertEqual(status,200)
        self.assertEqual(json.loads(reloaded),item)
        self.assertEqual(self.store.snapshot(sid)['evidence'],[])
        self.assertEqual(Path(self.store.get_file(file['id'])['path']).read_bytes(),raw)

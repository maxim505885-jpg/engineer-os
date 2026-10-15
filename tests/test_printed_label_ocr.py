import base64,hashlib,json,unittest
from pathlib import Path
from unittest.mock import patch
import fitz
from engineering.local_app import ocr
from tests import test_local_app_http as hf
FIXTURE=Path(__file__).parent/'fixtures/ocr/printed-labels.json'
class PrintedLabelTests(unittest.TestCase):
 def test_real_three_source_labels_preserve_source_and_transform_locator(self):
  if not ocr.identity()['available']:self.skipTest('Local rus+eng models unavailable')
  for c in json.loads(FIXTURE.read_text(encoding='utf-8')):
   with self.subTest(c['id']),fitz.open()as doc:
    raw=base64.b64decode(c['png_base64']);self.assertEqual(hashlib.sha256(raw).hexdigest(),c['png_sha256'])
    box=c['bbox'];w,h=box[2]-box[0],box[3]-box[1];p=doc.new_page(width=w,height=h);p.insert_image(p.rect,stream=raw);parser=ocr.TesseractOCR()
    try:blocks=parser.page_blocks(p,1,bbox=[0,0,w,h],selected_psm=7,preprocess=c['preprocess'])
    except TypeError as e:self.fail('Explicit label preprocessing missing: '+str(e))
    self.assertEqual(''.join(' '.join(b['text']for b in blocks).split()),''.join(c['expected'].split()))
    d=parser.last_page_dossier['regions'][0];self.assertEqual(d['input_raster']['png_sha256'],c['png_sha256']);self.assertEqual(d['preprocessing'],c['preprocess'])
    derived=d['processed_raster'];self.assertEqual(derived['source_png_sha256'],c['png_sha256']);self.assertEqual(hashlib.sha256(base64.b64decode(derived['png_base64'])).hexdigest(),derived['png_sha256'])
    for b in blocks:
     loc=b['provenance'][0]['bbox'];self.assertTrue(0<=loc['left']<loc['right']<=w);self.assertTrue(0<=loc['top']<loc['bottom']<=h)
    self.assertFalse(parser.last_page_dossier['acceptance_granted'])
 def test_inverse_geometry_includes_shear_padding_and_fractional_pixel_origin(self):
  with patch.object(ocr,'_paths',return_value=(None,None)):parser=ocr.TesseractOCR()
  for profile,shear in [('padded',0),('italic',.1)]:
   with self.subTest(profile=profile),fitz.open()as doc:
    page=doc.new_page(width=100,height=100)
    def recognize(pixels,*args,**kwargs):
     self.assertEqual((pixels.x,pixels.y),(61,123))
     parser.last_processed_raster=dict(width=400,height=180,padding=20,shear=shear)
     return b'level\tblock_num\tpar_num\tline_num\tleft\ttop\twidth\theight\tconf\ttext\n5\t1\t1\t1\t50\t40\t100\t30\t90\ttext\n'
    with patch.object(parser,'_recognize',side_effect=recognize):blocks=parser.page_blocks(page,1,bbox=[10.25,20.5,60.25,40.5],selected_psm=7,preprocess=profile)
    box=blocks[0]['provenance'][0]['bbox']
    expected=dict(left=(91-50*shear)/6,right=(191-20*shear)/6,top=143/6,bottom=173/6)
    for key,value in expected.items():self.assertAlmostEqual(box[key],value)
 def test_invalid_preprocessing_is_rejected_before_source_render(self):
  with patch.object(ocr,'_paths',return_value=(None,None)):parser=ocr.TesseractOCR()
  for profile in ['autocorrect',None,True]:
   with self.subTest(profile=profile),self.assertRaisesRegex(ocr.OCRError,'OCR_INVALID_PREPROCESSING'):parser.page_blocks(None,1,bbox=[0,0,10,10],selected_psm=7,preprocess=profile)
 def test_preprocessing_requires_explicit_selected_single_line(self):
  with patch.object(ocr,'_paths',return_value=(None,None)):parser=ocr.TesseractOCR()
  for bbox,psm in [(None,7),([0,0,10,10],6),([0,0,10,10],11)]:
   with self.subTest(bbox=bbox,psm=psm),self.assertRaisesRegex(ocr.OCRError,'OCR_PREPROCESSING_REQUIRES_SELECTED_LINE'):parser.page_blocks(None,1,bbox=bbox,selected_psm=psm,preprocess='italic')
class PrintedLabelHTTPTests(unittest.TestCase):
 setUp=hf.LocalHTTPTests.setUp
 close=hf.LocalHTTPTests.close
 request=hf.LocalHTTPTests.request
 create=hf.LocalHTTPTests.create
 def test_explicit_preprocessing_survives_worker_history_and_rejects_tampering(self):
  if not ocr.identity()['available']:self.skipTest('Local rus+eng models unavailable')
  from engineering.local_app.region_history import _validate
  sid=self.create();c=json.loads(FIXTURE.read_text())[1];box=c['bbox'];w,h=box[2]-box[0],box[3]-box[1]
  with fitz.open()as d:p=d.new_page(width=w,height=h);p.insert_image(p.rect,stream=base64.b64decode(c['png_base64']));raw=d.tobytes()
  status,_,data=self.request('POST',f'/api/sessions/{sid}/files?name=label.pdf',raw,{'Content-Type':'application/octet-stream'});self.assertEqual(status,201);f=json.loads(data);route=f'/api/sessions/{sid}/files/{f["id"]}/regions'
  req=dict(page=1,bbox=[0,0,w,h],expected_sha256=f['sha256'],ocr=True,ocr_psm=7,ocr_preprocess='italic')
  status,_,data=self.request('POST',route,req);self.assertEqual(status,201,data);item=json.loads(data);r=item['result']
  self.assertEqual(''.join(' '.join(b['text']for b in r['ocr_blocks']).split()),'Прогиб27мм');self.assertEqual(r['request_binding'],req)
  status,_,data=self.request('GET',route+'/'+item['id']);self.assertEqual(status,200);self.assertEqual(json.loads(data),item)
  self.assertEqual(self.store.snapshot(sid)['evidence'],[]);self.assertEqual(Path(self.store.get_file(f['id'])['path']).read_bytes(),raw)
  r['ocr_dossier']['regions'][0]['processed_raster']['source_png_sha256']='0'*64
  with self.assertRaisesRegex(ValueError,'processed raster'):_validate(r,f,req)

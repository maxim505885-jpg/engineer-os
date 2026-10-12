import base64,hashlib,json,unittest
from pathlib import Path
from unittest.mock import patch
import fitz
from engineering.local_app import ocr
from tests import test_local_app_http as hf
FIXTURE=Path(__file__).parent/'fixtures/ocr/latin-reinforcement.json'
class OCRLanguageTests(unittest.TestCase):
 def test_actual_latin_values_remain_d_not_digits_with_exact_source_binding(self):
  if not ocr.identity()['available']:self.skipTest('Local rus+eng models unavailable')
  for c in json.loads(FIXTURE.read_text()):
   with self.subTest(row=c['row'],column=c['column']),fitz.open()as d:
    raw=base64.b64decode(c['png_base64']);self.assertEqual(hashlib.sha256(raw).hexdigest(),c['png_sha256']);b=c['source_bbox'];w,h=b[2]-b[0],b[3]-b[1];p=d.new_page(width=w,height=h);p.insert_image(p.rect,stream=raw);parser=ocr.TesseractOCR()
    try:blocks=parser.page_blocks(p,1,bbox=[0,0,w,h],selected_psm=7,preprocess='padded',language='eng')
    except TypeError as e:self.fail('Explicit local language selection unavailable: '+str(e))
    self.assertEqual(''.join(' '.join(b['text']for b in blocks).split()),''.join(c['expected'].split()))
    region=parser.last_page_dossier['regions'][0];self.assertEqual(region['language'],'eng');render=p.get_pixmap(matrix=fitz.Matrix(6,6),clip=fitz.Rect(0,0,w,h),alpha=False).tobytes('png');self.assertEqual(region['input_raster']['png_sha256'],hashlib.sha256(render).hexdigest());self.assertFalse(parser.last_page_dossier['acceptance_granted'])
 def test_invalid_language_rejects_before_source_render(self):
  with patch.object(ocr,'_paths',return_value=(None,None)):parser=ocr.TesseractOCR()
  for language in [None,True,[],{},'eng --psm 0','auto','eng+rus']:
   with self.subTest(language=language),self.assertRaisesRegex(ocr.OCRError,'OCR_INVALID_LANGUAGE'):parser.page_blocks(None,1,bbox=[0,0,1,1],language=language)
 def test_nondefault_language_cannot_change_whole_page_flow(self):
  with patch.object(ocr,'_paths',return_value=(None,None)):parser=ocr.TesseractOCR()
  with self.assertRaisesRegex(ocr.OCRError,'OCR_LANGUAGE_REQUIRES_SELECTED_REGION'):parser.page_blocks(None,1,language='eng')
class OCRLanguageHTTPTests(unittest.TestCase):
 setUp=hf.LocalHTTPTests.setUp
 close=hf.LocalHTTPTests.close
 request=hf.LocalHTTPTests.request
 create=hf.LocalHTTPTests.create
 def test_actual_language_reaches_worker_and_persisted_request_binding(self):
  if not ocr.identity()['available']:self.skipTest('Local rus+eng models unavailable')
  from engineering.local_app.region_history import _validate
  sid=self.create();c=json.loads(FIXTURE.read_text())[0];b=c['source_bbox'];w,h=b[2]-b[0],b[3]-b[1]
  with fitz.open()as d:p=d.new_page(width=w,height=h);p.insert_image(p.rect,stream=base64.b64decode(c['png_base64']));raw=d.tobytes()
  status,_,data=self.request('POST',f'/api/sessions/{sid}/files?name=latin.pdf',raw,{'Content-Type':'application/octet-stream'});self.assertEqual(status,201);f=json.loads(data);route=f'/api/sessions/{sid}/files/{f["id"]}/regions';req=dict(page=1,bbox=[0,0,w,h],expected_sha256=f['sha256'],ocr=True,ocr_psm=7,ocr_preprocess='padded',ocr_language='eng')
  status,_,data=self.request('POST',route,req);self.assertEqual(status,201,data);item=json.loads(data);r=item['result'];self.assertEqual(''.join(' '.join(x['text']for x in r['ocr_blocks']).split()),'4d20+4d16');self.assertEqual(r['request_binding'],req);self.assertEqual(r['engine_identity']['language'],'eng')
  status,_,data=self.request('GET',route+'/'+item['id']);self.assertEqual(status,200);self.assertEqual(json.loads(data),item);self.assertEqual(self.store.snapshot(sid)['evidence'],[]);self.assertEqual(Path(self.store.get_file(f['id'])['path']).read_bytes(),raw)
  from engineering.local_app.region_history import _json
  for value in ['rus+eng',None]:
   corrupted=json.loads(json.dumps(item['result']))
   if value is None:corrupted['engine_identity'].pop('language',None)
   else:corrupted['engine_identity']['language']=value
   encoded=_json(corrupted)
   with self.store.connection()as db:db.execute('UPDATE source_region_reads SET result=?,result_sha256=? WHERE id=?',(encoded,hashlib.sha256(encoded.encode()).hexdigest(),item['id']))
   status,_,data=self.request('GET',route+'/'+item['id']);self.assertEqual(status,400,data)
  default=dict(req);default.pop('ocr_language');status,_,data=self.request('POST',route,default);self.assertEqual(status,201,data);other=json.loads(data)
  other['result']['engine_identity']['language']='eng';encoded=_json(other['result'])
  with self.store.connection()as db:db.execute('UPDATE source_region_reads SET result=?,result_sha256=? WHERE id=?',(encoded,hashlib.sha256(encoded.encode()).hexdigest(),other['id']))
  status,_,data=self.request('GET',route+'/'+other['id']);self.assertEqual(status,400,data)
  r['ocr_dossier']['regions'][0]['language']='rus+eng'
  with self.assertRaisesRegex(ValueError,'language'):_validate(r,f,req)

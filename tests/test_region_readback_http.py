"""Source-region readback reaches authenticated, durable local history without acceptance."""
import hashlib,json,unittest
from pathlib import Path
from unittest.mock import patch
from tests import test_local_app_http as fixture

class RegionHTTPTests(unittest.TestCase):
    setUp=fixture.LocalHTTPTests.setUp
    close=fixture.LocalHTTPTests.close
    request=fixture.LocalHTTPTests.request
    create=fixture.LocalHTTPTests.create
    def source(self):
        import fitz
        pdf=fitz.open();p=pdf.new_page(width=300,height=200);p.insert_text((50,80),'A 123.45');raw=pdf.tobytes();pdf.close()
        sid=self.create();status,_,data=self.request('POST',f'/api/sessions/{sid}/files?name=region.pdf',raw,{'Content-Type':'application/octet-stream'});self.assertEqual(status,201)
        f=json.loads(data);return sid,f,raw,f'/api/sessions/{sid}/files/{f["id"]}/regions'
    def test_native_read_persists_and_reloads_without_evidence(self):
        sid,f,original,route=self.source();body=dict(page=1,bbox=[40,55,160,95],expected_sha256=f['sha256'],ocr=False)
        self.assertEqual(self.request('POST',route,body,token=False)[0],403)
        status,_,raw=self.request('POST',route,body);self.assertEqual(status,201,raw)
        item=json.loads(raw);self.assertFalse(item['result']['acceptance_granted']);self.assertIn('123.45',str(item['result']['native_words']))
        status,_,raw=self.request('GET',route);self.assertEqual(status,200);history=json.loads(raw);self.assertEqual(history['total'],1)
        status,_,saved=self.request('GET',route+'/'+item['id']);self.assertEqual(status,200);self.assertEqual(json.loads(saved),item)
        from engineering.local_app.store import Store
        from engineering.local_app.region_history import get_region
        reopened=Store(self.store.root);self.assertEqual(get_region(reopened,sid,f['id'],item['id']),item)
        self.assertEqual(self.store.snapshot(sid)['evidence'],[]);self.assertEqual(Path(self.store.get_file(f['id'])['path']).read_bytes(),original)
        self.assertEqual(self.request('GET',route.replace(sid,self.create())+'/'+item['id'])[0],400)
        Path(self.store.get_file(f['id'])['path']).write_bytes(b'changed');self.assertEqual(self.request('GET',route+'/'+item['id'])[0],400)
    def test_invalid_scope_hash_bounds_and_busy_fail_before_history(self):
        sid,f,_,route=self.source();body=dict(page=1,bbox=[40,55,160,95],expected_sha256=f['sha256'],ocr=False)
        for change in [dict(expected_sha256='0'*64),dict(bbox=[0,0,301,200]),dict(page=True),dict(ocr='yes')]:
            status,_,_=self.request('POST',route,dict(body,**change));self.assertEqual(status,400)
        self.server.preview_slots.acquire();self.server.preview_slots.acquire()
        try:self.assertEqual(self.request('POST',route,body)[0],429)
        finally:self.server.preview_slots.release();self.server.preview_slots.release()
        self.assertEqual(json.loads(self.request('GET',route)[2])['total'],0)
    def test_stored_result_tampering_and_storage_limit_are_rejected(self):
        sid,f,_,route=self.source();body=dict(page=1,bbox=[40,55,160,95],expected_sha256=f['sha256'],ocr=False)
        status,_,raw=self.request('POST',route,body);self.assertEqual(status,201,raw);item=json.loads(raw)
        with self.store.connection() as db:db.execute('UPDATE source_region_reads SET result=? WHERE id=?',(json.dumps(dict(item['result'],native_text='invented')),item['id']))
        self.assertEqual(self.request('GET',route+'/'+item['id'])[0],400)
        from engineering.local_app import region_history
        with patch.object(region_history,'MAX_READS_PER_FILE',1):self.assertEqual(self.request('POST',route,body)[0],400)

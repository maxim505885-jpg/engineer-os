"""Real authenticated local routes for knowledge and preserved CAD originals."""
import json
import unittest
from tests import test_local_app_http as fixture


class ProductExtensionHTTPTests(unittest.TestCase):
    setUp=fixture.LocalHTTPTests.setUp
    close=fixture.LocalHTTPTests.close
    request=fixture.LocalHTTPTests.request
    create=fixture.LocalHTTPTests.create

    def test_knowledge_requires_token_and_live_acceptance(self):
        sid=self.create();url=f'/api/sessions/{sid}/knowledge'
        self.assertEqual(self.request('GET',url,token=False)[0],403)
        status,_,raw=self.request('GET',url)
        self.assertEqual(status,200);self.assertEqual(json.loads(raw)['records'],[])
        status,_,raw=self.request('GET',url+'/recall')
        self.assertEqual(status,200);self.assertFalse(json.loads(raw)['acceptance_granted'])
        self.assertEqual(self.request('POST',url,{'expected_audit_id':sid,'title':'No acceptance','evidence_ids':[sid],'actor':'tester'})[0],400)
        status,_,raw=self.request('GET',url+'/export')
        self.assertEqual(status,200);self.assertEqual(json.loads(raw)['records'],[])

    def test_cad_upload_and_session_isolated_inventory(self):
        sid=self.create();other=self.create()
        url=f'/api/sessions/{sid}/files?name=drawing.dwg'
        status,_,raw=self.request('POST',url,b'AC1032\x00controlled DWG header',headers={'Content-Type':'application/octet-stream','X-Filename':'drawing.dwg'})
        self.assertEqual(status,201);fid=json.loads(raw)['id']
        route=f'/api/sessions/{sid}/cad/{fid}'
        self.assertEqual(self.request('GET',route,token=False)[0],403)
        status,_,raw=self.request('GET',route)
        self.assertEqual(status,200);self.assertEqual(json.loads(raw)['status'],'BLOCK')
        self.assertEqual(self.request('GET',f'/api/sessions/{other}/cad/{fid}')[0],400)


if __name__=='__main__':unittest.main()

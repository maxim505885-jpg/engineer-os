import json
import unittest
from tests import test_local_app_http as http_fixture


class CalculationHTTPTests(unittest.TestCase):
    setUp=http_fixture.LocalHTTPTests.setUp
    close=http_fixture.LocalHTTPTests.close
    request=http_fixture.LocalHTTPTests.request
    create=http_fixture.LocalHTTPTests.create

    def test_authenticated_http_to_existing_worker_rectangle(self):
        from engineering.local_app.files import preserve_file
        from engineering.local_app.worker import Worker
        sid=self.create();source=preserve_file(self.store,sid,'dimensions.txt',b'Unverified user dimensions')
        route=f'/api/sessions/{sid}/engineering-runs'
        self.assertEqual(self.request('GET',route,token=False)[0],403)
        status,_,raw=self.request('GET',route);self.assertEqual(status,200)
        catalog=json.loads(raw)
        body=dict(tool='RECTANGLE',input_file_ids=[source['id']],options=dict(width_m=.2,height_m=.4,units='N_m_Pa'),expected_revision=catalog['expected_revision'])
        self.assertEqual(self.request('POST',route,body,token=False)[0],403)
        self.assertEqual(self.request('POST',route,dict(body,acceptance_granted=True))[0],400)
        self.assertEqual(self.request('POST',route,body)[0],202)
        Worker(self.store,None).run_once()
        result=self.store.snapshot(sid)['jobs'][0]['result']
        self.assertEqual(result['engineering_run']['result']['status'],'PASS')
        self.assertFalse(result['acceptance_granted'])

    def test_unknown_or_unqualified_adapter_is_not_queued(self):
        sid=self.create();route=f'/api/sessions/{sid}/engineering-runs'
        status,_,raw=self.request('GET',route);catalog=json.loads(raw)
        self.assertEqual(self.request('POST',route,dict(tool='DWG_CONVERT',input_file_ids=[],options={},expected_revision=catalog['expected_revision']))[0],400)
        self.assertFalse(self.store.snapshot(sid)['jobs'])

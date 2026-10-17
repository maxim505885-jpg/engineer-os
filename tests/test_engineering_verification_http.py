import json
import unittest
from tests import test_local_app_http as fixture


class VerificationHTTPTests(unittest.TestCase):
    setUp=fixture.LocalHTTPTests.setUp
    close=fixture.LocalHTTPTests.close
    request=fixture.LocalHTTPTests.request
    create=fixture.LocalHTTPTests.create

    def test_explicit_review_intent_and_exact_fields_required(self):
        from engineering.local_app.files import preserve_file
        from engineering.local_app.evidence import register
        from engineering.local_app.review import record_review
        sid=self.create();source=preserve_file(self.store,sid,'project.txt',b'Project height 4 m.')
        candidate=register(self.store,sid,file_id=source['id'],quote='Project height 4 m.',statement='Project declaration',data_class='P')
        record_review(self.store,sid,candidate['id'],expected_revision=0,decision='SOURCE_CONFIRMED',note='Exact original quotation',actor='Reader')
        self.assertEqual(self.request('GET','/api/review-authority',token=False)[0],403)
        self.assertIn(self.request('POST','/api/review-authority',{})[0],(400,403))
        provision_headers={'X-Engineer-Review-Intent':'PROVISION_LOCAL_REVIEW_AUTHORITY'}
        self.assertEqual(self.request('POST','/api/review-authority',{},provision_headers)[0],201)
        route=f'/api/sessions/{sid}/verifications'
        status,_,raw=self.request('GET',route+f'?kind=EVIDENCE&subject_id={candidate["id"]}')
        self.assertEqual(status,200);state=json.loads(raw)
        body=dict(subject_kind='EVIDENCE',subject_id=candidate['id'],expected_revision=state['expected_revision'],decision='ACCEPTED',
            reviewer='Controlled HTTP reviewer',method='Project quotation/class review',source_refs=state['source_refs'],reason='Only PROJECT declaration reviewed')
        self.assertIn(self.request('POST',route,body)[0],(400,403))
        headers={'X-Engineer-Review-Intent':'RESPONSIBLE_ENGINEERING_REVIEW'}
        self.assertEqual(self.request('POST',route,dict(body,engineering_verified=True),headers)[0],400)
        self.assertEqual(self.request('POST',route,body,headers)[0],201)
        status,_,raw=self.request('GET',route+f'?kind=EVIDENCE&subject_id={candidate["id"]}')
        self.assertEqual(status,200);self.assertTrue(json.loads(raw)['verified_subject']['engineering_verified'])
        self.assertEqual(self.store.final_audit_state(sid),[])
        self.assertIsNone(self.store.get_evidence(sid,candidate['id']).get('engineering_verified'))

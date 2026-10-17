import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


@unittest.skipUnless(importlib.util.find_spec('ifcopenshell'),'Optional IFC profile absent')
class IfcEvidenceTests(unittest.TestCase):
    def setUp(self):
        from engineering.local_app.store import Store
        from engineering.local_app.files import preserve_file
        import ifcopenshell
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.store=Store(Path(self.temp.name));self.sid=self.store.create_session()['id']
        raw=(Path(__file__).parent/'fixtures/bim/reference.ifc').read_bytes()
        saved=preserve_file(self.store,self.sid,'model.ifc',raw);self.file=self.store.get_file(saved['id'])
        guid=ifcopenshell.open(self.file['path']).by_type('IfcBeam')[0].GlobalId
        self.locator=dict(kind='IFC_GUID',source_sha256=self.file['sha256'],model_revision=self.file['sha256'],guid=guid,property_path=['properties','BaseQuantities','Length'])

    def locate(self,locator=None):
        from engineering.local_app.source_binding import ifc_location
        return ifc_location(self.store,self.sid,self.file,self.locator if locator is None else locator)

    def register(self,**changes):
        from engineering.local_app.evidence import register
        request=dict(file_id=self.file['id'],quote=self.locate()['quote'],statement='Declared IFC quantity, not a site measurement.',data_class='P',ifc_locator=self.locator)
        request.update(changes)
        return register(self.store,self.sid,**request)

    def test_numeric_property_is_typed_project_value_with_unqualified_units(self):
        located=self.locate();value=json.loads(located['quote'])
        self.assertEqual(value['value'],6000.)
        self.assertEqual(value['unit_interpretation'],'NOT_QUALIFIED')
        candidate=self.register();self.assertEqual(candidate['locator'],self.locator)
        self.assertFalse(candidate['data_class_verified']);self.assertFalse(candidate['acceptance_granted'])

    def test_unknown_guid_wrong_revision_or_injected_path_refused(self):
        for change in ({'guid':'3'+'0'*21},{'source_sha256':'0'*64},{'model_revision':'0'*64},{'property_path':['__dict__']},{'property_path':['properties','BaseQuantities','Unknown']}):
            with self.subTest(change=change),self.assertRaises(ValueError):self.locate(dict(self.locator,**change))

    def test_model_value_cannot_be_relabelled_measured_or_quoted_as_bare_number(self):
        for change in ({'data_class':'M'},{'data_class':'F'},{'quote':'6000'},{'page':1}):
            with self.subTest(change=change),self.assertRaises(ValueError):self.register(**change)

    def test_source_review_revalidates_the_same_model_property(self):
        from engineering.local_app.review import record_review
        from engineering.local_app.source_binding import validate_candidate
        candidate=self.register()
        record_review(self.store,self.sid,candidate['id'],expected_revision=0,decision='SOURCE_CONFIRMED',note='Exact declared model property reviewed',actor='Controlled reviewer')
        validate_candidate(self.store,self.sid,candidate)
        Path(self.file['path']).write_bytes(b'Changed source')
        with self.assertRaises(ValueError):validate_candidate(self.store,self.sid,candidate)

    def test_foreign_session_and_ambiguous_model_property_refused(self):
        from engineering.local_app.source_binding import ifc_location
        other=self.store.create_session()['id']
        with self.assertRaises(ValueError):ifc_location(self.store,other,self.file,self.locator)
        import ifcopenshell
        model=ifcopenshell.open(self.file['path']);beam=model.by_type('IfcBeam')[0]
        original=next(r.RelatingPropertyDefinition for r in beam.IsDefinedBy if r.is_a('IfcRelDefinesByProperties'))
        duplicate=model.create_entity('IfcElementQuantity',GlobalId=ifcopenshell.guid.new(),Name=original.Name,Quantities=original.Quantities)
        model.create_entity('IfcRelDefinesByProperties',GlobalId=ifcopenshell.guid.new(),RelatedObjects=[beam],RelatingPropertyDefinition=duplicate)
        target=Path(self.temp.name)/'ambiguous.ifc';model.write(str(target))
        from engineering.local_app.files import preserve_file
        saved=preserve_file(self.store,self.sid,'ambiguous.ifc',target.read_bytes());saved=self.store.get_file(saved['id'])
        locator=dict(self.locator,source_sha256=saved['sha256'],model_revision=saved['sha256'])
        with self.assertRaises(ValueError):ifc_location(self.store,self.sid,saved,locator)


from tests import test_local_app_http as http_fixture


@unittest.skipUnless(importlib.util.find_spec('ifcopenshell'),'Optional IFC profile absent')
class IfcEvidenceHTTPTests(unittest.TestCase):
    setUp=http_fixture.LocalHTTPTests.setUp
    close=http_fixture.LocalHTTPTests.close
    request=http_fixture.LocalHTTPTests.request
    create=http_fixture.LocalHTTPTests.create

    def test_locator_and_registration_are_authenticated_and_project_only(self):
        import ifcopenshell
        from urllib.parse import urlencode
        from engineering.local_app.files import preserve_file
        sid=self.create();raw=(Path(__file__).parent/'fixtures/bim/reference.ifc').read_bytes()
        file=preserve_file(self.store,sid,'reference.ifc',raw)
        guid=ifcopenshell.open(self.store.get_file(file['id'])['path']).by_type('IfcBeam')[0].GlobalId
        locator=dict(kind='IFC_GUID',source_sha256=file['sha256'],model_revision=file['sha256'],guid=guid,property_path=['type'])
        route=f'/api/sessions/{sid}/files/{file["id"]}/ifc-location?'+urlencode({'locator':json.dumps(locator)})
        self.assertEqual(self.request('GET',route,token=False)[0],403)
        status,_,body=self.request('GET',route);self.assertEqual(status,200,body)
        source=json.loads(body)
        evidence=dict(file_id=file['id'],quote=source['quote'],statement='Declared model class only',data_class='P',ifc_locator=locator)
        self.assertEqual(self.request('POST',f'/api/sessions/{sid}/evidence',evidence,token=False)[0],403)
        status,_,body=self.request('POST',f'/api/sessions/{sid}/evidence',evidence)
        self.assertEqual(status,201,body);self.assertFalse(json.loads(body)['acceptance_granted'])
        self.assertEqual(self.request('POST',f'/api/sessions/{sid}/evidence',dict(evidence,data_class='M'))[0],400)

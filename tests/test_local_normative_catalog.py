"""Application catalog boundary, using synthetic sources only."""
import json
import unittest
from pathlib import Path
from tests import test_normative_catalog as catalog_tests
from engineering.local_app.files import preserve_file

class LocalCatalogTests(unittest.TestCase):
    setUp=catalog_tests.CatalogPacketTests.setUp
    candidate=catalog_tests.CatalogPacketTests.candidate
    module=catalog_tests.CatalogPacketTests.module
    packet=catalog_tests.CatalogPacketTests.packet
    configured=catalog_tests.CatalogPacketTests.configured
    def prepare(self):
        packet=self.configured()
        self.binding=packet['catalog_rule']
        entry=dict(self.binding['rule'],source_path='norm.txt')
        self.catalog=preserve_file(self.store,self.sid,'catalog.json',json.dumps(dict(format_version=1,registry_version='synthetic',rules=[entry])).encode())
        return [self.norm['id']]
    def load(self,ids=None):
        try:from engineering.local_app.normative_catalog import inspect_catalog
        except ImportError:self.fail("Application catalog selection is unavailable")
        return inspect_catalog(self.store,self.sid,catalog_file_id=self.catalog['id'],source_file_ids=ids if ids is not None else [self.norm['id']])
    def test_selectable_rule_has_exact_source_clause_and_no_acceptance(self):
        self.prepare();r=self.load();self.assertFalse(r['acceptance_granted'])
        row=r['rules'][0];self.assertEqual(row['rule_sha256'],self.binding['rule_sha256'])
        self.assertEqual(row['source']['file_id'],self.norm['id']);self.assertEqual(row['rule']['clause_text'],'clause1 Limit 2.5 m')
    def test_limit_fragment_preserves_exact_source_whitespace(self):
        import hashlib
        self.prepare()
        for gap in ('\n','\u00a0','   '):
            requirement='Limit 2.5'+gap+'m';text='TEST 2026 clause1 '+requirement
            self.norm=preserve_file(self.store,self.sid,'norm.txt',text.encode())
            rule=dict(self.binding['rule'],normative_source_sha256=hashlib.sha256(text.encode()).hexdigest(),requirement=requirement,clause_text='clause1 '+requirement,source_path='norm.txt')
            self.catalog=preserve_file(self.store,self.sid,'catalog.json',json.dumps(dict(format_version=1,registry_version='synthetic',rules=[rule])).encode())
            self.assertEqual(self.load()['rules'][0].get('limit_fragment'),'2.5'+gap+'m')
    def test_missing_or_ambiguous_source_is_rejected(self):
        self.prepare()
        with self.assertRaises(ValueError):self.load([])
        duplicate=preserve_file(self.store,self.sid,'norm.txt',b'different')
        with self.assertRaises(ValueError):self.load([self.norm['id'],duplicate['id']])
    def test_foreign_source_or_catalog_is_rejected(self):
        self.prepare();other=self.store.create_session()['id'];foreign=preserve_file(self.store,other,'norm.txt',b'TEST')
        with self.assertRaises(ValueError):self.load([foreign['id']])
        self.catalog=preserve_file(self.store,other,'catalog.json',b'{}')
        with self.assertRaises(ValueError):self.load()
    def test_changed_source_and_catalog_fail_closed(self):
        self.prepare();path=Path(self.store.get_file(self.norm['id'])['path']);old=path.read_bytes();path.write_bytes(b'changed')
        with self.assertRaises(ValueError):self.load()
        path.write_bytes(old);Path(self.store.get_file(self.catalog['id'])['path']).write_bytes(b'{}')
        with self.assertRaises(ValueError):self.load()
    def test_duplicate_json_keys_and_paths_are_rejected(self):
        self.prepare()
        for raw in (b'{"format_version":1,"format_version":1}',json.dumps(dict(format_version=1,registry_version='synthetic',rules=[dict(self.binding['rule'],source_path='../norm.txt')])).encode()):
            self.catalog=preserve_file(self.store,self.sid,'catalog.json',raw)
            with self.assertRaises(ValueError):self.load()
    def test_catalog_is_not_modified_or_persisted_as_a_packet(self):
        self.prepare();before=self.store.snapshot(self.sid);self.load();after=self.store.snapshot(self.sid)
        self.assertEqual(before,after)

    def test_mutation_during_inspection_is_rejected(self):
        from unittest.mock import patch
        from engineering.local_app import normative_catalog
        self.prepare();original=normative_catalog.load_rule_catalog
        def changed(path):
            registry=original(path)
            Path(self.store.get_file(self.norm['id'])['path']).write_bytes(b'changed during inspection')
            return registry
        with patch.object(normative_catalog,'load_rule_catalog',side_effect=changed):
            with self.assertRaises(ValueError):self.load()
    def test_oversized_catalog_is_rejected(self):
        from engineering.normative.catalog import MAX_CATALOG_BYTES
        self.prepare();self.catalog=preserve_file(self.store,self.sid,'oversized.json',b' '*(MAX_CATALOG_BYTES+1))
        with self.assertRaises(ValueError):self.load()

from tests import test_local_app_http as http_tests
class CatalogHTTPTests(unittest.TestCase):
    setUp=http_tests.LocalHTTPTests.setUp
    close=http_tests.LocalHTTPTests.close
    request=http_tests.LocalHTTPTests.request
    candidate=LocalCatalogTests.candidate
    packet=LocalCatalogTests.packet
    configured=LocalCatalogTests.configured
    prepare=LocalCatalogTests.prepare
    def test_http_catalog_requires_token_exact_fields_and_same_project(self):
        self.sid=self.store.create_session()['id']
        self.norm=preserve_file(self.store,self.sid,'norm.txt',b'TEST 2026 clause1 Limit 2.5 m')
        self.actual=preserve_file(self.store,self.sid,'actual.txt',b'Height 2500 mm')
        self.n=self.candidate(self.norm,'TEST 2026 clause1 Limit 2.5 m');self.a=self.candidate(self.actual,'Height 2500 mm')
        self.prepare();url='/api/sessions/'+self.sid+'/normative-catalog'
        body=dict(catalog_file_id=self.catalog['id'],source_file_ids=[self.norm['id']])
        self.assertEqual(self.request('POST',url,body,token=False)[0],403)
        self.assertEqual(self.request('POST',url,dict(body,acceptance_granted=True))[0],400)
        status,_,raw=self.request('POST',url,body);self.assertEqual(status,200)
        result=json.loads(raw);self.assertFalse(result['acceptance_granted']);self.assertEqual(result['rules'][0]['source']['file_id'],self.norm['id'])
        other=self.store.create_session()['id'];self.assertEqual(self.request('POST','/api/sessions/'+other+'/normative-catalog',body)[0],400)

if __name__=='__main__':unittest.main()

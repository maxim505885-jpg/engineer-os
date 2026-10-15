import json
import tempfile
import threading
import unittest
from pathlib import Path
from http.client import HTTPConnection


class BuildIdentityTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        (self.root/'engineering').mkdir()
        (self.root/'engineering/app.py').write_text('VALUE=1\n',encoding='utf-8')

    def manifest(self,**changes):
        from engineering.local_app.build_identity import create_manifest
        data=create_manifest(self.root,version='0.1.0-rc.1',profile='native',tree_sha='a'*40,dirty=False)
        data.update(changes);path=self.root/'build-manifest.json'
        path.write_text(json.dumps(data),encoding='utf-8');return path

    def test_verified_bundle_has_exact_identity_and_no_engineering_acceptance(self):
        from engineering.local_app.build_identity import BuildIdentity
        build=BuildIdentity(self.root,manifest_path=self.manifest(),profile='native')
        report=build.report()
        self.assertTrue(report['artifact_verified'])
        self.assertEqual(report['tree_sha'],'a'*40)
        self.assertEqual(report['version'],'0.1.0-rc.1')
        self.assertEqual(report['status'],'PASS')
        self.assertFalse(report['acceptance_granted'])
        self.assertEqual(len(report['manifest_sha256']),64)

    def test_missing_manifest_is_development_not_verified_release(self):
        from engineering.local_app.build_identity import BuildIdentity
        report=BuildIdentity(self.root,profile='native').report()
        self.assertFalse(report['artifact_verified'])
        self.assertEqual(report['version'],'development')
        self.assertIn('BUILD_MANIFEST_MISSING',report['reasons'])

    def test_development_startup_binds_actual_source_not_just_git_head(self):
        from engineering.local_app.build_identity import BuildIdentity
        first=BuildIdentity(self.root,discover_git=True).report()
        (self.root/'engineering/app.py').write_text('VALUE=2\n',encoding='utf-8')
        second=BuildIdentity(self.root,discover_git=True).report()
        self.assertEqual(len(first['source_sha256']),64)
        self.assertNotEqual(first['source_sha256'],second['source_sha256'])

    def test_inventory_stops_enumeration_at_file_budget(self):
        from engineering.local_app.build_identity import inventory
        from unittest.mock import patch
        files=[self.root/'engineering/app.py']
        for index in range(3):
            p=self.root/f'engineering/extra{index}.py';p.write_text('pass\n');files.append(p)
        def many_paths(*args,**kwargs):
            yield from files
            raise AssertionError('enumerated beyond budget')
        with patch('engineering.local_app.build_identity.MAX_FILES',2),patch.object(Path,'rglob',many_paths):
            with self.assertRaisesRegex(ValueError,'BUILD_FILE_COUNT_LIMIT'):inventory(self.root)

    def test_changed_or_added_runtime_file_invalidates_frozen_startup(self):
        from engineering.local_app.build_identity import BuildIdentity
        path=self.manifest();build=BuildIdentity(self.root,manifest_path=path,profile='native')
        (self.root/'engineering/app.py').write_text('VALUE=2\n',encoding='utf-8')
        self.assertFalse(build.report()['artifact_verified'])
        self.assertIn('BUILD_SOURCE_CHANGED',build.report()['reasons'])
        self.assertEqual(build.report()['tree_sha'],'a'*40)
        (self.root/'engineering/app.py').write_text('VALUE=1\n',encoding='utf-8')
        build=BuildIdentity(self.root,manifest_path=path,profile='native')
        (self.root/'engineering/injected.py').write_text('VALUE=3\n',encoding='utf-8')
        self.assertIn('BUILD_SOURCE_CHANGED',build.report()['reasons'])

    def test_observed_code_change_requires_restart_even_after_file_restore(self):
        from engineering.local_app.build_identity import BuildIdentity
        build=BuildIdentity(self.root,manifest_path=self.manifest())
        path=self.root/'engineering/app.py';path.write_text('VALUE=2\n',encoding='utf-8')
        self.assertFalse(build.report()['artifact_verified'])
        path.write_text('VALUE=1\n',encoding='utf-8')
        self.assertFalse(build.report()['artifact_verified'])

    def test_dirty_profile_mismatch_and_manifest_tampering_block(self):
        from engineering.local_app.build_identity import BuildIdentity
        self.assertFalse(BuildIdentity(self.root,manifest_path=self.manifest(dirty=True),profile='native').report()['artifact_verified'])
        self.assertFalse(BuildIdentity(self.root,manifest_path=self.manifest(),profile='engineering').report()['artifact_verified'])
        path=self.manifest();build=BuildIdentity(self.root,manifest_path=path,profile='native')
        path.write_text('{}',encoding='utf-8')
        self.assertIn('BUILD_MANIFEST_CHANGED',build.report()['reasons'])

    def test_path_escape_and_unknown_manifest_fields_are_refused(self):
        from engineering.local_app.build_identity import BuildIdentity
        path=self.manifest(files={'../outside.py':'0'*64})
        self.assertEqual(BuildIdentity(self.root,manifest_path=path).report()['status'],'BLOCK')
        path=self.manifest(engineering_verified=True)
        self.assertEqual(BuildIdentity(self.root,manifest_path=path).report()['status'],'BLOCK')

    def test_actual_http_and_worker_share_build_receipt(self):
        from engineering.local_app.build_identity import BuildIdentity
        from engineering.local_app.store import Store
        from engineering.local_app.server import make_server
        from engineering.local_app.worker import Worker
        class Model:
            def chat(self,messages):return 'Controlled result'
        store=Store(self.root/'data');store.runtime_build=BuildIdentity(self.root,manifest_path=self.manifest())
        model=Model();server=make_server(store,model,port=0,drive_client=None)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        try:
            conn=HTTPConnection('127.0.0.1',server.server_port,timeout=5)
            conn.request('GET','/api/build',headers={'X-Engineer-Token':server.token})
            response=conn.getresponse();data=json.loads(response.read());conn.close()
            self.assertEqual(response.status,200)
            from scripts.check_running_build import check_running_build
            self.assertTrue(check_running_build(server.origin,store.runtime_build.report())['match'])
            wrong=dict(data,source_sha256='0'*64)
            self.assertFalse(check_running_build(server.origin,wrong)['match'])
            wrong=dict(data,data_root_sha256='0'*64)
            self.assertFalse(check_running_build(server.origin,wrong)['match'])
            conn=HTTPConnection('127.0.0.1',server.server_port,timeout=5)
            conn.request('GET','/')
            response=conn.getresponse();html=response.read().decode('utf-8');conn.close()
            self.assertTrue('id="build-status"' in html,'Build identity is missing from the page')
            sid=store.create_session()['id'];job=store.enqueue(sid,'Check',[])
            Worker(store,model).run_once()
            result=store.snapshot(sid)['jobs'][0]['result']
            self.assertEqual(result['runtime_build']['manifest_sha256'],data['manifest_sha256'])
            self.assertEqual(result['runtime_build']['tree_sha'],data['tree_sha'])
        finally:
            server.shutdown();server.server_close();thread.join(5)

import hashlib
import importlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from engineering.local_app.store import Store
from engineering.storage.google_drive import GoogleDriveClient


class Response:
    def __init__(self, data):self.stream=io.BytesIO(data)
    def __enter__(self):return self
    def __exit__(self,*args):pass
    def read(self,size=-1):return self.stream.read(size)


class Token:
    def access_token(self):return 'PRIVATE_TOKEN'


class LocalDriveImportTests(unittest.TestCase):
    def setUp(self):
        try:self.module=importlib.import_module('engineering.local_app.drive_import')
        except ModuleNotFoundError:self.fail('Local Drive import missing')
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.store=Store(Path(self.tmp.name));self.session=self.store.create_session()['id']
        self.data='Исходник: высота 4 м'.encode()
        self.meta=dict(id='drive_original_123',name='report.md',mimeType='text/markdown',size=str(len(self.data)),
                       md5Checksum=hashlib.md5(self.data).hexdigest(),modifiedTime='2026-10-06T00:00:00Z',
                       capabilities=dict(canDownload=True),trashed=False)
        self.calls=[];self.metadata_count=0;self.corrupt=False;self.change=False

        def opener(req,timeout):
            self.calls.append(req.full_url)
            if 'alt=media' in req.full_url:return Response(b'x'*len(self.data) if self.corrupt else self.data)
            self.metadata_count+=1
            meta=dict(self.meta)
            if self.change and self.metadata_count>=3:meta['modifiedTime']='2026-10-06T00:01:00Z'
            return Response(json.dumps(meta).encode())

        self.client=GoogleDriveClient(Token(),opener)

    def run_import(self,**kwargs):
        return self.module.import_original(self.store,self.session,self.client,'drive_original_123',**kwargs)

    def test_import_preserves_bytes_sha_and_source_history(self):
        sha=hashlib.sha256(self.data).hexdigest()
        result=self.run_import(expected_sha256=sha)
        file=self.store.get_file(result['id'])
        self.assertEqual(Path(file['path']).read_bytes(),self.data)
        self.assertEqual(file['sha256'],sha)
        self.assertEqual(file['source_metadata']['drive_file_id'],self.meta['id'])
        self.assertEqual(file['source_metadata']['md5_checksum'],self.meta['md5Checksum'])
        self.assertFalse(file['acceptance_granted'])
        self.assertEqual(file['extraction_status'],'UNVERIFIED')
        restored=Store(Path(self.tmp.name)).snapshot(self.session)['files'][0]
        self.assertEqual(restored['source_metadata'],file['source_metadata'])
        self.assertNotIn('PRIVATE_TOKEN',json.dumps(restored))
        self.assertFalse(list(self.store.root.glob('drive-import-*')))

    def test_office_import_runs_through_same_background_analysis(self):
        from test_office_documents import docx,xlsx,Model
        from engineering.local_app.worker import Worker
        for suffix,data in [('docx',docx()),('xlsx',xlsx())]:
            self.data=data;self.meta.update(name='drive.'+suffix,mimeType='application/octet-stream',size=str(len(data)),md5Checksum=hashlib.md5(data).hexdigest())
            file=self.run_import();self.store.enqueue(self.session,'Read',[file['id']]);model=Model();Worker(self.store,model).run_once()
            job=self.store.snapshot(self.session)['jobs'][0];self.assertEqual(job['state'],'SUCCEEDED')
            self.assertEqual(job['result']['document_analysis']['sources'][0]['backend'],suffix)
            self.assertEqual(self.store.get_file(file['id'])['source_metadata']['provider'],'GOOGLE_DRIVE')

    def test_checksum_mismatch_and_source_change_leave_no_file(self):
        for mode in ('corrupt','change','expected-sha'):
            self.corrupt=mode=='corrupt';self.change=mode=='change';self.metadata_count=0
            with self.subTest(mode=mode),self.assertRaises(self.module.DriveImportError):
                self.run_import(expected_sha256='0'*64 if mode=='expected-sha' else None)
            self.assertEqual(self.store.snapshot(self.session)['files'],[])
            self.assertFalse(list(self.store.root.glob('drive-import-*')))

    def test_bad_source_permission_type_size_blocks_before_media(self):
        original=dict(self.meta)
        for changes in ({'trashed':True},{'capabilities':{'canDownload':False}},
                        {'trashed':None},{'trashed':'false'},
                        {'capabilities':{'canDownload':'false'}},
                        {'capabilities':{'canDownload':1}},
                        {'mimeType':'application/vnd.google-apps.document'},
                        {'name':'model.exe'},{'size':'104857601'},{'md5Checksum':None}):
            self.meta=dict(original,**changes);self.calls=[]
            with self.subTest(changes=changes),self.assertRaises(self.module.DriveImportError):self.run_import()
            self.assertFalse(any('alt=media' in c for c in self.calls))
        self.assertEqual(self.store.snapshot(self.session)['files'],[])

    def test_dwg_import_preserves_original_but_never_claims_parsing(self):
        from engineering.local_app.cad import inventory
        self.data=b'AC1032\x00controlled header'
        self.meta.update(name='drawing.dwg',mimeType='application/octet-stream',size=str(len(self.data)),md5Checksum=hashlib.md5(self.data).hexdigest())
        original=self.store.get_file(self.run_import()['id'])
        self.assertEqual(Path(original['path']).read_bytes(),self.data)
        self.assertEqual(original['extraction_status'],'UNAVAILABLE')
        self.assertFalse(original['acceptance_granted'])
        self.assertEqual(inventory(self.store,self.session,original['id'])['status'],'BLOCK')

    def test_url_parser_rejects_arbitrary_hosts_paths_and_bad_ids(self):
        self.assertEqual(self.module.drive_file_id('https://drive.google.com/file/d/drive_original_123/view?usp=sharing'),'drive_original_123')
        self.assertEqual(self.module.drive_file_id('https://drive.google.com/open?id=drive_original_123'),'drive_original_123')
        for value in ('https://evil.example/file/d/drive_original_123/view','http://127.0.0.1:1234','https://drive.google.com@evil.example/file/d/drive_original_123', '../x',[],None):
            with self.subTest(value=value),self.assertRaises(ValueError):self.module.drive_file_id(value)

    def test_unknown_conversation_and_unconfigured_client_never_download(self):
        with self.assertRaises(ValueError):self.module.import_original(self.store,'bad',self.client,'drive_original_123')
        with self.assertRaises(self.module.DriveImportError):self.module.import_original(self.store,self.session,None,'drive_original_123')
        self.assertEqual(self.calls,[])

    def test_transport_rejects_redirect_and_non_google_destination(self):
        from urllib.request import Request
        opener=self.module.GoogleOnlyTransport()
        for url in ('http://oauth2.googleapis.com/token','https://evil.example/drive/v3/files/x','https://www.googleapis.com/other','https://www.googleapis.com@evil.example/drive/v3/files/x'):
            with self.subTest(url=url),self.assertRaises(ValueError):opener(Request(url),30)
        self.assertIsNone(self.module.NoRedirect().redirect_request(None,None,None,None,None,None))

    def test_absent_oauth_is_not_marked_connected(self):
        with patch.dict('os.environ',{},clear=True):
            self.assertIsNone(self.module.configured_client())

    def test_temp_cleanup_failure_cannot_report_failure_after_import_commit(self):
        original=self.module.tempfile.TemporaryDirectory
        class BrokenCleanup:
            def __init__(inner,*args,**kwargs):inner.folder=original(*args,**kwargs)
            def __enter__(inner):return inner.folder.__enter__()
            def __exit__(inner,*args):
                inner.folder.__exit__(*args)
                raise OSError('private cleanup failure')
        with patch.object(self.module.tempfile,'TemporaryDirectory',BrokenCleanup):
            with self.assertRaises(self.module.DriveImportError):self.run_import()
        self.assertEqual(self.store.snapshot(self.session)['files'],[])

    def test_legacy_file_metadata_migrates_without_losing_original(self):
        from engineering.local_app.files import preserve_file
        file=preserve_file(self.store,self.session,'legacy.txt',b'legacy')
        with self.store.connection() as db:db.execute('ALTER TABLE files DROP COLUMN source_metadata')
        restored=Store(self.store.root).get_file(file['id'])
        self.assertEqual(restored['source_metadata'],{})
        self.assertEqual(Path(restored['path']).read_bytes(),b'legacy')


if __name__=='__main__':unittest.main()

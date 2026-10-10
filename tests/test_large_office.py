import io
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch
from engineering.local_app import files,office
from engineering.local_app.store import Store
from tests import test_local_app_http as http_fixture
from tests import test_office_documents as office_fixture


class LargeOfficeTests(unittest.TestCase):
    def test_office_upload_has_separate_limit_without_relaxing_other_formats(self):
        limit=getattr(files,'file_limit',lambda name:files.MAX_FILE_BYTES)
        self.assertEqual(limit('report.DOCX'),256*1024*1024)
        self.assertEqual(limit('table.xlsx'),256*1024*1024)
        self.assertEqual(limit('report.docx.exe'),100*1024*1024)
        with tempfile.TemporaryDirectory() as root,patch.object(files,'MAX_FILE_BYTES',4):
            store=Store(Path(root));sid=store.create_session()['id']
            f=files.preserve_file(store,sid,'report.docx',b'original')
            self.assertEqual(Path(store.get_file(f['id'])['path']).read_bytes(),b'original')
            with self.assertRaises(ValueError):files.preserve_file(store,sid,'report.pdf',b'original')

    def test_unread_media_do_not_consume_xml_expansion_budget(self):
        stream=io.BytesIO()
        with zipfile.ZipFile(stream,'w',zipfile.ZIP_DEFLATED) as z:
            z.writestr('word/document.xml',b'<root/>');z.writestr('word/media/image.bin',b'\0'*(33*1024*1024))
        p=None
        try:
            try:p=office.Package(stream.getvalue())
            except office.OfficeError as e:self.fail('Unread media blocked bounded XML: '+str(e))
            self.assertEqual(p.xml('word/document.xml').tag,'root')
        finally:
            if p:p.close()

    def test_main_xml_above_old_eight_mib_limit_is_read_within_new_bound(self):
        stream=io.BytesIO()
        with zipfile.ZipFile(stream,'w',zipfile.ZIP_DEFLATED) as z:z.writestr('word/document.xml',b'<root>'+b' '*(9*1024*1024)+b'</root>')
        p=office.Package(stream.getvalue())
        try:
            try:self.assertEqual(p.xml('word/document.xml').tag,'root')
            except office.OfficeError as e:self.fail('Bounded main XML blocked: '+str(e))
        finally:p.close()


class LargeOfficeHTTPTests(unittest.TestCase):
    setUp=http_fixture.LocalHTTPTests.setUp
    close=http_fixture.LocalHTTPTests.close
    request=http_fixture.LocalHTTPTests.request
    create=http_fixture.LocalHTTPTests.create

    def test_authenticated_upload_uses_same_extension_limit_as_preservation(self):
        sid=self.create()
        with patch.object(files,'MAX_FILE_BYTES',4):
            status,_,_=self.request('POST',f'/api/sessions/{sid}/files?name=full.docx',b'original',headers={'Content-Type':'application/octet-stream'})
            self.assertEqual(status,201)
            status,_,_=self.request('POST',f'/api/sessions/{sid}/files?name=full.pdf',b'original',headers={'Content-Type':'application/octet-stream'})
            self.assertEqual(status,413)


class OfficeSnapshotTests(unittest.TestCase):
    setUp=office_fixture.OfficeTests.setUp

    def extract(self,progress=None):
        import threading
        from engineering.local_app.extraction import execute
        f=files.preserve_file(self.store,self.session,'report.docx',office_fixture.docx())
        self.store.enqueue(self.session,'Read',[f['id']]);parent=self.store.claim()
        child,_=self.store.automatic_extraction(parent,f['id'],'docx')
        return execute(self.store,child,threading.Event(),progress=progress),f

    def test_original_hash_checks_are_bounded_per_run_not_per_unit(self):
        from engineering.local_app import core_plan
        with patch.object(core_plan,'verify_originals',wraps=core_plan.verify_originals) as check:
            result,_=self.extract()
        self.assertLessEqual(check.call_count,3)
        self.assertEqual(result['extraction']['processed_units'],4)

    def test_mutated_original_is_rejected_before_next_unit(self):
        from engineering.local_app.extraction import ExtractionFailure
        changed=False
        def mutate(run):
            nonlocal changed
            if run['processed_units'] and not changed:
                changed=True;f=self.store.get_file(run['file_id']);Path(f['path']).write_bytes(b'changed')
        with self.assertRaises((ValueError,ExtractionFailure)):self.extract(mutate)

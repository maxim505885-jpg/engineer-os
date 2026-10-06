import tempfile
import unittest
from pathlib import Path
from engineering.local_app.store import Store
from engineering.local_app.files import preserve_file

class LocalEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.store=Store(self.tmp.name);self.session=self.store.create_session()['id']
        self.file=preserve_file(self.store,self.session,'source.txt','Высота 4 м. <script>alert(1)</script>'.encode())

    def add(self,**kwargs):
        try:
            from engineering.local_app.evidence import register
        except ImportError:self.fail('Local evidence register missing')
        args=dict(file_id=self.file['id'],quote='Высота 4 м.',statement='Высота по документу',page=None,data_class='U');args.update(kwargs)
        return register(self.store,self.session,**args)

    def test_match_is_durable_but_never_engineering_acceptance(self):
        record=self.add(data_class='M')
        self.assertEqual(record['source_match'],'MATCH')
        self.assertEqual(record['source_sha256'],self.file['sha256'])
        self.assertEqual(record['data_class'],'M')
        self.assertEqual(record['status'],'UNVERIFIED')
        self.assertFalse(record['acceptance_granted'])
        self.assertEqual(Store(self.tmp.name).snapshot(self.session)['evidence'][0]['id'],record['id'])

    def test_invented_quote_and_page_for_text_are_rejected(self):
        for args in [dict(quote='Высота 99 м'),dict(page=1),dict(data_class='ACCEPTED'),dict(page=True)]:
            with self.assertRaises(ValueError):self.add(**args)
        self.assertEqual(self.store.snapshot(self.session)['evidence'],[])

    def test_foreign_original_and_changed_bytes_are_rejected(self):
        other=self.store.create_session()['id'];f=preserve_file(self.store,other,'other.txt',b'123')
        with self.assertRaises(ValueError):self.add(file_id=f['id'],quote='123')
        Path(self.store.get_file(self.file['id'])['path']).write_bytes(b'changed')
        with self.assertRaises(ValueError):self.add()

    def test_pdf_quote_is_bound_to_actual_page_not_first_20_candidates(self):
        import fitz
        with fitz.open() as pdf:
            for i in range(21):pdf.new_page().insert_text((20,30),f'PAGE {i+1} 123.45')
            data=pdf.tobytes()
        f=preserve_file(self.store,self.session,'source.pdf',data)
        r=self.add(file_id=f['id'],page=21,quote='PAGE 21 123.45')
        self.assertEqual(r['source_match'],'MATCH');self.assertEqual(r['page'],21)
        for page in (1,22,None):
            with self.assertRaises(ValueError):self.add(file_id=f['id'],page=page,quote='PAGE 21 123.45')

    def test_unreadable_pdf_keeps_candidate_explicitly_unchecked(self):
        f=preserve_file(self.store,self.session,'scan.pdf',b'broken-pdf')
        r=self.add(file_id=f['id'],page=1,quote='Указанный пользователем фрагмент')
        self.assertEqual(r['source_match'],'NOT_CHECKED');self.assertEqual(r['status'],'UNVERIFIED')
        self.assertFalse(r['acceptance_granted'])

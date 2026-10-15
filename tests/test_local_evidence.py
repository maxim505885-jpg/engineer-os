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

    def pdf_file(self,lines):
        import fitz
        with fitz.open() as pdf:
            page=pdf.new_page()
            for i,line in enumerate(lines):page.insert_text((40,40+i*30),line)
            data=pdf.tobytes()
        return preserve_file(self.store,self.session,'located.pdf',data)

    def test_unique_pdf_quote_has_coordinates_and_source_binding_gate_only(self):
        f=self.pdf_file(['height 4m'])
        r=self.add(file_id=f['id'],page=1,quote='height 4m')
        self.assertIn('provenance',r,'Native quote provenance missing')
        p=r['provenance'];self.assertEqual(p['status'],'UNIQUE')
        self.assertEqual(p['coordinate_system'],'unrotated_page_points_top_left')
        box=p['regions'][0];self.assertLess(box['left'],box['right']);self.assertLess(box['top'],box['bottom'])
        self.assertEqual(r['document_validation']['status'],'VALIDATED')
        self.assertEqual(r['document_validation']['scope'],'SOURCE_BINDING_ONLY')
        self.assertFalse(r['acceptance_granted']);self.assertEqual(r['status'],'UNVERIFIED')
        self.assertEqual(Store(self.tmp.name).snapshot(self.session)['evidence'][0]['provenance'],p)

    def test_repeated_quote_is_ambiguous_without_validated_candidate(self):
        f=self.pdf_file(['height 4m','height 4m'])
        r=self.add(file_id=f['id'],page=1,quote='height 4m')
        self.assertIn('provenance',r,'Ambiguous provenance missing')
        self.assertEqual(r['provenance']['status'],'AMBIGUOUS')
        self.assertEqual(len(r['provenance']['regions']),2)
        self.assertEqual(r['document_validation']['status'],'BLOCK')
        self.assertIsNone(r['document_validation']['candidate_id'])

    def test_multiline_quote_does_not_claim_single_verified_location(self):
        f=self.pdf_file(['height 4m','width 6m'])
        r=self.add(file_id=f['id'],page=1,quote='height 4m\nwidth 6m')
        self.assertIn('provenance',r,'Multiline provenance missing')
        self.assertNotEqual(r['provenance']['status'],'UNIQUE')
        self.assertEqual(r['document_validation']['status'],'BLOCK')

    def test_text_sources_have_no_invented_pdf_coordinates(self):
        r=self.add();self.assertIn('provenance',r,'Non-PDF provenance missing')
        self.assertEqual(r['provenance']['status'],'NOT_APPLICABLE')
        self.assertEqual(r['provenance']['regions'],[])
        self.assertEqual(r['document_validation']['status'],'BLOCK')

    def test_rotated_pdf_keeps_unrotated_coordinates_and_rotation_metadata(self):
        import fitz
        with fitz.open() as pdf:
            page=pdf.new_page();page.insert_text((40,40),'rotation 90');page.set_rotation(90);data=pdf.tobytes()
        f=preserve_file(self.store,self.session,'rotated.pdf',data)
        r=self.add(file_id=f['id'],page=1,quote='rotation 90')
        p=r['provenance'];self.assertEqual(p['status'],'UNIQUE');self.assertEqual(p['page_rotation'],90)
        self.assertAlmostEqual(p['regions'][0]['left'],40,places=2)
        self.assertLess(p['page_width'],p['page_height'])

    def test_case_insensitive_merged_search_rect_cannot_validate_exact_quote(self):
        f=self.pdf_file(['abcABC'])
        r=self.add(file_id=f['id'],page=1,quote='abc')
        self.assertEqual(r['provenance']['status'],'AMBIGUOUS')
        self.assertEqual(r['document_validation']['status'],'BLOCK')

    def test_overlapping_occurrences_are_ambiguous(self):
        f=self.pdf_file(['ababa'])
        r=self.add(file_id=f['id'],page=1,quote='aba')
        self.assertEqual(r['provenance']['exact_occurrences'],2)
        self.assertEqual(r['provenance']['status'],'AMBIGUOUS')
        self.assertEqual(r['document_validation']['status'],'BLOCK')

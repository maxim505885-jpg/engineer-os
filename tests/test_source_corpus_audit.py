import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import zipfile


class SourceCorpusAuditTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)/'sources';self.root.mkdir()

    def pdf(self,name='source.pdf'):
        import fitz
        path=self.root/name
        with fitz.open() as doc:
            doc.new_page().insert_text((30,50),'Declared height 4000 mm')
            doc.new_page()
            doc.save(path)
        return path

    def test_recursive_snapshot_includes_ignored_formats_and_excludes_owner_as_content(self):
        from engineering.document_intelligence.corpus_audit import audit_corpus
        self.pdf();nested=self.root/'nested';nested.mkdir()
        (nested/'model.dwg').write_bytes(b'AC1032 original')
        (nested/'model.lir').write_bytes(b'not semantically decoded')
        (nested/'~$report.docx').write_bytes(b'owner metadata')
        result=audit_corpus(self.root)
        self.assertEqual(result['file_count'],4)
        self.assertEqual(result['pdf_pages'],2)
        self.assertEqual(result['extensions'],{'.pdf':1,'.dwg':1,'.lir':1,'.docx':1})
        owner=next(f for f in result['files'] if f['relative'].endswith('~$report.docx'))
        self.assertEqual(owner['role'],'TEMPORARY_OWNER_FILE')
        pdf=next(f for f in result['files'] if f['extension']=='.pdf')
        self.assertEqual(pdf['native_empty_pages'],[2])
        self.assertFalse(result['complete_document_set'])
        self.assertFalse(result['acceptance_granted'])
        self.assertTrue(result['originals_unchanged'])

    def test_corrupt_docx_and_pdf_remain_blocked_originals(self):
        from engineering.document_intelligence.corpus_audit import audit_corpus
        for name in ('broken.docx','broken.pdf'):(self.root/name).write_bytes(b'broken original')
        result=audit_corpus(self.root)
        self.assertEqual(result['status'],'BLOCK')
        self.assertTrue(all(f['status']=='BLOCK' for f in result['files']))
        self.assertTrue(all((self.root/f['relative']).read_bytes()==b'broken original' for f in result['files']))

    def test_expected_identity_mismatch_never_parses_source(self):
        from engineering.document_intelligence.corpus_audit import audit_corpus
        source=self.pdf()
        with patch('scripts.pdf_layer_census.inventory',side_effect=AssertionError('must not parse')):
            result=audit_corpus(self.root,expected_manifest={'source.pdf':'0'*64})
        self.assertIn('SOURCE_IDENTITY_MISMATCH',result['files'][0]['reasons'])

    def test_documented_counts_never_equal_layout_qualification(self):
        from engineering.document_intelligence.corpus_audit import audit_corpus
        path=self.root/'source.docx'
        with zipfile.ZipFile(path,'w') as z:
            z.writestr('word/document.xml','<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>source</w:t></w:r></w:p></w:body></w:document>')
        result=audit_corpus(self.root)
        self.assertEqual(result['docx_logical_units'],1)
        self.assertEqual(result['files'][0]['completeness'],'NOT_VERIFIED')
        self.assertIn('LAYOUT_NOT_VERIFIED',result['files'][0]['limitations'])

    def test_corpus_changed_during_inspection_is_detected(self):
        from engineering.document_intelligence.corpus_audit import audit_corpus
        source=self.pdf()
        def changed(path):
            (self.root/'added.lir').write_bytes(b'new input')
            return dict(page_count=2,native_empty_pages=[2],pages_with_embedded_images=0,pages=[])
        with patch('scripts.pdf_layer_census.inventory',side_effect=changed):result=audit_corpus(self.root)
        self.assertFalse(result['source_tree_unchanged'])
        self.assertIn('SOURCE_TREE_CHANGED',result['reasons'])

    def test_earlier_source_changed_during_later_inspection_is_detected(self):
        from engineering.document_intelligence.corpus_audit import audit_corpus
        earlier=self.root/'a.lir';earlier.write_bytes(b'original model')
        source=self.pdf('z.pdf')
        def changed(path):
            earlier.write_bytes(b'changed model')
            return dict(sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                        page_count=2,native_empty_pages=[2],pages_with_embedded_images=0,pages=[])
        with patch('scripts.pdf_layer_census.inventory',side_effect=changed):
            result=audit_corpus(self.root)
        self.assertFalse(result['originals_unchanged'])
        row=next(x for x in result['files'] if x['relative']=='a.lir')
        self.assertFalse(row['original_unchanged'])
        self.assertIn('SOURCE_CHANGED_DURING_AUDIT',row['reasons'])
        self.assertIn('SOURCE_CONTENT_CHANGED',result['reasons'])

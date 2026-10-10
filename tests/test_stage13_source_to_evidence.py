"""Verify source-bound extracted table candidates through real evidence gate.

This test does not assert visual cell correctness or binary OMML/media preservation.
"""
import hashlib
import tempfile
import unittest
import zipfile
from pathlib import Path

from engineering.document_intelligence.contracts import (
    DocumentBlock, NormalizedDocument, PageRef,
)
from engineering.document_intelligence.document_registration import SourceDocumentIdentity
from engineering.document_intelligence.pipeline import prepare_validated_evidence
from scripts.stage13_source_evidence_replay import replay


class AcceptingIdentityVerifier:
    def verify(self, identity):
        if not identity.document_id or not identity.project_id:
            raise ValueError('Missing registered identity')


class Stage13SourceToEvidenceTests(unittest.TestCase):
    def test_source_table_data_reaches_validated_candidates(self):
        import fitz
        with tempfile.TemporaryDirectory() as folder:
            pdf=Path(folder)/'source.pdf'
            docx=Path(folder)/'source.docx'
            document=fitz.open()
            page=document.new_page()
            page.insert_text((40,40),'Source table header')
            document.save(pdf)
            document.close()
            with zipfile.ZipFile(docx,'w') as archive:
                archive.writestr('word/document.xml',b'<document/>')
            source=replay(pdf,docx,pages=[1])
            sha=source['sources']['pdf_sha256']
            block=DocumentBlock(block_id='p1-text',kind='text',
                text='Source table header',provenance=(PageRef(page_no=1),))
            normalized=NormalizedDocument(source_path=str(pdf),parser='stage13-test-fixture',
                blocks=(block,),source_sha256=sha)
            identity=SourceDocumentIdentity(project_id='project',document_id='document',source_sha256=sha)
            candidates=prepare_validated_evidence(normalized,identity,AcceptingIdentityVerifier())
            self.assertEqual(len(candidates),1)
            self.assertEqual(candidates[0].text,block.text)
            self.assertEqual(candidates[0].page_numbers,(1,))
            self.assertEqual(candidates[0].source_sha256,sha)

    def test_source_identity_mismatch_blocks_pipeline(self):
        import fitz
        with tempfile.TemporaryDirectory() as folder:
            pdf=Path(folder)/'source.pdf'
            document=fitz.open()
            document.new_page()
            document.save(pdf)
            document.close()
            sha=hashlib.sha256(pdf.read_bytes()).hexdigest()
            block=DocumentBlock(block_id='p1',kind='text',text='Cell',
                                provenance=(PageRef(page_no=1),))
            normalized=NormalizedDocument(source_path=str(pdf),parser='test',
                blocks=(block,),source_sha256=sha)
            wrong=SourceDocumentIdentity(project_id='p',document_id='d',source_sha256='0'*64)
            with self.assertRaisesRegex(ValueError,'checksum'):
                prepare_validated_evidence(normalized,wrong,AcceptingIdentityVerifier())


if __name__=='__main__':
    unittest.main()

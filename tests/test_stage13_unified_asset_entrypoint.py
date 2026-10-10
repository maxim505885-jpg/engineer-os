import hashlib
import tempfile
import unittest
import zipfile
from pathlib import Path
from uuid import uuid4

from engineering.document_intelligence import persist_selected_unverified_asset
from engineering.document_intelligence.docx_asset_ingestion import source_assets


class Stage13UnifiedAssetEntrypointTests(unittest.TestCase):
    def test_exact_docx_source_candidate_reaches_uncertainty_transport(self):
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)/'report.docx'
            with zipfile.ZipFile(source,'w') as z:
                z.writestr('word/document.xml',b'<document/>')
                z.writestr('word/media/figure.emf',b'EMF source bytes')
            item=source_assets(source)[0]
            saved=[]
            def transport(candidate,project_id,document_id):
                self.assertFalse(candidate.verified)
                saved.append(candidate)
                return 'candidate-id'
            result=persist_selected_unverified_asset(
                str(source),item.source_sha256,item.candidate_id,
                str(uuid4()),str(uuid4()),transport=transport)
            self.assertEqual(result,'candidate-id')
            self.assertEqual(saved[0].asset_sha256,item.asset_sha256)

    def test_identity_mismatch_fails_before_transport(self):
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)/'report.docx'
            with zipfile.ZipFile(source,'w') as z:
                z.writestr('word/document.xml',b'<document/>')
                z.writestr('word/media/a.png',b'asset')
            item=source_assets(source)[0]
            recorded=[]
            with self.assertRaisesRegex(ValueError,'SOURCE_IDENTITY_MISMATCH'):
                persist_selected_unverified_asset(
                    str(source),'0'*64,item.candidate_id,str(uuid4()),str(uuid4()),
                    transport=lambda *args: recorded.append(args))
            self.assertEqual(recorded,[])

    def test_pdf_requires_page_and_only_asset_ids(self):
        with self.assertRaisesRegex(ValueError,'ASSET_CANDIDATE_ID_REQUIRED'):
            persist_selected_unverified_asset('report.pdf','a'*64,'doc-evidence:x',
                str(uuid4()),str(uuid4()),transport=lambda *args: None)
        with self.assertRaisesRegex(ValueError,'PDF_ASSET_PAGE_REQUIRED'):
            persist_selected_unverified_asset('report.pdf','a'*64,'doc-asset:x',
                str(uuid4()),str(uuid4()),transport=lambda *args: None)


if __name__=='__main__':
    unittest.main()

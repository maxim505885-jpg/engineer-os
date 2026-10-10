import hashlib
import tempfile
import unittest
import zipfile
from pathlib import Path
from engineering.document_intelligence.asset_evidence_validation import (
    prepare_docx_asset_candidates,validate_asset_source
)


class AssetEvidenceValidationTests(unittest.TestCase):
    def test_registered_source_yields_unverified_payloads(self):
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)/'source.docx'
            xml=b'<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math"><w:body><m:oMath/></w:body></w:document>'
            with zipfile.ZipFile(source,'w') as archive:
                archive.writestr('word/document.xml',xml)
                archive.writestr('word/media/a.emf',b'emf')
            sha=hashlib.sha256(source.read_bytes()).hexdigest()
            candidates=prepare_docx_asset_candidates(source,sha)
            self.assertEqual(len(candidates),2)
            media=next(item for item in candidates if item.asset_kind=='emf_graphic')
            result=validate_asset_source(media,b'emf',sha)
            self.assertEqual(result.status,'UNCERTAINTY')
            self.assertEqual(result.reason,'SEMANTIC_VISUAL_REVIEW_REQUIRED')
            self.assertFalse(media.verified)

    def test_wrong_registered_source_blocks(self):
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)/'source.docx'
            with zipfile.ZipFile(source,'w') as archive:
                archive.writestr('word/document.xml',b'<document/>')
            with self.assertRaisesRegex(ValueError,'SOURCE_IDENTITY_MISMATCH'):
                prepare_docx_asset_candidates(source,'0'*64)


if __name__=='__main__':
    unittest.main()

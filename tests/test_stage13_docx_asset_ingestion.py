import hashlib
import tempfile
import unittest
import zipfile
from pathlib import Path

from engineering.document_intelligence.docx_asset_ingestion import source_assets


class DocxAssetIngestionTests(unittest.TestCase):
    def test_omml_and_emf_preserve_exact_source_hash(self):
        with tempfile.TemporaryDirectory() as dirname:
            source=Path(dirname)/'sample.docx'
            xml=b'<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math"><w:body><m:oMath><m:r/></m:oMath></w:body></w:document>'
            with zipfile.ZipFile(source,'w') as archive:
                archive.writestr('word/document.xml',xml)
                archive.writestr('word/media/drawing.emf',b'EMF bytes')
                archive.writestr('word/media/image.png',b'PNG bytes')
            assets=source_assets(source)
            self.assertEqual(len(assets),3)
            self.assertEqual({x.asset_kind for x in assets},{'omml_formula','emf_graphic','embedded_image'})
            self.assertTrue(all(x.source_sha256==hashlib.sha256(source.read_bytes()).hexdigest() for x in assets))
            self.assertTrue(all(not x.verified for x in assets))
            emf=next(x for x in assets if x.asset_kind=='emf_graphic')
            self.assertEqual(emf.asset_sha256,hashlib.sha256(b'EMF bytes').hexdigest())

    def test_changed_zip_has_different_source_identity(self):
        with tempfile.TemporaryDirectory() as dirname:
            source=Path(dirname)/'sample.docx'
            with zipfile.ZipFile(source,'w') as archive:
                archive.writestr('word/document.xml',b'<document/>')
                archive.writestr('word/media/a.emf',b'original')
            old=source_assets(source)[0]
            with zipfile.ZipFile(source,'a') as archive:
                archive.writestr('word/media/b.png',b'new')
            self.assertNotEqual(source_assets(source)[0].source_sha256,old.source_sha256)


if __name__=='__main__':
    unittest.main()

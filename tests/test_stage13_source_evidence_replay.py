import tempfile
import unittest
import zipfile
from pathlib import Path
from scripts.stage13_source_evidence_replay import replay


class SourceEvidenceReplayTests(unittest.TestCase):
    def test_real_source_structures_never_auto_accept(self):
        import fitz
        with tempfile.TemporaryDirectory() as folder:
            base=Path(folder)
            pdf=base/'sample.pdf'
            docx=base/'sample.docx'
            d=fitz.open()
            page=d.new_page()
            page.insert_text((20,30),'Table heading')
            d.save(pdf)
            d.close()
            math_xml=b'<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math"><w:body><m:oMath><m:r/></m:oMath></w:body></w:document>'
            with zipfile.ZipFile(docx,'w') as z:
                z.writestr('word/document.xml',math_xml)
                z.writestr('word/media/image.png',b'example media')
            result=replay(pdf,docx,pages=[1])
            self.assertEqual(result['pdf_pages'],1)
            self.assertEqual(result['docx']['omml_count'],1)
            self.assertEqual(result['docx']['media_count'],1)
            self.assertFalse(result['docx']['downstream_preservation_proven'])
            self.assertEqual(result['module_gate_status'],'BLOCK')

    def test_bad_page_number_is_rejected(self):
        import fitz
        with tempfile.TemporaryDirectory() as folder:
            pdf=Path(folder)/'a.pdf'
            docx=Path(folder)/'b.docx'
            d=fitz.open()
            d.new_page()
            d.save(pdf)
            d.close()
            with zipfile.ZipFile(docx,'w') as z:
                z.writestr('word/document.xml',b'<document/>')
            with self.assertRaises(ValueError):
                replay(pdf,docx,pages=[2])


if __name__=='__main__':
    unittest.main()

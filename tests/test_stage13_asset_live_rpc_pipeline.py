import hashlib
import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from uuid import uuid4

from engineering.document_intelligence.asset_candidate_pipeline import (
    persist_selected_docx_asset,persist_selected_pdf_table
)
from engineering.document_intelligence.docx_asset_ingestion import source_assets
from engineering.document_intelligence.pdf_table_asset_ingestion import pdf_table_candidates
from engineering.document_intelligence.supabase_asset_candidate_transport import (
    SupabaseAssetCandidateTransport
)


class FakeHTTPResponse:
    def __enter__(self):
        return self
    def __exit__(self,*args):
        return False
    def read(self):
        return b'"00000000-0000-4000-8000-000000000001"'


class AssetCandidatePipelineTests(unittest.TestCase):
    def test_docx_real_bytes_to_selected_transport(self):
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)/'source.docx'
            xml=b'<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math"><w:body><m:oMath><m:r/></m:oMath></w:body></w:document>'
            with zipfile.ZipFile(source,'w') as archive:
                archive.writestr('word/document.xml',xml)
                archive.writestr('word/media/picture.emf',b'real-emf-bytes')
            sha=hashlib.sha256(source.read_bytes()).hexdigest()
            items=source_assets(source)
            recorded=[]
            def capture(candidate,project_id,document_id):
                recorded.append(candidate)
                return 'stored'
            for item in items:
                result=persist_selected_docx_asset(source,sha,item.candidate_id,
                    str(uuid4()),str(uuid4()),capture)
                self.assertEqual(result,'stored')
            self.assertEqual(len(recorded),2)
            self.assertTrue(all(not item.verified for item in recorded))
            with self.assertRaisesRegex(ValueError,'SOURCE_IDENTITY_MISMATCH'):
                persist_selected_docx_asset(source,'f'*64,items[0].candidate_id,
                    str(uuid4()),str(uuid4()),capture)
            self.assertEqual(len(recorded),2)

    def test_pdf_real_table_bytes_to_selected_transport(self):
        import fitz
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)/'table.pdf'
            doc=fitz.open(); page=doc.new_page(width=400,height=400)
            shape=page.new_shape()
            for x in (20,130,240): shape.draw_line((x,50),(x,150))
            for y in (50,100,150): shape.draw_line((20,y),(240,y))
            shape.finish(color=(0,0,0));shape.commit()
            for xy,word in [((40,80),'A1'),((145,80),'B1'),((40,130),'A2'),((145,130),'B2')]:
                page.insert_text(xy,word)
            doc.save(source);doc.close()
            sha=hashlib.sha256(source.read_bytes()).hexdigest()
            candidate,payload=pdf_table_candidates(source,[1])[0]
            captured=[]
            result=persist_selected_pdf_table(source,sha,1,candidate.candidate_id,
                str(uuid4()),str(uuid4()),lambda c,p,d: captured.append(c) or 'stored')
            self.assertEqual(result,'stored')
            self.assertEqual(captured[0].asset_sha256,hashlib.sha256(payload).hexdigest())
            self.assertFalse(captured[0].verified)

    def test_http_rpc_does_not_use_validated_text_route(self):
        received=[]
        def opener(req,timeout):
            received.append((req.full_url,json.loads(req.data)))
            return FakeHTTPResponse()
        import hashlib
        from engineering.document_intelligence.asset_provenance import DocumentAssetEvidence
        candidate=DocumentAssetEvidence(source_sha256='a'*64,
            asset_sha256=hashlib.sha256(b'asset').hexdigest(),asset_kind='embedded_image',
            location='word/media/pic.png')
        transport=SupabaseAssetCandidateTransport('https://example.supabase.co','fake-service-key',opener)
        self.assertEqual(transport(candidate,str(uuid4()),str(uuid4())),
                         '00000000-0000-4000-8000-000000000001')
        self.assertTrue(received[0][0].endswith('/rest/v1/rpc/persist_unverified_document_asset_candidate'))
        self.assertTrue(received[0][1]['p_candidate_id'].startswith('doc-asset:'))


if __name__=='__main__':
    unittest.main()

import hashlib
import unittest
from uuid import uuid4
from engineering.document_intelligence.asset_provenance import DocumentAssetEvidence
from engineering.document_intelligence.evidence_persistence import EvidencePersistenceContext
from engineering.document_intelligence.uncertain_asset_register import (
    uncertain_asset_row,UncertainAssetRegisterWriter
)


class UncertainAssetRegisterTests(unittest.TestCase):
    def setUp(self):
        self.bytes=b'OMML exact XML'
        self.sha='a'*64
        self.asset=DocumentAssetEvidence(source_sha256=self.sha,
            asset_sha256=hashlib.sha256(self.bytes).hexdigest(),
            asset_kind='omml_formula',location='word/document.xml#oMath[0]')
        self.ctx=EvidencePersistenceContext(project_id=str(uuid4()),document_id=str(uuid4()))

    def test_source_bound_uncertainty_row(self):
        row=uncertain_asset_row(self.asset,self.bytes,self.sha,self.ctx)
        self.assertEqual(row['confidence'],'UNCERTAINTY')
        self.assertEqual(row['data_class'],'UNKNOWN')
        self.assertIn(self.asset.asset_sha256,row['source_ref'])
        self.assertEqual(row['evidence_code'],self.asset.candidate_id)

    def test_tampered_payload_never_inserted(self):
        inserted=[]
        writer=UncertainAssetRegisterWriter(lambda *args:inserted.append(args))
        with self.assertRaisesRegex(ValueError,'ASSET_PAYLOAD_MISMATCH'):
            writer.persist(self.asset,b'altered',self.sha,self.ctx)
        self.assertEqual(inserted,[])

    def test_injected_transport_receives_uncertain_row(self):
        calls=[]
        def insert(table,row,conflict):
            calls.append((table,row,conflict))
            return {'id':'mock'}
        response=UncertainAssetRegisterWriter(insert).persist(self.asset,self.bytes,self.sha,self.ctx)
        self.assertEqual(response['id'],'mock')
        self.assertEqual(calls[0][0],'evidence')
        self.assertEqual(calls[0][1]['confidence'],'UNCERTAINTY')


if __name__=='__main__':
    unittest.main()

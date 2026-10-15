import hashlib
import unittest
from dataclasses import FrozenInstanceError
from engineering.document_intelligence.asset_provenance import DocumentAssetEvidence, verify_payload

class AssetProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.payload=b'<m:oMath>example</m:oMath>'
        self.source='a'*64
        self.item=DocumentAssetEvidence(source_sha256=self.source,
            asset_sha256=hashlib.sha256(self.payload).hexdigest(),
            asset_kind='omml_formula', location='word/document.xml#oMath[0]')

    def test_checksum_and_location_survive(self):
        self.assertTrue(verify_payload(self.item,self.payload,self.source))
        self.assertTrue(self.item.candidate_id.startswith('doc-asset:'))
        self.assertFalse(self.item.verified)
        with self.assertRaises(FrozenInstanceError):
            self.item.asset_sha256='0'*64

    def test_wrong_media_bytes_or_document_hash_block(self):
        with self.assertRaisesRegex(ValueError,'ASSET_PAYLOAD_MISMATCH'):
            verify_payload(self.item,b'different',self.source)
        with self.assertRaisesRegex(ValueError,'SOURCE_IDENTITY_MISMATCH'):
            verify_payload(self.item,self.payload,'b'*64)

    def test_no_automatic_verified_assets(self):
        with self.assertRaisesRegex(ValueError,'cannot enter as verified'):
            DocumentAssetEvidence(source_sha256=self.source,
                asset_sha256=self.item.asset_sha256,asset_kind='emf_graphic',
                location='word/media/a.emf',verified=True)

if __name__=='__main__':
    unittest.main()

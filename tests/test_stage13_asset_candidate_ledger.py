import hashlib
import tempfile
import unittest
from pathlib import Path
from engineering.document_intelligence.asset_provenance import DocumentAssetEvidence
from engineering.document_intelligence.asset_candidate_ledger import write_candidate_ledger


class AssetCandidateLedgerTests(unittest.TestCase):
    def setUp(self):
        self.payload=b'fixture emf bytes'
        self.source='c'*64
        self.candidate=DocumentAssetEvidence(
            source_sha256=self.source,
            asset_sha256=hashlib.sha256(self.payload).hexdigest(),
            asset_kind='emf_graphic',location='word/media/drawing.emf')

    def test_unverified_manifest_durable_readback(self):
        with tempfile.TemporaryDirectory() as folder:
            output=Path(folder)/'assets.json'
            manifest=write_candidate_ledger([self.candidate],
                {self.candidate.candidate_id:self.payload},self.source,output)
            self.assertEqual(manifest['count'],1)
            self.assertEqual(manifest['records'][0]['status'],'UNCERTAINTY')
            self.assertFalse(manifest['records'][0]['visual_semantics_verified'])
            self.assertFalse(manifest['production_evidence_rpc_persisted'])
            self.assertTrue(output.is_file())

    def test_tampered_asset_does_not_create_ledger(self):
        with tempfile.TemporaryDirectory() as folder:
            output=Path(folder)/'assets.json'
            with self.assertRaisesRegex(ValueError,'ASSET_PAYLOAD_MISMATCH'):
                write_candidate_ledger([self.candidate],
                    {self.candidate.candidate_id:b'tampered'},self.source,output)
            self.assertFalse(output.exists())

    def test_missing_payload_does_not_create_ledger(self):
        with tempfile.TemporaryDirectory() as folder:
            output=Path(folder)/'assets.json'
            with self.assertRaisesRegex(ValueError,'MISSING_ASSET_PAYLOAD'):
                write_candidate_ledger([self.candidate],{},self.source,output)
            self.assertFalse(output.exists())


if __name__=='__main__':
    unittest.main()

import unittest

from engineering.document_intelligence.contracts import DocumentBlock, NormalizedDocument, PageRef
from engineering.document_intelligence.document_registration import SourceDocumentIdentity
from engineering.document_intelligence.evidence_persistence import EvidencePersistenceContext, EvidenceRegisterWriter
from engineering.document_intelligence.pipeline import prepare_validated_evidence, persist_selected_evidence


class _Verifier:
    def __init__(self):
        self.calls = []

    def verify(self, identity):
        self.calls.append(identity)


class DocumentEvidencePipelineTests(unittest.TestCase):
    def setUp(self):
        self.document = NormalizedDocument(
            "report.pdf",
            "docling",
            (
                DocumentBlock("docling:1", "text", "Факт 1", (PageRef(1),)),
                DocumentBlock("docling:2", "text", "Факт 2", (PageRef(2),)),
            ),
            "a" * 64,
        )
        self.identity = SourceDocumentIdentity(
            "11111111-1111-1111-1111-111111111111",
            "22222222-2222-2222-2222-222222222222",
            "a" * 64,
        )
        self.context = EvidencePersistenceContext(
            project_id=self.identity.project_id,
            document_id=self.identity.document_id,
        )

    def test_preparation_requires_registered_identity_and_valid_provenance(self):
        verifier = _Verifier()
        candidates = prepare_validated_evidence(self.document, self.identity, verifier)
        self.assertEqual(len(candidates), 2)
        self.assertEqual(verifier.calls, [self.identity])

    def test_hash_mismatch_blocks_before_db_verifier(self):
        verifier = _Verifier()
        bad_identity = SourceDocumentIdentity(
            self.identity.project_id, self.identity.document_id, "b" * 64
        )
        with self.assertRaises(ValueError):
            prepare_validated_evidence(self.document, bad_identity, verifier)
        self.assertEqual(verifier.calls, [])

    def test_only_explicit_selection_is_persisted(self):
        candidates = prepare_validated_evidence(self.document, self.identity, _Verifier())
        calls = []
        writer = EvidenceRegisterWriter(
            lambda table, row, conflict: calls.append(row["evidence_code"]) or row["evidence_code"]
        )
        result = persist_selected_evidence(
            self.document, candidates, (candidates[1].evidence_id,), self.context, writer
        )
        self.assertEqual(result, (candidates[1].evidence_id,))
        self.assertEqual(calls, [candidates[1].evidence_id])

    def test_empty_or_unknown_selection_blocks(self):
        candidates = prepare_validated_evidence(self.document, self.identity, _Verifier())
        writer = EvidenceRegisterWriter(lambda *args: "unexpected")
        with self.assertRaises(ValueError):
            persist_selected_evidence(self.document, candidates, (), self.context, writer)
        with self.assertRaises(ValueError):
            persist_selected_evidence(
                self.document, candidates, ("doc-evidence:" + "f" * 64,), self.context, writer
            )


if __name__ == "__main__":
    unittest.main()

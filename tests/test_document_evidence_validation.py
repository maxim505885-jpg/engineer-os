import unittest
from dataclasses import replace

from engineering.document_intelligence.contracts import DocumentBlock, NormalizedDocument, PageRef
from engineering.document_intelligence.evidence_bridge import evidence_candidates
from engineering.document_intelligence.evidence_validation import (
    EvidenceCandidateStatus,
    validate_evidence_candidate,
    validated_evidence_candidates,
)


class DocumentEvidenceValidationTests(unittest.TestCase):
    def setUp(self):
        self.document = NormalizedDocument(
            source_path="report.pdf",
            parser="docling",
            source_sha256="c" * 64,
            blocks=(DocumentBlock("docling:1", "text", "Факт из отчёта", (PageRef(9),)),),
        )
        self.candidate = evidence_candidates(self.document)[0]

    def test_valid_candidate_passes_gate(self):
        result = validate_evidence_candidate(self.document, self.candidate)
        self.assertEqual(result.status, EvidenceCandidateStatus.VALIDATED)
        self.assertEqual(validated_evidence_candidates(self.document, (self.candidate,)), (self.candidate,))

    def test_missing_page_provenance_blocks(self):
        candidate = replace(self.candidate, page_numbers=())
        result = validate_evidence_candidate(self.document, candidate)
        self.assertEqual(result.status, EvidenceCandidateStatus.BLOCK)
        self.assertIn("MISSING_PAGE_PROVENANCE", result.reasons)

    def test_source_hash_mismatch_blocks(self):
        candidate = replace(self.candidate, source_sha256="d" * 64)
        result = validate_evidence_candidate(self.document, candidate)
        self.assertEqual(result.status, EvidenceCandidateStatus.BLOCK)
        self.assertIn("SOURCE_HASH_MISMATCH", result.reasons)

    def test_content_mismatch_blocks(self):
        candidate = replace(self.candidate, text="Подменённый текст")
        result = validate_evidence_candidate(self.document, candidate)
        self.assertEqual(result.status, EvidenceCandidateStatus.BLOCK)
        self.assertIn("BLOCK_CONTENT_MISMATCH", result.reasons)

    def test_batch_gate_fails_closed_if_one_candidate_is_invalid(self):
        bad = replace(self.candidate, page_numbers=())
        with self.assertRaises(ValueError):
            validated_evidence_candidates(self.document, (self.candidate, bad))


if __name__ == "__main__":
    unittest.main()

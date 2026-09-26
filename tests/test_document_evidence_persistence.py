import unittest
from dataclasses import replace

from engineering.document_intelligence.contracts import DocumentBlock, NormalizedDocument, PageRef
from engineering.document_intelligence.evidence_bridge import evidence_candidates
from engineering.document_intelligence.evidence_persistence import (
    EvidencePersistenceContext,
    EvidenceRegisterWriter,
    evidence_row,
)


class EvidencePersistenceTests(unittest.TestCase):
    def setUp(self):
        self.document = NormalizedDocument(
            "report.pdf",
            "docling",
            (DocumentBlock("docling:1", "text", "Факт", (PageRef(4),)),),
            "e" * 64,
        )
        self.candidate = evidence_candidates(self.document)[0]
        self.context = EvidencePersistenceContext(
            project_id="11111111-1111-1111-1111-111111111111",
            document_id="22222222-2222-2222-2222-222222222222",
        )

    def test_builds_existing_evidence_schema_row(self):
        row = evidence_row(self.document, self.candidate, self.context)
        self.assertEqual(
            set(row),
            {
                "project_id", "document_id", "evidence_code", "data_class",
                "description", "source_ref", "confidence",
            },
        )
        self.assertIn("sha256:" + "e" * 64, row["source_ref"])
        self.assertIn("pages:4", row["source_ref"])
        self.assertEqual(row["data_class"], "ACTUAL")

    def test_writer_uses_only_evidence_table(self):
        calls = []
        writer = EvidenceRegisterWriter(lambda table, row: calls.append((table, row)) or "ok")
        result = writer.persist(self.document, self.candidate, self.context)
        self.assertEqual(result, "ok")
        self.assertEqual(calls[0][0], "evidence")

    def test_tampered_candidate_cannot_reach_transport(self):
        calls = []
        writer = EvidenceRegisterWriter(lambda table, row: calls.append((table, row)))
        tampered = replace(self.candidate, text="Подмена")
        with self.assertRaises(ValueError):
            writer.persist(self.document, tampered, self.context)
        self.assertEqual(calls, [])

    def test_invalid_database_context_is_rejected(self):
        with self.assertRaises(ValueError):
            EvidencePersistenceContext(project_id="not-uuid", document_id=self.context.document_id)


if __name__ == "__main__":
    unittest.main()

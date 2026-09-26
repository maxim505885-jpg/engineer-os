import unittest

from engineering.document_intelligence.contracts import (
    DocumentBlock,
    NormalizedDocument,
    PageRef,
)
from engineering.document_intelligence.evidence_bridge import evidence_candidates


class EvidenceBridgeTests(unittest.TestCase):
    def test_candidates_are_source_bound_and_deterministic(self):
        document = NormalizedDocument(
            source_path="report.pdf",
            parser="docling",
            source_sha256="a" * 64,
            blocks=(
                DocumentBlock(
                    block_id="docling:1",
                    kind="text",
                    text="Фактический фрагмент",
                    provenance=(PageRef(7),),
                ),
            ),
        )
        first = evidence_candidates(document)
        second = evidence_candidates(document)
        self.assertEqual(first, second)
        self.assertTrue(first[0].evidence_id.startswith("doc-evidence:"))
        self.assertEqual(first[0].source_sha256, "a" * 64)
        self.assertEqual(first[0].page_numbers, (7,))

    def test_source_hash_changes_evidence_identity(self):
        block = DocumentBlock("docling:1", "text", "Один текст", (PageRef(1),))
        left = NormalizedDocument("a.pdf", "docling", (block,), "a" * 64)
        right = NormalizedDocument("b.pdf", "docling", (block,), "b" * 64)
        self.assertNotEqual(
            evidence_candidates(left)[0].evidence_id,
            evidence_candidates(right)[0].evidence_id,
        )


if __name__ == "__main__":
    unittest.main()

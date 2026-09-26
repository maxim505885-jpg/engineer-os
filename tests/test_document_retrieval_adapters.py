import unittest

from engineering.document_intelligence.contracts import DocumentBlock, NormalizedDocument, PageRef
from engineering.document_intelligence.retrieval_adapters import (
    DeepDocRetrievalAdapter,
    PageIndexRetrievalAdapter,
    RetrievalAdapterError,
    RetrievalHit,
)


class RetrievalAdapterTests(unittest.TestCase):
    def setUp(self):
        self.document = NormalizedDocument(
            "report.pdf", "docling",
            (DocumentBlock("docling:1", "text", "Факт", (PageRef(1),)),),
            "f" * 64,
        )

    def test_deepdoc_hit_must_resolve_to_normalized_block(self):
        adapter = DeepDocRetrievalAdapter(lambda document, query: (RetrievalHit("docling:1"),))
        self.assertEqual(adapter.search(self.document, "нагрузка")[0].block_id, "docling:1")

    def test_pageindex_hit_must_resolve_to_normalized_block(self):
        adapter = PageIndexRetrievalAdapter(lambda document, query: (RetrievalHit("docling:1"),))
        self.assertEqual(adapter.search(self.document, "раздел")[0].block_id, "docling:1")

    def test_unknown_upstream_reference_is_blocked(self):
        adapter = PageIndexRetrievalAdapter(lambda document, query: (RetrievalHit("external:99"),))
        with self.assertRaises(RetrievalAdapterError):
            adapter.search(self.document, "раздел")

    def test_empty_retrieval_is_not_silent_success(self):
        adapter = DeepDocRetrievalAdapter(lambda document, query: ())
        with self.assertRaises(RetrievalAdapterError):
            adapter.search(self.document, "дефект")


if __name__ == "__main__":
    unittest.main()

import unittest

from engineering.document_intelligence.contracts import DocumentBlock, NormalizedDocument, PageRef
from engineering.document_intelligence.retrieval_adapters import RetrievalHit
from engineering.document_intelligence.retrieval_benchmark import (
    RetrievalBenchmarkCase,
    benchmark_retriever,
)


class RetrievalBenchmarkTests(unittest.TestCase):
    def setUp(self):
        self.document = NormalizedDocument(
            "report.pdf",
            "docling",
            (
                DocumentBlock("b1", "text", "Фундамент", (PageRef(1),)),
                DocumentBlock("b2", "text", "Перекрытие", (PageRef(2),)),
            ),
            "a" * 64,
        )

    def test_measures_confirmed_block_retrieval(self):
        cases = (
            RetrievalBenchmarkCase("фундамент", ("b1",)),
            RetrievalBenchmarkCase("перекрытие", ("b2",)),
        )
        def retrieve(document, query):
            return (RetrievalHit("b1" if query == "фундамент" else "b2"),)
        result = benchmark_retriever("provider", self.document, cases, retrieve)
        self.assertEqual(result.top1_rate, 1.0)
        self.assertEqual(result.expected_recall, 1.0)

    def test_unknown_provider_block_fails_closed(self):
        case = (RetrievalBenchmarkCase("фундамент", ("b1",)),)
        with self.assertRaises(ValueError):
            benchmark_retriever(
                "provider", self.document, case,
                lambda document, query: (RetrievalHit("invented"),),
            )

    def test_benchmark_cannot_reference_unknown_ground_truth(self):
        case = (RetrievalBenchmarkCase("что-то", ("invented",)),)
        with self.assertRaises(ValueError):
            benchmark_retriever(
                "provider", self.document, case,
                lambda document, query: (RetrievalHit("b1"),),
            )


if __name__ == "__main__":
    unittest.main()

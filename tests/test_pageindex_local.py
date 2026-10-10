import tempfile
import unittest
from pathlib import Path

from engineering.document_intelligence.contracts import DocumentBlock, NormalizedDocument, PageRef
from engineering.document_intelligence.pageindex_local import PageIndexLocalProvider
from engineering.document_intelligence.retrieval_adapters import RetrievalAdapterError


class _Client:
    def __init__(self, answer):
        self.answer = answer
        self.submitted = []
    def submit_document(self, path, wait=False):
        self.submitted.append((path, wait))
        return {"doc_id": "doc-1"}
    def chat(self, query, **kwargs):
        return self.answer


class PageIndexLocalProviderTests(unittest.TestCase):
    def _document(self, path):
        return NormalizedDocument(
            path,
            "docling",
            (
                DocumentBlock("b1", "text", "Фундамент", (PageRef(1),)),
                DocumentBlock("b2", "text", "Перекрытие", (PageRef(2),)),
            ),
            "a" * 64,
        )

    def test_page_citation_resolves_only_to_known_blocks(self):
        with tempfile.NamedTemporaryFile(suffix=".pdf") as handle:
            client = _Client('Ответ <cite doc="report.pdf" page="2"/>')
            provider = PageIndexLocalProvider(client_factory=lambda **kwargs: client)
            hits = provider.search(self._document(handle.name), "перекрытие")
        self.assertEqual(tuple(hit.block_id for hit in hits), ("b2",))
        self.assertEqual(client.submitted[0][1], True)

    def test_old_style_citation_is_supported(self):
        with tempfile.NamedTemporaryFile(suffix=".pdf") as handle:
            client = _Client("Ответ <doc=report.pdf;page=1>")
            provider = PageIndexLocalProvider(client_factory=lambda **kwargs: client)
            hits = provider.search(self._document(handle.name), "фундамент")
        self.assertEqual(hits[0].block_id, "b1")

    def test_untraceable_answer_fails_closed(self):
        with tempfile.NamedTemporaryFile(suffix=".pdf") as handle:
            provider = PageIndexLocalProvider(client_factory=lambda **kwargs: _Client("Ответ без ссылки"))
            with self.assertRaises(RetrievalAdapterError):
                provider.search(self._document(handle.name), "вопрос")

    def test_non_ollama_model_is_rejected_for_free_local_provider(self):
        with self.assertRaises(ValueError):
            PageIndexLocalProvider(index_model="openai/gpt-5", chat_model="ollama/qwen3:8b")


if __name__ == "__main__":
    unittest.main()

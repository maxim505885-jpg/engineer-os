"""Optional PageIndex local retrieval provider.

The provider is deliberately outside ENGINEER OS evidence truth. PageIndex
may use a local LiteLLM/Ollama model to reason over its tree, but every result
must resolve back to page-provenanced NormalizedDocument blocks.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Callable

from .contracts import NormalizedDocument
from .retrieval_adapters import RetrievalAdapterError, RetrievalHit


_CITE_PAGE = re.compile(
    r"(?:<doc=[^;<>]+;page=(\d+)(?:;[^<>]*)?>|<cite\s[^<>]*\bpage=[\"']?(\d+))",
    re.IGNORECASE,
)


class PageIndexLocalProvider:
    def __init__(
        self,
        *,
        index_model: str = "ollama/qwen3:8b",
        chat_model: str = "ollama/qwen3:8b",
        storage_path: str = ".engineer-os/pageindex",
        client_factory: Callable | None = None,
    ) -> None:
        if not index_model.startswith("ollama/") or not chat_model.startswith("ollama/"):
            raise ValueError("ENGINEER OS local PageIndex provider requires Ollama models")
        self._index_model = index_model
        self._chat_model = chat_model
        self._storage_path = storage_path
        self._client_factory = client_factory

    def _client(self):
        if self._client_factory is not None:
            return self._client_factory(
                index={"model": self._index_model, "storage_path": self._storage_path},
                chat={"model": self._chat_model},
            )
        try:
            from pageindex import PageIndexClient
        except ImportError as exc:
            raise RetrievalAdapterError("PageIndex SDK is not installed") from exc
        return PageIndexClient(
            index={"model": self._index_model, "storage_path": self._storage_path},
            chat={"model": self._chat_model},
        )

    def search(self, document: NormalizedDocument, query: str) -> tuple[RetrievalHit, ...]:
        if not query.strip():
            raise RetrievalAdapterError("query is required")
        source = Path(document.source_path)
        if not source.is_file():
            raise RetrievalAdapterError("PageIndex source PDF is unavailable")

        client = self._client()
        try:
            submitted = client.submit_document(str(source), wait=True)
            doc_id = submitted["doc_id"]
            answer = client.chat(query, doc_id=doc_id, citations=True)
        except Exception as exc:
            raise RetrievalAdapterError("PageIndex local retrieval failed") from exc
        if not isinstance(answer, str):
            raise RetrievalAdapterError("PageIndex returned an invalid answer")

        pages: list[int] = []
        for match in _CITE_PAGE.finditer(answer):
            value = match.group(1) or match.group(2)
            page = int(value)
            if page > 0 and page not in pages:
                pages.append(page)
        if not pages:
            raise RetrievalAdapterError("PageIndex returned no traceable page citations")

        hits: list[RetrievalHit] = []
        seen: set[str] = set()
        for page in pages:
            for block in document.blocks:
                if block.block_id in seen:
                    continue
                if any(ref.page_no == page for ref in block.provenance):
                    seen.add(block.block_id)
                    hits.append(
                        RetrievalHit(
                            block_id=block.block_id,
                            rationale=f"PageIndex cited page {page}",
                        )
                    )
        if not hits:
            raise RetrievalAdapterError("PageIndex citations do not resolve to normalized blocks")
        return tuple(hits)

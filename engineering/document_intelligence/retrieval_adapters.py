"""Experimental retrieval adapters for document intelligence.

These are capability boundaries, not trusted engineering evidence sources.
Upstream runtimes remain optional and their output must resolve back to
validated NormalizedDocument blocks before use.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from .contracts import NormalizedDocument


class RetrievalAdapterError(RuntimeError):
    pass


@dataclass(frozen=True)
class RetrievalHit:
    block_id: str
    score: float | None = None
    rationale: str | None = None


def _known_blocks(document: NormalizedDocument) -> set[str]:
    return {block.block_id for block in document.blocks}


def _validate_hits(document: NormalizedDocument, hits: tuple[RetrievalHit, ...]) -> tuple[RetrievalHit, ...]:
    if not hits:
        raise RetrievalAdapterError("retrieval returned no traceable hits")
    known = _known_blocks(document)
    if any(not hit.block_id or hit.block_id not in known for hit in hits):
        raise RetrievalAdapterError("retrieval referenced unknown document block")
    return hits


class DeepDocRetrievalAdapter:
    """Port for RAGFlow/DeepDoc-derived retrieval experiments."""

    def __init__(self, retrieve: Callable[[NormalizedDocument, str], tuple[RetrievalHit, ...]]) -> None:
        self._retrieve = retrieve

    def search(self, document: NormalizedDocument, query: str) -> tuple[RetrievalHit, ...]:
        if not query.strip():
            raise RetrievalAdapterError("query is required")
        return _validate_hits(document, tuple(self._retrieve(document, query)))


class PageIndexRetrievalAdapter:
    """Port for PageIndex local/cloud implementations.

    No PageIndex dependency or API key is required by ENGINEER OS core.
    """

    def __init__(self, retrieve: Callable[[NormalizedDocument, str], tuple[RetrievalHit, ...]]) -> None:
        self._retrieve = retrieve

    def search(self, document: NormalizedDocument, query: str) -> tuple[RetrievalHit, ...]:
        if not query.strip():
            raise RetrievalAdapterError("query is required")
        return _validate_hits(document, tuple(self._retrieve(document, query)))

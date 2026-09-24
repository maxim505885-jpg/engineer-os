from __future__ import annotations

import re
from dataclasses import dataclass

from .chunking import DocumentChunk


_WORD_RE = re.compile(r"[A-Za-zА-Яа-яЁё0-9]{3,}")


@dataclass(frozen=True)
class RetrievedEvidence:
    chunk: DocumentChunk
    score: int


class EvidenceContextCatalog:
    """In-memory, read-only document context for specialist retrieval."""

    def __init__(self) -> None:
        self._chunks_by_material: dict[str, tuple[DocumentChunk, ...]] = {}

    def register(self, material_id: str, chunks: tuple[DocumentChunk, ...]) -> None:
        if not material_id.strip():
            raise ValueError("material_id is required")
        self._chunks_by_material[material_id] = tuple(chunks)

    def retrieve(self, material_ids: tuple[str, ...], query: str, *, limit: int = 8) -> tuple[DocumentChunk, ...]:
        if limit < 1:
            raise ValueError("limit must be positive")
        tokens = {token.lower() for token in _WORD_RE.findall(query)}
        candidates: list[RetrievedEvidence] = []
        for material_id in material_ids:
            for chunk in self._chunks_by_material.get(material_id, ()):
                text_tokens = {token.lower() for token in _WORD_RE.findall(chunk.text)}
                score = len(tokens & text_tokens)
                candidates.append(RetrievedEvidence(chunk, score))

        candidates.sort(key=lambda item: (-item.score, item.chunk.sequence, item.chunk.id))
        selected = candidates[:limit]
        return tuple(item.chunk for item in selected)

    def evidence_ids(self, material_ids: tuple[str, ...], chunk_ids: tuple[str, ...]) -> tuple[str, ...]:
        wanted = set(chunk_ids)
        ids: list[str] = []
        for material_id in material_ids:
            for chunk in self._chunks_by_material.get(material_id, ()):
                if chunk.id in wanted:
                    ids.extend(chunk.evidence_ids)
        return tuple(dict.fromkeys(ids))

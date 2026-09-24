from __future__ import annotations

from dataclasses import dataclass

from .chunking import DocumentChunk


class EvidenceContextError(ValueError):
    pass


@dataclass(frozen=True)
class EvidenceContext:
    """Read-only retrieval view over document chunks.

    Core agents receive chunk identifiers through SpecialistTask; this object keeps
    the actual source text outside ENGINEER CORE contracts.
    """

    chunks: tuple[DocumentChunk, ...]

    def __post_init__(self) -> None:
        ids = [chunk.id for chunk in self.chunks]
        if len(ids) != len(set(ids)):
            raise EvidenceContextError("EvidenceContext contains duplicate chunk ids")

    def retrieve(self, chunk_ids: tuple[str, ...]) -> tuple[DocumentChunk, ...]:
        if not chunk_ids:
            return ()
        by_id = {chunk.id: chunk for chunk in self.chunks}
        missing = [chunk_id for chunk_id in chunk_ids if chunk_id not in by_id]
        if missing:
            raise EvidenceContextError(
                "Requested context chunk ids are unavailable: " + ", ".join(missing)
            )
        return tuple(by_id[chunk_id] for chunk_id in chunk_ids)

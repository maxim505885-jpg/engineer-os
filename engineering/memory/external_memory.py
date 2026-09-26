"""Trust boundary for external/project memory systems such as Mem0."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable


class MemoryTrust(str, Enum):
    UNVERIFIED = "UNVERIFIED"
    CONFIRMED_REFERENCE = "CONFIRMED_REFERENCE"


class MemoryBoundaryError(RuntimeError):
    pass


@dataclass(frozen=True)
class MemoryRecord:
    memory_id: str
    text: str
    source_ref: str
    trust: MemoryTrust = MemoryTrust.UNVERIFIED

    def __post_init__(self) -> None:
        if not self.memory_id.strip():
            raise ValueError("memory_id is required")
        if not self.text.strip():
            raise ValueError("memory text is required")
        if not self.source_ref.strip():
            raise ValueError("memory source_ref is required")


class ExternalMemoryAdapter:
    """Retrieves context only; never emits AgentResult or EvidenceCandidate."""

    def __init__(self, search_memory: Callable[[str], tuple[MemoryRecord, ...]]) -> None:
        self._search_memory = search_memory

    def search(self, query: str) -> tuple[MemoryRecord, ...]:
        if not query.strip():
            raise MemoryBoundaryError("memory query is required")
        records = tuple(self._search_memory(query))
        seen: set[str] = set()
        for record in records:
            if not isinstance(record, MemoryRecord):
                raise MemoryBoundaryError("memory backend returned invalid record")
            if record.memory_id in seen:
                raise MemoryBoundaryError("memory backend returned duplicate memory_id")
            seen.add(record.memory_id)
        return records


def memory_context(records: tuple[MemoryRecord, ...]) -> tuple[dict[str, str], ...]:
    """Serialize memory as explicitly non-evidentiary context."""
    return tuple(
        {
            "memory_id": item.memory_id,
            "text": item.text,
            "source_ref": item.source_ref,
            "trust": item.trust.value,
            "evidentiary_status": "NOT_EVIDENCE",
        }
        for item in records
    )

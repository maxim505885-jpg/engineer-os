"""Fail-closed contracts for normalized engineering documents."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class DocumentParseError(RuntimeError):
    """Raised when a source document cannot be normalized reliably."""


@dataclass(frozen=True)
class BoundingBox:
    left: float
    top: float
    right: float
    bottom: float


@dataclass(frozen=True)
class PageRef:
    page_no: int
    bbox: BoundingBox | None = None


@dataclass(frozen=True)
class DocumentBlock:
    block_id: str
    kind: str
    text: str
    provenance: tuple[PageRef, ...] = ()


@dataclass(frozen=True)
class NormalizedDocument:
    source_path: str
    parser: str
    blocks: tuple[DocumentBlock, ...]
    source_sha256: str

    def __post_init__(self) -> None:
        if len(self.source_sha256) != 64 or any(ch not in "0123456789abcdef" for ch in self.source_sha256):
            raise ValueError("source_sha256 must be 64 lowercase hex characters")
        if not self.blocks:
            raise ValueError("normalized document must contain at least one block")


class DocumentParser(Protocol):
    def parse(self, source_path: str) -> NormalizedDocument: ...

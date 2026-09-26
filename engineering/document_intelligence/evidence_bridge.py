"""Bridge normalized document blocks into immutable evidence candidates.

This module does not persist or ACCEPT evidence. It creates deterministic,
source-bound candidates for the existing Evidence Register/persistence layer.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from .contracts import DocumentBlock, NormalizedDocument


@dataclass(frozen=True)
class EvidenceCandidate:
    evidence_id: str
    source_sha256: str
    block_id: str
    kind: str
    text: str
    page_numbers: tuple[int, ...]


def _candidate_id(document: NormalizedDocument, block: DocumentBlock) -> str:
    payload = "\n".join(
        (
            document.source_sha256,
            block.block_id,
            block.kind,
            block.text,
            ",".join(str(ref.page_no) for ref in block.provenance),
        )
    ).encode("utf-8")
    return "doc-evidence:" + hashlib.sha256(payload).hexdigest()


def evidence_candidates(document: NormalizedDocument) -> tuple[EvidenceCandidate, ...]:
    """Create deterministic candidates; persistence/validation remains external."""
    candidates = []
    for block in document.blocks:
        if not block.text.strip():
            continue
        candidates.append(
            EvidenceCandidate(
                evidence_id=_candidate_id(document, block),
                source_sha256=document.source_sha256,
                block_id=block.block_id,
                kind=block.kind,
                text=block.text,
                page_numbers=tuple(ref.page_no for ref in block.provenance),
            )
        )
    if not candidates:
        raise ValueError("normalized document contains no evidence candidates")
    return tuple(candidates)

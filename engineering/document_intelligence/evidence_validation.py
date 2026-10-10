"""Validation gate for document-derived evidence candidates.

Candidates are untrusted extraction output until this gate validates source
binding and page provenance. The gate does not make engineering conclusions.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .contracts import NormalizedDocument
from .evidence_bridge import EvidenceCandidate


class EvidenceCandidateStatus(str, Enum):
    VALIDATED = "VALIDATED"
    BLOCK = "BLOCK"


@dataclass(frozen=True)
class EvidenceValidation:
    candidate: EvidenceCandidate
    status: EvidenceCandidateStatus
    reasons: tuple[str, ...] = ()


def validate_evidence_candidate(
    document: NormalizedDocument,
    candidate: EvidenceCandidate,
) -> EvidenceValidation:
    reasons: list[str] = []

    if candidate.source_sha256 != document.source_sha256:
        reasons.append("SOURCE_HASH_MISMATCH")
    if not candidate.text.strip():
        reasons.append("EMPTY_EVIDENCE_TEXT")
    if not candidate.page_numbers:
        reasons.append("MISSING_PAGE_PROVENANCE")
    elif any(page < 1 for page in candidate.page_numbers):
        reasons.append("INVALID_PAGE_PROVENANCE")

    matching_blocks = tuple(block for block in document.blocks if block.block_id == candidate.block_id)
    if len(matching_blocks) != 1:
        reasons.append("BLOCK_NOT_UNIQUE_OR_MISSING")
    else:
        block = matching_blocks[0]
        if block.text != candidate.text or block.kind != candidate.kind:
            reasons.append("BLOCK_CONTENT_MISMATCH")
        if tuple(ref.page_no for ref in block.provenance) != candidate.page_numbers:
            reasons.append("BLOCK_PROVENANCE_MISMATCH")

    return EvidenceValidation(
        candidate=candidate,
        status=EvidenceCandidateStatus.BLOCK if reasons else EvidenceCandidateStatus.VALIDATED,
        reasons=tuple(reasons),
    )


def validated_evidence_candidates(
    document: NormalizedDocument,
    candidates: tuple[EvidenceCandidate, ...],
) -> tuple[EvidenceCandidate, ...]:
    validations = tuple(validate_evidence_candidate(document, item) for item in candidates)
    blocked = tuple(item for item in validations if item.status is EvidenceCandidateStatus.BLOCK)
    if blocked:
        reasons = sorted({reason for item in blocked for reason in item.reasons})
        raise ValueError("document evidence validation blocked: " + ",".join(reasons))
    if not validations:
        raise ValueError("document evidence validation blocked: NO_CANDIDATES")
    return tuple(item.candidate for item in validations)

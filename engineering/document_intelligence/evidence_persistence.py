"""Persistence boundary for validated document evidence.

The adapter prepares rows for the existing public.evidence register. It never
accepts raw extraction output: callers must provide the NormalizedDocument and
the candidate is revalidated immediately before row construction.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from .contracts import NormalizedDocument
from .evidence_bridge import EvidenceCandidate
from .evidence_validation import EvidenceCandidateStatus, validate_evidence_candidate


@dataclass(frozen=True)
class EvidencePersistenceContext:
    project_id: str
    document_id: str
    data_class: str = "UNKNOWN"
    confidence: str = "PROVENANCE_VALIDATED"

    def __post_init__(self) -> None:
        for name, value in (("project_id", self.project_id), ("document_id", self.document_id)):
            try:
                UUID(value)
            except (TypeError, ValueError) as exc:
                raise ValueError(f"{name} must be a UUID") from exc
        allowed = {"PROJECT", "ACTUAL", "MEASURED", "TESTED", "CALCULATED", "ASSUMED", "INTERPRETED", "UNKNOWN"}
        if self.data_class not in allowed:
            raise ValueError("invalid data_class")


def evidence_row(
    document: NormalizedDocument,
    candidate: EvidenceCandidate,
    context: EvidencePersistenceContext,
) -> dict[str, str]:
    """Build a public.evidence row only after revalidating provenance."""
    validation = validate_evidence_candidate(document, candidate)
    if validation.status is not EvidenceCandidateStatus.VALIDATED:
        raise ValueError(
            "refusing to persist unvalidated document evidence: "
            + ",".join(validation.reasons)
        )

    pages = ",".join(str(page) for page in candidate.page_numbers)
    source_ref = (
        f"document:{context.document_id};sha256:{candidate.source_sha256};"
        f"block:{candidate.block_id};pages:{pages}"
    )
    return {
        "project_id": context.project_id,
        "document_id": context.document_id,
        "evidence_code": candidate.evidence_id,
        "data_class": context.data_class,
        "description": candidate.text,
        "source_ref": source_ref,
        "confidence": context.confidence,
    }


class EvidenceRegisterWriter:
    """Small port around persistence; transport is injected and testable."""

    def __init__(self, insert_row):
        self._insert_row = insert_row

    def persist(
        self,
        document: NormalizedDocument,
        candidate: EvidenceCandidate,
        context: EvidencePersistenceContext,
    ):
        row = evidence_row(document, candidate, context)
        return self._insert_row("evidence", row, ("document_id", "evidence_code"))


def production_evidence_writer():
    """Build the only production writer for validated document evidence."""
    from .supabase_evidence_transport import production_evidence_transport
    return EvidenceRegisterWriter(production_evidence_transport())

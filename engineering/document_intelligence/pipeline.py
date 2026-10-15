"""Fail-closed pipeline from parsed document to explicitly selected Evidence Register rows."""

from __future__ import annotations

from .contracts import NormalizedDocument
from .document_registration import SourceDocumentIdentity, assert_document_identity
from .evidence_bridge import EvidenceCandidate, evidence_candidates
from .evidence_persistence import EvidencePersistenceContext, EvidenceRegisterWriter
from .evidence_validation import validated_evidence_candidates


def prepare_validated_evidence(
    document: NormalizedDocument,
    identity: SourceDocumentIdentity,
    identity_verifier,
) -> tuple[EvidenceCandidate, ...]:
    """Verify DB identity and provenance before exposing candidates for selection."""
    assert_document_identity(document.source_sha256, identity)
    identity_verifier.verify(identity)
    return validated_evidence_candidates(document, evidence_candidates(document))


def persist_selected_evidence(
    document: NormalizedDocument,
    candidates: tuple[EvidenceCandidate, ...],
    selected_evidence_ids: tuple[str, ...],
    context: EvidencePersistenceContext,
    writer: EvidenceRegisterWriter,
) -> tuple[object, ...]:
    """Persist only an explicit subset; never bulk-accept all parser output implicitly."""
    if not selected_evidence_ids:
        raise ValueError("at least one evidence_id must be explicitly selected")
    if len(set(selected_evidence_ids)) != len(selected_evidence_ids):
        raise ValueError("duplicate evidence_id selection")

    by_id = {candidate.evidence_id: candidate for candidate in candidates}
    if len(by_id) != len(candidates):
        raise ValueError("candidate evidence IDs must be unique")

    missing = tuple(item for item in selected_evidence_ids if item not in by_id)
    if missing:
        raise ValueError("selected evidence_id is not a validated candidate")

    return tuple(
        writer.persist(document, by_id[evidence_id], context)
        for evidence_id in selected_evidence_ids
    )



def persist_selected_unverified_asset(
    source_path: str,
    registered_sha256: str,
    candidate_id: str,
    project_id: str,
    document_id: str,
    *,
    page_number: int | None = None,
    transport=None,
):
    """Production asset entrypoint, separate from validated text evidence.

    Requires explicit candidate selection, rechecks original source bytes,
    and stores ONLY a source-linked UNCERTAINTY candidate.
    """
    from pathlib import Path
    from .asset_candidate_pipeline import (
        persist_selected_docx_asset, persist_selected_pdf_table,
    )
    if not candidate_id.startswith('doc-asset:'):
        raise ValueError('ASSET_CANDIDATE_ID_REQUIRED')
    if transport is None:
        from .supabase_asset_candidate_transport import production_asset_candidate_transport
        transport=production_asset_candidate_transport()
    suffix=Path(source_path).suffix.lower()
    if suffix=='.docx':
        if page_number is not None:
            raise ValueError('DOCX_ASSET_REQUIRES_ZIP_LOCATION_NOT_PDF_PAGE')
        return persist_selected_docx_asset(
            source_path,registered_sha256,candidate_id,project_id,document_id,transport)
    if suffix=='.pdf':
        if page_number is None or page_number<1:
            raise ValueError('PDF_ASSET_PAGE_REQUIRED')
        return persist_selected_pdf_table(
            source_path,registered_sha256,page_number,candidate_id,
            project_id,document_id,transport)
    raise ValueError('UNSUPPORTED_ASSET_SOURCE_TYPE')

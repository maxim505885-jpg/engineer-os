"""Candidate-only asset row adapter for existing evidence transport.

Byte integrity does not imply engineering validation. Caller must explicitly
opt into recording an uncertain asset candidate; no automated acceptance.
"""
from .asset_provenance import verify_payload
from .evidence_persistence import EvidencePersistenceContext


def uncertain_asset_row(candidate, payload: bytes, registered_source_sha256: str,
                        context: EvidencePersistenceContext):
    if candidate.verified:
        raise ValueError("VERIFIED_ASSET_NOT_ALLOWED")
    verify_payload(candidate, payload, registered_source_sha256)
    return {
        "project_id": context.project_id,
        "document_id": context.document_id,
        "evidence_code": candidate.candidate_id,
        "data_class": "UNKNOWN",
        "description": ("Unverified document asset: " + candidate.asset_kind
                        + " at " + candidate.location
                        + "; SEMANTIC_VISUAL_REVIEW_REQUIRED"),
        "source_ref": ("document:" + context.document_id
                       + ";sha256:" + candidate.source_sha256
                       + ";asset_sha256:" + candidate.asset_sha256
                       + ";location:" + candidate.location
                       + ";page:" + (str(candidate.page_number) if candidate.page_number else "")),
        "confidence": "UNCERTAINTY",
    }


class UncertainAssetRegisterWriter:
    """Uses injected existing evidence transport; insertion is not validation."""

    def __init__(self, insert_row):
        self._insert_row = insert_row

    def persist(self, candidate, payload, source_sha256, context):
        row = uncertain_asset_row(candidate, payload, source_sha256, context)
        return self._insert_row("evidence", row, ("document_id", "evidence_code"))

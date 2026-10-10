"""Fail-closed boundary for DOCX binary asset evidence.

Byte integrity is necessary but insufficient for semantic validation.
"""
from dataclasses import dataclass
from .asset_provenance import DocumentAssetEvidence, verify_payload
from .docx_asset_ingestion import source_assets

@dataclass(frozen=True)
class AssetValidationResult:
    candidate: DocumentAssetEvidence
    status: str
    reason: str


def validate_asset_source(candidate, payload, source_sha256):
    verify_payload(candidate,payload,source_sha256)
    return AssetValidationResult(candidate,'UNCERTAINTY','SEMANTIC_VISUAL_REVIEW_REQUIRED')


def prepare_docx_asset_candidates(source_path, registered_sha256):
    """Verify source identity before exposing immutable, unverified candidates."""
    import hashlib
    with open(source_path,'rb') as f:
        actual=hashlib.file_digest(f,'sha256').hexdigest()
    if actual!=registered_sha256:
        raise ValueError('SOURCE_IDENTITY_MISMATCH')
    candidates=source_assets(source_path)
    if len(set(item.candidate_id for item in candidates))!=len(candidates):
        raise ValueError('DUPLICATE_ASSET_CANDIDATE')
    if any(item.source_sha256!=registered_sha256 for item in candidates):
        raise ValueError('SOURCE_IDENTITY_MISMATCH')
    return candidates

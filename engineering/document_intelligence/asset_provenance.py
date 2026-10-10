"""Source-linked immutable references for non-text document assets.

An asset candidate is NOT a validated interpretation of an engineering item.
Preserves source and payload identity without changing existing text pipelines.
"""
from dataclasses import dataclass
import hashlib

_ALLOWED={"table_cells","omml_formula","emf_graphic","embedded_image"}

@dataclass(frozen=True)
class DocumentAssetEvidence:
    source_sha256: str
    asset_sha256: str
    asset_kind: str
    location: str
    page_number: int | None = None
    verified: bool = False

    def __post_init__(self):
        for value in (self.source_sha256,self.asset_sha256):
            if len(value)!=64 or any(c not in "0123456789abcdef" for c in value):
                raise ValueError("Asset and source SHA256 must be valid")
        if self.asset_kind not in _ALLOWED:
            raise ValueError("Unsupported asset kind")
        if not self.location.strip():
            raise ValueError("Asset source location required")
        if self.page_number is not None and self.page_number<1:
            raise ValueError("Invalid page number")
        if self.verified:
            raise ValueError("Source-only assets cannot enter as verified")

    @property
    def candidate_id(self):
        data="\n".join([self.source_sha256,self.asset_sha256,self.asset_kind,
                          self.location,str(self.page_number or "")]).encode("utf-8")
        return "doc-asset:"+hashlib.sha256(data).hexdigest()


def verify_payload(candidate: DocumentAssetEvidence, payload: bytes, source_sha256: str) -> bool:
    if candidate.source_sha256!=source_sha256:
        raise ValueError("SOURCE_IDENTITY_MISMATCH")
    if hashlib.sha256(payload).hexdigest()!=candidate.asset_sha256:
        raise ValueError("ASSET_PAYLOAD_MISMATCH")
    return True

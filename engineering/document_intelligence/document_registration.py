"""Registration contract for source documents before evidence persistence."""

from __future__ import annotations

from dataclasses import dataclass
import re

_SHA256 = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class SourceDocumentIdentity:
    project_id: str
    document_id: str
    source_sha256: str

    def __post_init__(self) -> None:
        if not _SHA256.fullmatch(self.source_sha256):
            raise ValueError("source_sha256 must be 64 lowercase hex characters")


def assert_document_identity(document_source_sha256: str, identity: SourceDocumentIdentity) -> None:
    """Fail closed when parsed bytes do not match the registered DB document."""
    if document_source_sha256 != identity.source_sha256:
        raise ValueError("parsed source does not match registered document checksum")

"""Document Intelligence boundary for evidence-preserving document parsing."""

from .contracts import (
    BoundingBox,
    DocumentBlock,
    DocumentParseError,
    NormalizedDocument,
    PageRef,
)
from .docling_adapter import DoclingDocumentParser, document_intelligence_enabled
from .evidence_bridge import EvidenceCandidate, evidence_candidates

__all__ = [
    "BoundingBox",
    "DocumentBlock",
    "DocumentParseError",
    "NormalizedDocument",
    "PageRef",
    "DoclingDocumentParser",
    "document_intelligence_enabled",
    "EvidenceCandidate",
    "evidence_candidates",
]

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
from .evidence_persistence import EvidencePersistenceContext, EvidenceRegisterWriter, evidence_row, production_evidence_writer
from .pipeline import prepare_validated_evidence, persist_selected_evidence
from .document_registration import SourceDocumentIdentity, assert_document_identity
from .supabase_document_identity import SupabaseDocumentIdentityVerifier, production_document_identity_verifier
from .retrieval_adapters import DeepDocRetrievalAdapter, PageIndexRetrievalAdapter, RetrievalAdapterError, RetrievalHit
from .evidence_validation import (
    EvidenceCandidateStatus,
    EvidenceValidation,
    validate_evidence_candidate,
    validated_evidence_candidates,
)

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
    "EvidencePersistenceContext",
    "EvidenceRegisterWriter",
    "evidence_row",
    "production_evidence_writer",
    "prepare_validated_evidence",
    "persist_selected_evidence",
    "SourceDocumentIdentity",
    "assert_document_identity",
    "SupabaseDocumentIdentityVerifier",
    "production_document_identity_verifier",
    "DeepDocRetrievalAdapter",
    "PageIndexRetrievalAdapter",
    "RetrievalAdapterError",
    "RetrievalHit",
    "EvidenceCandidateStatus",
    "EvidenceValidation",
    "validate_evidence_candidate",
    "validated_evidence_candidates",
]

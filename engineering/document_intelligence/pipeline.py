from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from engineering.core.contracts import MaterialRef

from .chunking import DocumentChunk, DocumentChunker
from .docx import DocxTextExtractor, ExtractedDocument


@dataclass(frozen=True)
class DocumentIntelligenceResult:
    material: MaterialRef
    document: ExtractedDocument
    chunks: tuple[DocumentChunk, ...]


class DocumentIntelligence:
    """Deterministic document ingestion: extract, bind evidence, then chunk."""

    def __init__(self, chunker: DocumentChunker | None = None) -> None:
        self.extractor = DocxTextExtractor()
        self.chunker = chunker or DocumentChunker()

    def ingest(self, path: str | Path, *, material_id: str | None = None) -> DocumentIntelligenceResult:
        document = self.extractor.extract(path)
        document_id = self._document_id(document)
        if material_id is not None and material_id != document_id:
            raise ValueError("material_id must match the deterministic document_id to preserve evidence provenance")
        material = MaterialRef(
            id=document_id,
            kind="document",
            name=Path(document.source_path).name,
            uri=document.source_path,
        )
        return DocumentIntelligenceResult(
            material=material,
            document=document,
            chunks=self.chunker.chunk(document),
        )

    @staticmethod
    def _document_id(document: ExtractedDocument) -> str:
        for evidence_id in (*document.paragraph_ids, *(table.id for table in document.tables), *document.image_ids):
            return evidence_id.split(":", 1)[0]
        return "unknown"

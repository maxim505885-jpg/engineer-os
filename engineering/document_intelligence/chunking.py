from __future__ import annotations

from dataclasses import dataclass

from .docx import ExtractedBlock, ExtractedDocument


@dataclass(frozen=True)
class DocumentChunk:
    id: str
    document_id: str
    sequence: int
    text: str
    evidence_ids: tuple[str, ...]
    block_kinds: tuple[str, ...]


class DocumentChunker:
    """Split extracted blocks without losing source/evidence binding."""

    def __init__(self, max_chars: int = 6000) -> None:
        if max_chars < 1:
            raise ValueError("max_chars must be positive")
        self.max_chars = max_chars

    def chunk(self, document: ExtractedDocument) -> tuple[DocumentChunk, ...]:
        if not document.blocks:
            return ()

        document_id = document.paragraph_ids[0].split(":paragraph:", 1)[0] if document.paragraph_ids else (
            document.tables[0].id.split(":table:", 1)[0] if document.tables else (
                document.image_ids[0].split(":image:", 1)[0] if document.image_ids else "unknown"
            )
        )

        chunks: list[DocumentChunk] = []
        current: list[ExtractedBlock] = []
        current_chars = 0

        def flush() -> None:
            nonlocal current, current_chars
            if not current:
                return
            sequence = len(chunks) + 1
            text_parts = [block.text for block in current if block.text]
            evidence_ids = tuple(block.id for block in current)
            chunks.append(
                DocumentChunk(
                    id=f"{document_id}:chunk:{sequence:04d}",
                    document_id=document_id,
                    sequence=sequence,
                    text="\n\n".join(text_parts),
                    evidence_ids=evidence_ids,
                    block_kinds=tuple(block.kind for block in current),
                )
            )
            current = []
            current_chars = 0

        for block in document.blocks:
            block_size = len(block.text)
            if current and current_chars + block_size + 2 > self.max_chars:
                flush()
            current.append(block)
            current_chars += block_size + (2 if len(current) > 1 else 0)
            if block_size > self.max_chars:
                flush()

        flush()
        return tuple(chunks)

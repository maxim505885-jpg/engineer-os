"""Optional Docling adapter.

Docling is imported lazily so ENGINEER OS can boot without the optional
dependency. Parsing failures are explicit and never degrade into an empty or
accepted document.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Any, Callable

from .contracts import BoundingBox, DocumentBlock, DocumentParseError, NormalizedDocument, PageRef


def document_intelligence_enabled() -> bool:
    return os.environ.get("ENGINEER_OS_DOCUMENT_INTELLIGENCE", "false").lower() == "true"


class DoclingDocumentParser:
    def __init__(self, converter_factory: Callable[[], Any] | None = None) -> None:
        self._converter_factory = converter_factory

    @staticmethod
    def _sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def _converter(self) -> Any:
        if self._converter_factory is not None:
            return self._converter_factory()
        try:
            from docling.datamodel.base_models import InputFormat
            from docling.datamodel.pipeline_options import PdfPipelineOptions, RapidOcrOptions
            from docling.document_converter import DocumentConverter, PdfFormatOption
        except ImportError as exc:
            raise DocumentParseError(
                "Docling is not installed; document intelligence cannot parse this source"
            ) from exc
        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_ocr = True
        pipeline_options.ocr_options = RapidOcrOptions(
            backend="onnxruntime",
            lang=["iso:ru", "iso:en"],
        )
        return DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
            }
        )

    @staticmethod
    def _page_ref(prov: Any) -> PageRef | None:
        if not isinstance(prov, dict):
            return None
        page_no = prov.get("page_no")
        if not isinstance(page_no, int) or page_no < 1:
            return None
        bbox_data = prov.get("bbox")
        bbox = None
        if isinstance(bbox_data, dict):
            try:
                bbox = BoundingBox(
                    float(bbox_data["l"]),
                    float(bbox_data["t"]),
                    float(bbox_data["r"]),
                    float(bbox_data["b"]),
                )
            except (KeyError, TypeError, ValueError):
                bbox = None
        return PageRef(page_no=page_no, bbox=bbox)

    @classmethod
    def _normalize(cls, exported: dict[str, Any]) -> tuple[DocumentBlock, ...]:
        blocks: list[DocumentBlock] = []
        seen: set[tuple[str, str, tuple[PageRef, ...]]] = set()

        def visit(node: Any, path: str) -> None:
            if isinstance(node, dict):
                text = node.get("text")
                if isinstance(text, str) and text.strip():
                    kind = str(node.get("label") or node.get("type") or "text")
                    raw_prov = node.get("prov") or node.get("provenance") or ()
                    if isinstance(raw_prov, dict):
                        raw_prov = (raw_prov,)
                    refs = tuple(
                        ref for ref in (cls._page_ref(item) for item in raw_prov)
                        if ref is not None
                    ) if isinstance(raw_prov, (list, tuple)) else ()
                    key = (kind, text.strip(), refs)
                    if key not in seen:
                        seen.add(key)
                        blocks.append(
                            DocumentBlock(
                                block_id=f"docling:{len(blocks) + 1}",
                                kind=kind,
                                text=text.strip(),
                                provenance=refs,
                            )
                        )
                for key, value in node.items():
                    visit(value, f"{path}/{key}")
            elif isinstance(node, list):
                for index, value in enumerate(node):
                    visit(value, f"{path}/{index}")

        visit(exported, "")
        return tuple(blocks)

    def parse(self, source_path: str) -> NormalizedDocument:
        path = Path(source_path)
        if not path.is_file():
            raise DocumentParseError(f"source document not found: {source_path}")
        if not document_intelligence_enabled():
            raise DocumentParseError("document intelligence is disabled")

        try:
            result = self._converter().convert(str(path))
            document = getattr(result, "document", None)
            if document is None or not hasattr(document, "export_to_dict"):
                raise DocumentParseError("Docling returned no exportable document")
            exported = document.export_to_dict()
            if not isinstance(exported, dict):
                raise DocumentParseError("Docling export is not a mapping")
            blocks = self._normalize(exported)
        except DocumentParseError:
            raise
        except Exception as exc:
            raise DocumentParseError(f"Docling conversion failed: {type(exc).__name__}") from exc

        if not blocks:
            raise DocumentParseError("Docling produced no evidence-bearing content")

        return NormalizedDocument(
            source_path=str(path),
            parser="docling",
            blocks=blocks,
            source_sha256=self._sha256(path),
        )

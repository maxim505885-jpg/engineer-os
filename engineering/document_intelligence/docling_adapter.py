"""Optional Docling adapter.

Docling is imported lazily so ENGINEER OS can boot without the optional
dependency. Parsing failures are explicit and never degrade into an empty or
accepted document.
"""

from __future__ import annotations

import hashlib
import os
import re
from pathlib import Path
from typing import Any, Callable

from .contracts import BoundingBox, DocumentBlock, DocumentParseError, NormalizedDocument, PageRef


def document_intelligence_enabled() -> bool:
    return os.environ.get("ENGINEER_OS_DOCUMENT_INTELLIGENCE", "false").lower() == "true"


class DoclingDocumentParser:
    def __init__(self, converter_factory: Callable[[], Any] | None = None, *, table_mode: str = "accurate") -> None:
        if table_mode not in ("accurate", "fast"):
            raise ValueError("table_mode must be accurate or fast")
        self._converter_factory = converter_factory
        self._table_mode = table_mode

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
            from docling.datamodel.pipeline_options import PdfPipelineOptions, RapidOcrOptions, TableFormerMode
            from docling.document_converter import DocumentConverter, PdfFormatOption
        except ImportError as exc:
            raise DocumentParseError(
                "Docling is not installed; document intelligence cannot parse this source"
            ) from exc
        pipeline_options = PdfPipelineOptions()
        if self._table_mode == "fast":
            pipeline_options.table_structure_options.mode = TableFormerMode.FAST
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
                    # Nested table cells and duplicated export fields may have no
                    # page provenance. They cannot serve as evidence blocks.
                    if refs and key not in seen:
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

    @classmethod
    def _is_page_stamp(cls, table: dict[str, Any]) -> bool:
        """Recognize only the measured bottom drawing stamp, never a body table."""
        prov = table.get("prov") or []
        data = table.get("data") or {}
        if (not isinstance(prov, list) or len(prov) != 1 or not isinstance(data, dict)
                or (data.get("num_rows"), data.get("num_cols")) not in ((3, 7), (1, 6))):
            return False
        bbox = prov[0].get("bbox") if isinstance(prov[0], dict) else None
        if (not isinstance(bbox, dict) or bbox.get("coord_origin") != "BOTTOMLEFT"
                or not isinstance(bbox.get("t"), (int, float))
                or not isinstance(bbox.get("b"), (int, float))
                or not 0 <= bbox["b"] < bbox["t"] <= 80):
            return False
        cells = data.get("table_cells")
        one_row = data.get("num_rows") == 1
        if not isinstance(cells, list) or not (len(cells) == 6 if one_row else 7 <= len(cells) <= 12):
            return False
        values = [c.get("text", "").strip() for c in cells if isinstance(c, dict)]
        if len(values) != len(cells):
            return False
        required = {"Изм.", "Кол.уч", "Подп.", "Дата", "Лист"}
        if not required.issubset(values):
            return False
        if one_row and (set(values) != required | {"№ док."} or
                        {(c.get("start_row_offset_idx"), c.get("end_row_offset_idx"),
                          c.get("start_col_offset_idx"), c.get("end_col_offset_idx"))
                         for c in cells} != {(0, 1, col, col + 1) for col in range(6)}):
            return False
        allowed = required | {"№ док.", "№ док. Лист", "Лист №", "Пояснения"}
        return all(v in allowed or v.isdigit() or re.fullmatch(
            r"[A-ZА-ЯЁ]{2,5}-[A-ZА-ЯЁ]{2,5}-\d{2}/\d{4}-\d+", v
        ) for v in values)

    @classmethod
    def _table_rows(cls, exported: dict[str, Any]) -> tuple[DocumentBlock, ...]:
        rows: list[DocumentBlock] = []
        tables = exported.get("tables") or []
        if not isinstance(tables, list):
            raise DocumentParseError("table export is not a list")
        for table_index, table in enumerate(tables):
            if not isinstance(table, dict):
                raise DocumentParseError("table export is not a mapping")
            if cls._is_page_stamp(table):
                continue
            provenance = table.get("prov") or []
            if not isinstance(provenance, list):
                raise DocumentParseError("table provenance is invalid")
            refs = tuple(ref for ref in (cls._page_ref(p) for p in provenance) if ref is not None)
            if len(refs) != 1:
                raise DocumentParseError("table requires exactly one source page")
            # Table provenance bounds the entire table, not an individual row.
            row_ref = PageRef(page_no=refs[0].page_no)
            data = table.get("data") or {}
            if not isinstance(data, dict):
                raise DocumentParseError("table data is invalid")
            count_rows, count_cols = data.get("num_rows"), data.get("num_cols")
            if (not isinstance(count_rows, int) or not isinstance(count_cols, int)
                    or count_rows < 2 or count_cols < 2):
                raise DocumentParseError("table dimensions are invalid")
            cells = data.get("table_cells")
            if not isinstance(cells, list):
                raise DocumentParseError("table cells are missing")
            grid: dict[tuple[int, int], str] = {}
            for cell in cells:
                if not isinstance(cell, dict):
                    raise DocumentParseError(f"table page {row_ref.page_no} table {table_index} invalid cell")
                r, c = cell.get("start_row_offset_idx"), cell.get("start_col_offset_idx")
                if (not isinstance(r, int) or not isinstance(c, int)
                        or r < 0 or r >= count_rows or c < 0 or c >= count_cols):
                    raise DocumentParseError(f"table page {row_ref.page_no} table {table_index} invalid cell coordinates")
                location = f"table page {row_ref.page_no} table {table_index}"
                if cell.get("end_row_offset_idx") != r + 1 or cell.get("end_col_offset_idx") != c + 1:
                    raise DocumentParseError(f"{location} merged cell row {r} col {c}")
                if (r, c) in grid:
                    raise DocumentParseError(f"{location} duplicate cell row {r} col {c}")
                if not isinstance(cell.get("text"), str) or not cell["text"].strip():
                    raise DocumentParseError(f"{location} empty cell row {r} col {c}")
                grid[r, c] = cell["text"].strip()
            if len(grid) != count_rows * count_cols:
                raise DocumentParseError(
                    f"table page {row_ref.page_no} table {table_index} grid has missing cells "
                    f"({count_rows * count_cols - len(grid)} missing of {count_rows * count_cols})"
                )
            headings = [grid[0, c] for c in range(count_cols)]
            for r in range(1, count_rows):
                rows.append(DocumentBlock(
                    block_id=f"docling:table:{table_index}:row:{r}:page:{refs[0].page_no}",
                    kind="table_row",
                    text=" | ".join(f"{headings[c]}: {grid[r, c]}" for c in range(count_cols)),
                    provenance=(row_ref,),
                ))
        return tuple(rows)

    def parse(self, source_path: str, *, page_range: tuple[int, int] | None = None) -> NormalizedDocument:
        path = Path(source_path)
        if not path.is_file():
            raise DocumentParseError(f"source document not found: {source_path}")
        if not document_intelligence_enabled():
            raise DocumentParseError("document intelligence is disabled")

        try:
            converter = self._converter()
            result = converter.convert(str(path), page_range=page_range) if page_range else converter.convert(str(path))
            document = getattr(result, "document", None)
            if document is None or not hasattr(document, "export_to_dict"):
                raise DocumentParseError("Docling returned no exportable document")
            exported = document.export_to_dict()
            if not isinstance(exported, dict):
                raise DocumentParseError("Docling export is not a mapping")
            blocks = self._normalize(exported)
            # The generic text walker does not preserve table cell/page
            # relationships. A table can also be silently omitted while its
            # caption survives, so both signals must block the chunk.
            has_table_caption = any(
                block.kind == "caption" and re.match(r"^\s*(?:табл(?:ица|\.)?\s|table\s)", block.text, re.I)
                for block in blocks
            )
            table_rows = self._table_rows(exported)
            table_pages = {ref.page_no for row in table_rows for ref in row.provenance}
            if has_table_caption and any(
                ref.page_no not in table_pages for block in blocks
                if block.kind == "caption" and re.match(r"^\s*(?:табл(?:ица|\.)?\s|table\s)", block.text, re.I)
                for ref in block.provenance
            ):
                raise DocumentParseError("table caption lacks verified table rows")
            blocks += table_rows
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

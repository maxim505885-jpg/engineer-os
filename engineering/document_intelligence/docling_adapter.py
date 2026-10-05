"""Optional Docling adapter.

Docling is imported lazily so ENGINEER OS can boot without the optional
dependency. Parsing failures are explicit and never degrade into an empty or
accepted document.
"""

from __future__ import annotations

import hashlib
import os
import math
import re
from pathlib import Path
from typing import Any, Callable

from .contracts import BoundingBox, DocumentBlock, DocumentParseError, NormalizedDocument, PageRef


def document_intelligence_enabled() -> bool:
    return os.environ.get("ENGINEER_OS_DOCUMENT_INTELLIGENCE", "false").lower() == "true"


class DoclingDocumentParser:
    def __init__(self, converter_factory: Callable[[], Any] | None = None, *, table_mode: str = "accurate",
                 artifacts_path: str | Path | None = None) -> None:
        if table_mode not in ("accurate", "fast"):
            raise ValueError("table_mode must be accurate or fast")
        self._converter_factory = converter_factory
        self._table_mode = table_mode
        selected = artifacts_path if artifacts_path is not None else os.environ.get('ENGINEER_OS_DOCLING_ARTIFACTS_PATH')
        self._artifacts_path = Path(selected) if selected else None

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
        if self._artifacts_path is not None and not self._artifacts_path.is_dir():
            raise DocumentParseError(f'Docling model artifacts folder not found: {self._artifacts_path}')
        try:
            from docling.datamodel.base_models import InputFormat
            from docling.datamodel.pipeline_options import PdfPipelineOptions, RapidOcrOptions, TableFormerMode
            from docling.document_converter import DocumentConverter, PdfFormatOption
        except ImportError as exc:
            raise DocumentParseError(
                "Docling is not installed; document intelligence cannot parse this source"
            ) from exc
        pipeline_options = PdfPipelineOptions(artifacts_path=self._artifacts_path)
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
    def _page_ref(prov: Any, page_heights: dict[int, float] | None = None) -> PageRef | None:
        if not isinstance(prov, dict):
            return None
        page_no = prov.get("page_no")
        if not isinstance(page_no, int) or page_no < 1:
            return None
        bbox_data = prov.get("bbox")
        bbox = None
        if isinstance(bbox_data, dict):
            try:
                left, top, right, bottom = (float(bbox_data[k]) for k in ("l", "t", "r", "b"))
                origin = bbox_data.get("coord_origin", "TOPLEFT")
                if origin == "BOTTOMLEFT":
                    height = (page_heights or {}).get(page_no)
                    if height is None:
                        raise ValueError("source page height required for bottom-left coordinates")
                    top, bottom = height - top, height - bottom
                elif origin != "TOPLEFT":
                    raise ValueError("unknown coordinate origin")
                if (not all(math.isfinite(v) for v in (left, top, right, bottom))
                        or not 0 <= left < right or not 0 <= top < bottom):
                    raise ValueError("invalid source bbox")
                bbox = BoundingBox(left, top, right, bottom)
            except (KeyError, TypeError, ValueError):
                bbox = None
        return PageRef(page_no=page_no, bbox=bbox)

    @classmethod
    def _normalize(cls, exported: dict[str, Any]) -> tuple[DocumentBlock, ...]:
        blocks: list[DocumentBlock] = []
        seen: set[tuple[str, str, tuple[PageRef, ...]]] = set()
        page_heights = {}
        pages = exported.get("pages")
        if isinstance(pages, dict):
            for key, page in pages.items():
                try:
                    height = page["size"]["height"]
                    page_no = int(key)
                    if (page_no >= 1 and type(height) in (int, float)
                            and math.isfinite(height) and height > 0):
                        page_heights[page_no] = float(height)
                except (KeyError, TypeError, ValueError):
                    continue

        def visit(node: Any, path: str) -> None:
            if isinstance(node, dict):
                text = node.get("text")
                if isinstance(text, str) and text.strip():
                    kind = str(node.get("label") or node.get("type") or "text")
                    raw_prov = node.get("prov") or node.get("provenance") or ()
                    if isinstance(raw_prov, dict):
                        raw_prov = (raw_prov,)
                    refs = tuple(
                        ref for ref in (cls._page_ref(item, page_heights) for item in raw_prov)
                        if ref is not None
                    ) if isinstance(raw_prov, (list, tuple)) else ()
                    key = (kind, text.strip(), refs)
                    # Nested table cells and duplicated export fields may have no
                    # page provenance. They cannot serve as evidence blocks.
                    if refs and key not in seen:
                        seen.add(key)
                        # Independent page exports restart their local counters.
                        # Keep original page identity when combining bounded chunks.
                        page_identity = ','.join(str(p) for p in sorted({ref.page_no for ref in refs}))
                        blocks.append(
                            DocumentBlock(
                                block_id=f"docling:pages:{page_identity}:block:{len(blocks) + 1}",
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
                or any(type(data.get(k)) is not int for k in ('num_rows','num_cols'))
                or (data.get("num_rows"), data.get("num_cols")) not in ((3, 7), (1, 6), (3, 8), (2, 7), (2, 6), (2, 8))):
            return False
        bbox = prov[0].get("bbox") if isinstance(prov[0], dict) else None
        if (not isinstance(bbox, dict) or bbox.get("coord_origin") != "BOTTOMLEFT"
                or not isinstance(bbox.get("t"), (int, float))
                or not isinstance(bbox.get("b"), (int, float))
                or not 0 <= bbox["b"] < bbox["t"] <= 80):
            return False
        cells = data.get("table_cells")
        # Pages 34/51 export only the six labels of the same bottom stamp.
        # Require the complete literal row with unambiguous offsets; never
        # generalize the engineering table guard to arbitrary one-row tables.
        if (data["num_rows"], data["num_cols"]) == (1, 6):
            if not isinstance(cells, list) or len(cells) != 6:
                return False
            labels = ("Изм.", "Кол.уч", "Лист", "№ док.", "Подп.", "Дата")
            positions = {}
            for cell in cells:
                if not isinstance(cell, dict):
                    return False
                col = cell.get("start_col_offset_idx")
                if (type(col) is not int or not 0 <= col < 6 or col in positions
                        or cell.get("start_row_offset_idx") != 0
                        or cell.get("end_row_offset_idx") != 1
                        or cell.get("end_col_offset_idx") != col + 1
                        or cell.get("column_header") is not False
                        or cell.get("text") != labels[col]):
                    return False
                positions[col] = cell["text"]
            return len(positions) == 6
        if not isinstance(cells, list) or not 7 <= len(cells) <= 12:
            return False
        if any(not isinstance(c,dict) or not isinstance(c.get('text'),str) for c in cells):
            return False
        values = [c['text'].strip() for c in cells]
        variant=(data['num_rows'],data['num_cols']) in ((3,8),(2,7),(2,6),(2,8))
        split_number_stamp=((data['num_rows'],data['num_cols'])==(3,8)
                            and '№ Лист' in values and 'док.' in values)
        page=prov[0].get('page_no')
        if variant and (type(page) is not int or page<1):
            return False
        if variant and (any(type(bbox.get(k)) not in (int,float) or not math.isfinite(bbox[k])
                            for k in ('l','t','r','b'))
                        or not ((40<=bbox['l']<=50 or (split_number_stamp and 20<=bbox['l']<=25)) and 570<=bbox['r']<=585
                                and 50<=bbox['t']<=70 and 10<=bbox['b']<=20)):
            return False
        required = {"Изм.", "Кол.уч", "Подп.", "Дата", "Лист"}
        # Measured page-11 export joins adjacent stamp labels in one cell.
        # Expand only this exact known label pair; never split body text.
        labels = set(values)
        if "Кол.уч Лист" in labels:
            labels.update(("Кол.уч", "Лист"))
        if variant and 'Кол.уч Дата' in labels:
            labels.update(('Кол.уч','Дата'))
        if variant and '№ док. Лист' in labels:
            labels.add('№ док.')
        if split_number_stamp:
            labels.add('№ док.')
        if variant:
            required=required|{'№ док.'}
        if not required.issubset(labels):
            return False
        allowed = required | {"№ док.", "№ док. Лист", "Кол.уч Лист", "Лист №", "Пояснения"}
        if variant:
            allowed=allowed|{'Кол.уч Дата'}
            if split_number_stamp:
                allowed=allowed|{'№ Лист','док.'}
            code=r'[A-ZА-ЯЁ]{2,5}-[A-ZА-ЯЁ]{2,5}-\d{2}/\d{4}-\d+'
            if not any(re.fullmatch(code,v) or re.fullmatch(code+' '+str(page),v) for v in values):
                return False
            # New measured shapes must carry the actual source sheet number;
            # arbitrary numerical engineering values cannot be stamp cells.
            if not any(v==str(page) or re.fullmatch(code+' '+str(page),v) for v in values):
                return False
            return all(v in allowed or v==str(page) or re.fullmatch(code,v)
                       or re.fullmatch(code+' '+str(page),v) for v in values)
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
                    raise DocumentParseError("table cell is invalid")
                r, c = cell.get("start_row_offset_idx"), cell.get("start_col_offset_idx")
                if (not isinstance(r, int) or not isinstance(c, int)
                        or r < 0 or r >= count_rows or c < 0 or c >= count_cols
                        or cell.get("end_row_offset_idx") != r + 1
                        or cell.get("end_col_offset_idx") != c + 1
                        or (r, c) in grid or not isinstance(cell.get("text"), str)
                        or not cell["text"].strip()):
                    raise DocumentParseError("table cell is missing, merged or ambiguous")
                grid[r, c] = cell["text"].strip()
            if len(grid) != count_rows * count_cols:
                raise DocumentParseError("table grid has missing cells")
            # A complete grid can still contain the bottom drawing stamp
            # merged into body cells (observed in the V4 continuation export).
            stamp_labels = ("№ док.", "Подп.", "Кол.уч", "Изм.")
            if sum(any(label in value for value in grid.values())
                   for label in stamp_labels) >= 2:
                raise DocumentParseError("table contains mixed page stamp labels")
            # Never promote the first data row of a continuation to headings.
            # Support only one explicit, complete column-header row. Missing
            # metadata and multi-row/partial headers require source review.
            if any(type(cell.get("column_header")) is not bool
                   or cell["column_header"] != (cell["start_row_offset_idx"] == 0)
                   for cell in cells):
                raise DocumentParseError("table column header metadata is missing or ambiguous")
            headings = [grid[0, c] for c in range(count_cols)]
            # A cropped continuation can have a complete grid and still be
            # incorrectly labelled as a header by the model. Rebar quantities
            # observed in body rows require source review, even with True flags.
            # This is a conservative supplementary guard, not semantic proof.
            if any(re.search(r"\b\d+\s*[dDдД]\s*\d+\s*=\s*\d", heading)
                   for heading in headings):
                raise DocumentParseError("table header contains suspected rebar body data")
            if len(set(headings)) != count_cols:
                raise DocumentParseError("table column headers are duplicated")
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

"""Inspect bounded Docling table export without registering evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


def text_blocks(exported: dict) -> list[dict]:
    """Keep only text directly bound to a page; table cells are exported separately."""
    blocks: list[dict] = []
    seen: set[tuple[str, str, str]] = set()

    def visit(node: object) -> None:
        if isinstance(node, dict):
            value = node.get("text")
            provenance = node.get("prov") or node.get("provenance") or []
            if isinstance(provenance, dict):
                provenance = [provenance]
            if (isinstance(value, str) and value.strip() and isinstance(provenance, list)
                    and provenance and all(isinstance(ref, dict) and
                                           type(ref.get("page_no")) is int and
                                           ref["page_no"] > 0 for ref in provenance)):
                kind = str(node.get("label") or node.get("type") or "text")
                key = (kind, value.strip(), json.dumps(provenance, sort_keys=True))
                if key not in seen:
                    seen.add(key)
                    blocks.append({"kind": kind, "text": value.strip(),
                                   "provenance": provenance})
            for child in node.values():
                visit(child)
        elif isinstance(node, list):
            for child in node:
                visit(child)

    visit(exported)
    return blocks


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--page", type=int, required=True)
    parser.add_argument("--end", type=int, help="Last page (at most two pages total)")
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--include-blocks", action="store_true",
                        help="Include page-bound text and captions for region review")
    args = parser.parse_args()
    end = args.end or args.page
    if args.page < 1 or end < args.page or end - args.page > 1:
        parser.error("choose one or two positive pages")
    with args.source.open("rb") as handle:
        digest = hashlib.file_digest(handle, "sha256").hexdigest()
    if digest != args.sha256.lower():
        print("BLOCK: source checksum mismatch", file=sys.stderr)
        return 2
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from engineering.document_intelligence.docling_adapter import DoclingDocumentParser

    result = DoclingDocumentParser()._converter().convert(str(args.source), page_range=(args.page, end))
    exported = result.document.export_to_dict()
    tables = []
    for table in exported.get("tables", []):
        data = table.get("data") or {}
        tables.append({
            "provenance": table.get("prov", []),
            "num_rows": data.get("num_rows"), "num_cols": data.get("num_cols"),
            "cells": [{key: cell.get(key) for key in (
                "text", "start_row_offset_idx", "end_row_offset_idx",
                "start_col_offset_idx", "end_col_offset_idx")}
                for cell in data.get("table_cells", [])],
        })
    payload = {"source_sha256": digest, "page_start": args.page, "page_end": end, "tables": tables}
    if args.include_blocks:
        payload["text_blocks"] = text_blocks(exported)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print("TABLES:", len(tables))
    print("CELLS:", [len(table["cells"]) for table in tables])
    print("OUTPUT:", args.output)
    print("UNCERTAINTY: inspect exported cells against the page image")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

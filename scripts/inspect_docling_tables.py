"""Inspect bounded Docling table export without registering evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--page", type=int, required=True)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.page < 1:
        parser.error("page must be positive")
    with args.source.open("rb") as handle:
        digest = hashlib.file_digest(handle, "sha256").hexdigest()
    if digest != args.sha256.lower():
        print("BLOCK: source checksum mismatch", file=sys.stderr)
        return 2
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from engineering.document_intelligence.docling_adapter import DoclingDocumentParser

    result = DoclingDocumentParser()._converter().convert(str(args.source), page_range=(args.page, args.page))
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
    payload = {"source_sha256": digest, "page": args.page, "tables": tables}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print("TABLES:", len(tables))
    print("CELLS:", [len(table["cells"]) for table in tables])
    print("OUTPUT:", args.output)
    print("UNCERTAINTY: inspect exported cells against the page image")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

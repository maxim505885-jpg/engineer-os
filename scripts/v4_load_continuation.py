"""Recover the V4 page 254 load-table continuation using its page 253 header.

This is a region-level cross-check, not acceptance of the page or calculations.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path

import pdfplumber


def _flat(value: str) -> str:
    return re.sub(r"\s+", "", value)


def recover(source: Path, review: dict, exported: dict) -> dict:
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    if (digest != review.get("source_sha256") or digest != exported.get("source_sha256")
            or review.get("status") != "BLOCK" or
            254 not in review.get("isolated_pages", [])
            or (exported.get("page_start"), exported.get("page_end")) != (254, 254)):
        raise ValueError("source, export, or blocked-page identity mismatch")
    tables = exported.get("tables", [])
    if not tables or (tables[0].get("num_rows"), tables[0].get("num_cols")) != (14, 5):
        raise ValueError("expected 14-by-5 continuation table")
    if [p.get("page_no") for p in tables[0].get("provenance", [])] != [254]:
        raise ValueError("continuation table page provenance mismatch")
    grid: list[list[str | None]] = [[None] * 5 for _ in range(14)]
    for cell in tables[0].get("cells", []):
        r, c = cell.get("start_row_offset_idx"), cell.get("start_col_offset_idx")
        if (not isinstance(r, int) or not isinstance(c, int) or not 0 <= r < 14 or not 0 <= c < 5
                or cell.get("end_row_offset_idx") != r + 1
                or cell.get("end_col_offset_idx") != c + 1 or grid[r][c] is not None
                or not isinstance(cell.get("text"), str) or not cell["text"].strip()):
            raise ValueError("invalid, merged, duplicate, or empty continuation cell")
        grid[r][c] = cell["text"]
    if any(value is None for row in grid for value in row):
        raise ValueError("continuation has missing cells")
    with pdfplumber.open(source) as pdf:
        if len(pdf.pages) != 534:
            raise ValueError("source page count mismatch")
        headers = [t[0] for t in pdf.pages[252].extract_tables()
                   if len(t) == 6 and all(len(row) == 5 for row in t)]
        bodies = [t for t in pdf.pages[253].extract_tables()
                  if len(t) == 14 and all(len(row) == 5 for row in t)]
    if len(headers) != 1 or len(bodies) != 1 or any(
            not isinstance(v, str) or not v.strip() for v in headers[0]):
        raise ValueError("unique preceding header or continuation table missing")
    if any(_flat(grid[r][c]) != _flat(bodies[0][r][c] or "")
           for r in range(14) for c in range(5)):
        raise ValueError("Docling cells disagree with independent PDF table extraction")
    identifiers = [str(row[0]) for row in grid]
    if identifiers != [str(n) for n in range(6, 16)] + [f"{n} (S)" for n in range(16, 20)]:
        raise ValueError("continuation sequence is broken")
    return {"source_sha256": digest, "page": 254, "page_status": "UNCERTAINTY",
            "region_status": "UNCERTAINTY", "header_source_page": 253,
            "header": headers[0], "rows": grid,
            "cross_check": "70/70 Docling cells match independent PDF table extraction",
            "unverified": "Other tables, prose, formulas, figures, and engineering calculation."}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("review", type=Path)
    parser.add_argument("export_zip", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    with zipfile.ZipFile(args.export_zip) as archive:
        exported = json.loads(archive.read("page-254.json"))
    result = recover(args.source, json.loads(args.review.read_text(encoding="utf-8")), exported)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("ROWS:", len(result["rows"]))
    print("REGION:", result["region_status"])
    print("PAGE:", result["page_status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Export all blocked-page PDF table candidates without accepting any page.

This independent geometry pass is useful when Docling cannot reconstruct a
table. Pdfplumber can misread page frames, stamps, colours and merged cells;
every emitted grid therefore remains an unverified candidate.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pdfplumber


def collect(source: Path, review: dict) -> dict:
    with source.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    if review.get("source_sha256") != digest or review.get("status") != "BLOCK":
        raise ValueError("source identity or review status mismatch")
    reasons = {int(page): reason for reason, pages in review["blocked_reasons"].items()
               for page in pages}
    if len(reasons) != sum(map(len, review["blocked_reasons"].values())):
        raise ValueError("duplicate blocked page reason")
    pages = []
    with pdfplumber.open(source) as pdf:
        if len(pdf.pages) != review.get("page_count"):
            raise ValueError("PDF page count mismatch")
        for number in sorted(reasons):
            if not 1 <= number <= len(pdf.pages):
                raise ValueError(f"blocked page out of bounds: {number}")
            page = pdf.pages[number - 1]
            candidates = []
            for table in page.find_tables():
                x0, y0, x1, y1 = table.bbox
                # The 10-point page frame encloses the entire A4 sheet. The
                # threshold only rejects obvious frames; it does not certify
                # that a remaining region is a real body table.
                if (len(table.rows) < 2 or len(table.columns) < 2 or x0 <= 30
                        or x1 >= page.width - 5 or y0 >= page.height - 80 or y1 <= 80):
                    continue
                grid = table.extract()
                if not grid or any(len(row) != len(table.columns) for row in grid):
                    raise ValueError(f"nonrectangular table candidate on page {number}")
                nonempty = sum(bool(isinstance(cell, str) and cell.strip())
                               for row in grid for cell in row)
                candidates.append({
                    "bbox_pdf_top_left": [round(v, 2) for v in table.bbox],
                    "rows": len(grid), "columns": len(table.columns),
                    "nonempty_cells": nonempty,
                    "total_grid_positions": len(grid) * len(table.columns),
                    "first_row_is_numbered_data": bool(grid[0][0] and
                        str(grid[0][0]).strip().splitlines()[0].isdigit()),
                    "touches_bottom_80pt": y1 >= page.height - 80,
                    "raw_grid": grid,
                })
            pages.append({"page": number, "reason": reasons[number],
                          "page_status": "BLOCK", "candidates": candidates})
    return {"source_sha256": digest, "status": "BLOCK", "page_count": len(pages),
            "pages_with_candidates": sum(bool(p["candidates"]) for p in pages),
            "candidate_tables": sum(len(p["candidates"]) for p in pages),
            "note": "Raw PDF geometry candidates only; compare all cells, captions, images, colours, formulae and stamps with source pages.",
            "pages": pages}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("review", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = collect(args.source, json.loads(args.review.read_text(encoding="utf-8")))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, separators=(",", ":")) + "\n",
                           encoding="utf-8")
    print("BLOCKED_PAGES:", result["page_count"])
    print("PAGES_WITH_CANDIDATES:", result["pages_with_candidates"])
    print("CANDIDATE_TABLES:", result["candidate_tables"])
    print("STATUS: BLOCK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

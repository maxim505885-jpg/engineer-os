"""Cross-check V4 drawing-register transcriptions against source PDF table cells."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.v4_manual_evidence import validate


def _normalized(value: str) -> str:
    # Line wrapping may split a number after a hyphen; punctuation itself matters.
    return re.sub(r"\s+", "", value).rstrip(";.")


def compare_rows(rows: list, claims: dict[str, str]) -> list[dict]:
    mismatches = []
    for locator, claimed in claims.items():
        figure = int(locator)
        matches = [row for row in rows if isinstance(row, list) and len(row) >= 2
                   and str(row[0]) == locator and isinstance(row[1], str)]
        if len(matches) != 1:
            mismatches.append({"figure": figure, "reason": f"SOURCE_ROW_COUNT_{len(matches)}"})
        elif _normalized(claimed) != _normalized(matches[0][1]):
            mismatches.append({"figure": figure, "reason": "TEXT_MISMATCH"})
        if len(matches) == 1 and len(matches[0]) >= 3 and str(matches[0][2] or "").strip():
            mismatches.append({"figure": figure, "reason": "NONEMPTY_NOTE"})
    for row in rows:
        if (isinstance(row, list) and row and str(row[0]).isdigit()
                and str(row[0]) not in claims):
            mismatches.append({"figure": int(row[0]), "reason": "UNPLANNED_SOURCE_ROW"})
    return mismatches


def check(source: Path, review: Path, evidence_path: Path) -> dict:
    import pdfplumber  # Optional dependency for this independent diagnostic.

    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    validate(source, review, evidence)
    mismatches = []
    checked = 0
    with pdfplumber.open(source) as pdf:
        for entry in evidence["pages"]:
            page = entry["page"]
            if page not in (490, 491):
                continue
            claims = {item["locator"]: item["transcription"] for item in entry["claims"]
                      if item["locator"].isdigit()}
            expected = set(claims)
            tables = pdf.pages[page - 1].extract_tables()
            candidates = [table for table in tables if
                          expected.issubset({str(row[0]) for row in table if row and row[0]})]
            if len(candidates) != 1:
                raise ValueError(f"page {page} has {len(candidates)} matching register tables")
            checked += len(claims)
            mismatches.extend({"page": page, **item} for item in
                              compare_rows(candidates[0], claims))
    if checked != 43:
        raise ValueError("drawing register must contain all 43 numbered claims")
    return {"checked_rows": checked, "mismatches": mismatches, "status": "BLOCK"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("review", type=Path)
    parser.add_argument("evidence", type=Path)
    args = parser.parse_args()
    result = check(args.source, args.review, args.evidence)
    print(json.dumps(result, ensure_ascii=False))
    return 2 if result["mismatches"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Build page-bound, region-only evidence for the checked V4 drawing register."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.v4_drawing_register_check import check


def assemble(evidence: dict, verification: dict, *, expected_rows: int = 43) -> dict:
    if (evidence.get("status") != "BLOCK" or verification.get("status") != "BLOCK"
            or verification.get("mismatches") or
            verification.get("checked_rows") != expected_rows):
        raise ValueError("manual register verification failed")
    pages = evidence.get("pages", [])
    selected = [entry for entry in pages if entry.get("page") in (490, 491)]
    if not selected:
        raise ValueError("register pages are missing")
    blocks = []
    row_numbers = []
    for entry in selected:
        page = entry["page"]
        claims = {item["locator"]: item["transcription"] for item in entry["claims"]}
        for locator in ("register_heading", "category_heading"):
            if locator in claims:
                blocks.append({"block_id": f"manual:register:{page}:{locator}",
                               "kind": "section_heading", "text": claims[locator],
                               "provenance": [{"page_no": page}]})
        for locator in sorted((key for key in claims if key.isdigit()), key=int):
            row_numbers.append(int(locator))
            blocks.append({"block_id": f"manual:register:{page}:row:{locator}",
                           "kind": "table_row", "text": claims[locator],
                           "provenance": [{"page_no": page}]})
    if len(row_numbers) != expected_rows or sorted(row_numbers) != list(range(1, expected_rows + 1)):
        raise ValueError("register rows are missing or duplicated")
    return {"source_sha256": evidence["source_sha256"],
            "parser": "manual_register_verified_by_pdf_table_cells",
            "page_start": 490, "page_end": 491,
            "status": "BLOCK", "region_status": "UNCERTAINTY",
            "scope": "drawing register text only; other page regions and drawings remain blocked",
            "blocks": blocks}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("review", type=Path)
    parser.add_argument("evidence", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    verification = check(args.source, args.review, args.evidence)
    data = json.loads(args.evidence.read_text(encoding="utf-8"))
    result = assemble(data, verification)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")
    print("REGISTER_ROWS:", verification["checked_rows"])
    print("REGION_STATUS:", result["region_status"])
    print("PAGE_STATUS:", result["status"])
    print("OUTPUT:", args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

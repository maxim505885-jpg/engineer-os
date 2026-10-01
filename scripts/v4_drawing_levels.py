"""Compare drawing-register decimal levels with the independent PDF text layer."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.v4_manual_evidence import validate

DECIMAL = re.compile(r"[+−-]?\d+[.,]\d+")
FIGURE = re.compile(r"Рисунок\s+Ж\.(\d+)\.")


def compare_levels(page_text: str, claims: dict[str, str]) -> list[dict]:
    markers = list(FIGURE.finditer(page_text))
    regions = {int(match.group(1)): page_text[match.end():
               markers[index + 1].start() if index + 1 < len(markers) else len(page_text)]
               for index, match in enumerate(markers)}
    mismatches = []
    for locator, transcription in claims.items():
        figure = int(locator)
        claimed = DECIMAL.findall(transcription)
        source = DECIMAL.findall(regions[figure]) if figure in regions else None
        if source != claimed:
            mismatches.append({"figure": figure, "claimed": claimed, "source": source})
    return mismatches


def check(source: Path, review: Path, evidence_path: Path) -> dict:
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    coverage = validate(source, review, evidence)
    mismatches = []
    checked = 0
    for entry in evidence["pages"]:
        page = entry["page"]
        if page not in (490, 491):
            continue
        claims = {item["locator"]: item["transcription"] for item in entry["claims"]
                  if item["locator"].isdigit()}
        result = subprocess.run(["pdftotext", "-f", str(page), "-l", str(page),
                                 "-layout", str(source), "-"],
                                capture_output=True, text=True, check=True)
        checked += len(claims)
        mismatches.extend({"page": page, **item} for item in compare_levels(result.stdout, claims))
    if checked != 43:
        raise ValueError("drawing register must contain all 43 numbered claims")
    return {"checked_figures": checked, "mismatches": mismatches,
            "manual_coverage": coverage["claims"], "status": "BLOCK"}


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

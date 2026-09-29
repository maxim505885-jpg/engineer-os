"""Record a separately verified manual page route without rewriting Docling audits."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.v4_drawing_register_check import check
from scripts.v4_manual_register_recovery import assemble


def overlay(review: dict, recovered: dict, page_texts: dict[int, str],
            *, expected_rows: int = 43) -> dict:
    if (review.get("status") != "BLOCK" or recovered.get("status") != "BLOCK"
            or recovered.get("region_status") != "UNCERTAINTY"
            or review.get("source_sha256") != recovered.get("source_sha256")):
        raise ValueError("source or recovery status mismatch")
    reasons = review.get("blocked_reasons", {})
    blocked = {p for pages in reasons.values() for p in pages}
    if not {490, 491}.issubset(blocked):
        raise ValueError("manual pages are not both in the blocked queue")
    rows = [b for b in recovered.get("blocks", []) if b.get("kind") == "table_row"]
    if len(rows) != expected_rows:
        raise ValueError("manual register row count mismatch")
    seen = set()
    for block in rows:
        match = re.match(r"^Рисунок Ж\.(\d+)\.", block.get("text", ""))
        refs = block.get("provenance")
        if not match or not isinstance(refs, list) or len(refs) != 1:
            raise ValueError("manual row provenance is invalid")
        number = int(match.group(1))
        page = refs[0].get("page_no")
        if page not in (490, 491) or number in seen or f"Рисунок Ж.{number}." not in page_texts.get(page, ""):
            raise ValueError("manual row is absent from its source page")
        seen.add(number)
    if seen != set(range(1, expected_rows + 1)):
        raise ValueError("manual register numbering is incomplete")
    shell = {490: ("Приложение Ж", "Ведомость чертежей", "Наименование", "Примечание"),
             491: ("Результаты геодезических измерений",)}
    common_stamp = ("ОСК-ССК-22/0526-1", "Взаи. инв. №", "Инв. № подл.",
                    "Подп. и дата", "Изм.", "Кол.уч", "Лист", "№ док.",
                    "Подп.", "Дата")
    for page, labels in shell.items():
        text = page_texts.get(page, "")
        if any(label not in text for label in (*labels, *common_stamp, str(page))):
            raise ValueError(f"page {page} shell text is incomplete")
    return {"source_sha256": recovered["source_sha256"],
            "original_blocked_pages": len(blocked),
            "remaining_blocked_pages": len(blocked - {490, 491}),
            "manual_page_status": {"490": "UNCERTAINTY", "491": "UNCERTAINTY"},
            "status": "BLOCK", "review_path": "docs/V4_PAGE_488_MANUAL_REVIEW.md",
            "note": "Additive manual route; original Docling audits remain blocked and unchanged."}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("source", "review", "evidence", "recovered", "output"):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    original = json.loads(args.review.read_text(encoding="utf-8"))
    recovered = json.loads(args.recovered.read_text(encoding="utf-8"))
    verification = check(args.source, args.review, args.evidence)
    evidence = json.loads(args.evidence.read_text(encoding="utf-8"))
    if recovered != assemble(evidence, verification):
        raise ValueError("recovered register differs from verified source")
    result = subprocess.run(["pdftotext", "-f", "490", "-l", "491", "-layout",
                             str(args.source), "-"], capture_output=True, text=True, check=True)
    texts = result.stdout.split("\f")
    if len(texts) < 2:
        raise ValueError("page text layer is incomplete")
    outcome = overlay(original, recovered, {490: texts[0], 491: texts[1]})
    with args.source.open("rb") as stream:
        if hashlib.file_digest(stream, "sha256").hexdigest() != outcome["source_sha256"]:
            raise ValueError("source PDF SHA-256 mismatch")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(outcome, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")
    print("MANUAL_PAGE_STATUS:", outcome["manual_page_status"])
    print("REMAINING_BLOCKED:", outcome["remaining_blocked_pages"])
    print("DOCUMENT_STATUS:", outcome["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

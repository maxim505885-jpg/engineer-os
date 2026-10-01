"""Retry only known V4 pages blocked by the validated 1x6 footer stamp."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.local_docling_batch import run_chunk
from scripts.run_v4_local import DOCUMENT_ID, PROJECT_ID, SOURCE_SHA256
from scripts.v4_extraction_review import review

FOOTER_PAGES = (18, 34, 51, 100, 170, 254)


def retry(directory: Path, *, source: Path, run=run_chunk) -> dict:
    before = review(directory, 534)
    for page in FOOTER_PAGES:
        if page not in before["blocked_reasons"].get("OTHER_EXTRACTION_FAILURE", []):
            raise ValueError(f"page {page} has changed status; inspect before retry")
        audit = json.loads((directory / f"pages-{page:04d}-{page:04d}.audit.json").read_text(encoding="utf-8"))
        if (audit.get("source_sha256") != SOURCE_SHA256 or audit.get("project_id") != PROJECT_ID
                or audit.get("document_id") != DOCUMENT_ID or audit.get("page_start") != page
                or audit.get("page_end") != page or "table dimensions are invalid" not in audit.get("stderr", "")):
            raise ValueError(f"page {page} audit does not match the confirmed footer failure")
    args = SimpleNamespace(source=source, output_dir=directory, sha256=SOURCE_SHA256,
                           project_id=PROJECT_ID, document_id=DOCUMENT_ID)
    for page in FOOTER_PAGES:
        print(f"RETRY FOOTER page {page}", flush=True)
        run(args, page, page)
    return review(directory, 534)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    with args.source.open("rb") as handle:
        if hashlib.file_digest(handle, "sha256").hexdigest() != SOURCE_SHA256:
            parser.error("V4 source SHA-256 mismatch")
    result = retry(args.directory, source=args.source)
    output = args.directory / "v4-extraction-review.json"
    temporary = output.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(output)
    print("BLOCKED_REASONS:", {reason: len(pages) for reason, pages in result["blocked_reasons"].items()})
    print("REVIEW:", output)
    print("STATUS:", result["status"])
    return 2 if result["status"] == "BLOCK" else 0


if __name__ == "__main__":
    raise SystemExit(main())

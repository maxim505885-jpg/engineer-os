"""Recheck only V4 pages whose old audit hides the table failure reason."""

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


def retry_legacy(directory: Path, page_count: int, *, source: Path | None = None, run=None) -> tuple[int, dict]:
    previous = review(directory, page_count)
    pages = previous["blocked_reasons"].get("AMBIGUOUS_TABLE_CELL_OLD_AUDIT", [])
    args = SimpleNamespace(source=source, output_dir=directory, sha256=SOURCE_SHA256,
                           project_id=PROJECT_ID, document_id=DOCUMENT_ID)
    for page in pages:
        print(f"RECHECK page {page}/{page_count}", flush=True)
        (run or run_chunk)(args, page, page)
    return len(pages), review(directory, page_count)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--pages", type=int, default=534)
    args = parser.parse_args()
    if not args.source.is_file():
        parser.error("V4 source PDF is unavailable")
    with args.source.open("rb") as handle:
        if hashlib.file_digest(handle, "sha256").hexdigest() != SOURCE_SHA256:
            parser.error("V4 source SHA-256 mismatch")
    count, result = retry_legacy(args.directory, args.pages, source=args.source)
    output = args.directory / "v4-extraction-review.json"
    temporary = output.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(output)
    print(f"RECHECKED: {count}")
    print("BLOCKED_REASONS:", {reason: len(pages) for reason, pages in result["blocked_reasons"].items()})
    print(f"REVIEW: {output}")
    print(f"STATUS: {result['status']}")
    return 2 if result["status"] == "BLOCK" else 0


if __name__ == "__main__":
    raise SystemExit(main())

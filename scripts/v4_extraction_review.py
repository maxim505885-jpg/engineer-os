"""Summarize every V4 extraction chunk without accepting document evidence."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.local_docling_batch import CHECK_VERSION, reusable_output
from scripts.run_v4_local import DOCUMENT_ID, PROJECT_ID, SOURCE_SHA256


def review(directory: Path, page_count: int) -> dict:
    if page_count < 1:
        raise ValueError("page count must be positive")
    issues = []
    present_pages = set()
    missing_provenance_pages = set()
    successful_chunks = 0
    blocked_chunks = 0
    total_blocks = 0
    for first in range(1, page_count + 1, 2):
        last = min(first + 1, page_count)
        stem = f"pages-{first:04d}-{last:04d}"
        audit_path = directory / f"{stem}.audit.json"
        output_path = directory / f"{stem}.json"
        try:
            audit = json.loads(audit_path.read_text(encoding="utf-8"))
            if not isinstance(audit, dict) or any(audit.get(key) != value for key, value in (
                ("source_sha256", SOURCE_SHA256), ("project_id", PROJECT_ID),
                ("document_id", DOCUMENT_ID), ("page_start", first),
                ("page_end", last), ("check_version", CHECK_VERSION),
                ("exit_code", 0),
            )):
                raise ValueError("audit mismatch or failed extraction")
            if not reusable_output(output_path, first=first, last=last,
                    sha256=SOURCE_SHA256, project_id=PROJECT_ID, document_id=DOCUMENT_ID):
                raise ValueError("output invalid or missing")
            output = json.loads(output_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, ValueError, TypeError) as exc:
            blocked_chunks += 1
            issues.append({"chunk": stem, "reason": str(exc)})
            continue
        successful_chunks += 1
        total_blocks += len(output["blocks"])
        located = {ref["page_no"] for block in output["blocks"]
                   for ref in block["provenance"]}
        present_pages.update(located)
        missing_provenance_pages.update(set(range(first, last + 1)) - located)
    return {
        "source_sha256": SOURCE_SHA256, "project_id": PROJECT_ID,
        "document_id": DOCUMENT_ID, "page_count": page_count,
        "successful_chunks": successful_chunks, "blocked_chunks": blocked_chunks,
        "blocks": total_blocks, "pages_with_extracted_blocks": len(present_pages),
        "pages_without_extracted_blocks": sorted(missing_provenance_pages),
        "issues": issues, "status": "BLOCK" if blocked_chunks else "UNCERTAINTY",
        "note": "Extraction inventory only; pages and engineering conclusions require review",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--pages", type=int, required=True)
    args = parser.parse_args()
    result = review(args.directory, args.pages)
    path = args.directory / "v4-extraction-review.json"
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)
    print(f"REVIEW: {path}")
    print(f"CHUNKS: {result['successful_chunks']} passed, {result['blocked_chunks']} blocked")
    print(f"PAGES_WITH_BLOCKS: {result['pages_with_extracted_blocks']}/{result['page_count']}")
    print(f"STATUS: {result['status']}")
    return 2 if result["blocked_chunks"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Summarize every V4 extraction chunk without accepting document evidence."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.local_docling_batch import CHECK_VERSION, reusable_output
from scripts.run_v4_local import DOCUMENT_ID, PROJECT_ID, SOURCE_SHA256


def blocked_reason(directory: Path, page: int) -> str:
    """Classify a failed page from its source-bound audit without changing its status."""
    try:
        data = json.loads((directory / f"pages-{page:04d}-{page:04d}.audit.json").read_text(encoding="utf-8"))
        if (not isinstance(data, dict) or data.get("source_sha256") != SOURCE_SHA256
                or data.get("project_id") != PROJECT_ID or data.get("document_id") != DOCUMENT_ID
                or data.get("page_start") != page or data.get("page_end") != page):
            return "AUDIT_MISSING_OR_INVALID"
        error = data.get("stderr", "")
        if not isinstance(error, str):
            return "AUDIT_MISSING_OR_INVALID"
    except (OSError, UnicodeError, ValueError):
        return "AUDIT_MISSING_OR_INVALID"
    if "merged cell" in error:
        return "MERGED_TABLE_CELL"
    if "grid has missing cells" in error:
        return "MISSING_TABLE_CELLS"
    if "empty cell" in error:
        return "EMPTY_TABLE_CELL"
    if "dropped table cells" in error:
        return "DROPPED_TABLE_CELLS"
    if "table cell is missing, merged or ambiguous" in error:
        return "AMBIGUOUS_TABLE_CELL_OLD_AUDIT"
    return "OTHER_EXTRACTION_FAILURE"


def load_chunk(directory: Path, first: int, last: int) -> dict:
    stem = f"pages-{first:04d}-{last:04d}"
    audit = json.loads((directory / f"{stem}.audit.json").read_text(encoding="utf-8"))
    if not isinstance(audit, dict) or any(audit.get(key) != value for key, value in (
        ("source_sha256", SOURCE_SHA256), ("project_id", PROJECT_ID),
        ("document_id", DOCUMENT_ID), ("page_start", first),
        ("page_end", last), ("check_version", CHECK_VERSION),
        ("exit_code", 0),
    )):
        raise ValueError("audit mismatch or failed extraction")
    path = directory / f"{stem}.json"
    if not reusable_output(path, first=first, last=last, sha256=SOURCE_SHA256,
                           project_id=PROJECT_ID, document_id=DOCUMENT_ID):
        raise ValueError("output invalid or missing")
    return json.loads(path.read_text(encoding="utf-8"))


def review(directory: Path, page_count: int) -> dict:
    if page_count < 1:
        raise ValueError("page count must be positive")
    issues = []
    present_pages = set()
    missing_provenance_pages = set()
    successful_chunks = 0
    blocked_chunks = 0
    total_blocks = 0
    page_counts = {page: {"blocks": 0, "table_rows": 0} for page in range(1, page_count + 1)}
    blocked_pages = set()
    blocked_reasons: dict[str, list[int]] = {}
    isolated_pages = []
    for first in range(1, page_count + 1, 2):
        last = min(first + 1, page_count)
        try:
            chunks = [(first, last, load_chunk(directory, first, last))]
        except (OSError, UnicodeError, ValueError, TypeError):
            chunks = []
            for page in range(first, last + 1):
                try:
                    chunks.append((page, page, load_chunk(directory, page, page)))
                    isolated_pages.append(page)
                except (OSError, UnicodeError, ValueError, TypeError) as exc:
                    blocked_chunks += 1
                    blocked_pages.add(page)
                    reason = blocked_reason(directory, page)
                    blocked_reasons.setdefault(reason, []).append(page)
                    issues.append({"chunk": f"pages-{page:04d}-{page:04d}", "reason": str(exc), "category": reason})
        for chunk_first, chunk_last, output in chunks:
            successful_chunks += 1
            total_blocks += len(output["blocks"])
            located = {ref["page_no"] for block in output["blocks"]
                       for ref in block["provenance"]}
            present_pages.update(located)
            missing_provenance_pages.update(set(range(chunk_first, chunk_last + 1)) - located)
            for block in output["blocks"]:
                for page in {ref["page_no"] for ref in block["provenance"]}:
                    page_counts[page]["blocks"] += 1
                    if block.get("kind") == "table_row":
                        page_counts[page]["table_rows"] += 1
    queue = []
    for page, counts in page_counts.items():
        if page in blocked_pages:
            priority, reason = 1, "EXTRACTION_BLOCKED"
        elif page in missing_provenance_pages:
            priority, reason = 2, "NO_EXTRACTED_BLOCKS"
        elif counts["table_rows"]:
            priority, reason = 3, "TABLE_REQUIRES_VISUAL_REVIEW"
        else:
            priority, reason = 4, "TEXT_REQUIRES_SEMANTIC_REVIEW"
        queue.append({"page": page, "priority": priority, "reason": reason, **counts})
    queue.sort(key=lambda item: (item["priority"], item["page"]))
    return {
        "source_sha256": SOURCE_SHA256, "project_id": PROJECT_ID,
        "document_id": DOCUMENT_ID, "page_count": page_count,
        "successful_chunks": successful_chunks, "blocked_chunks": blocked_chunks,
        "blocks": total_blocks, "pages_with_extracted_blocks": len(present_pages),
        "pages_without_extracted_blocks": sorted(missing_provenance_pages),
        "isolated_pages": isolated_pages,
        "blocked_reasons": blocked_reasons,
        "review_queue": queue,
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
    print("BLOCKED_REASONS:", {reason: len(pages) for reason, pages in result["blocked_reasons"].items()})
    print(f"STATUS: {result['status']}")
    return 2 if result["blocked_chunks"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Read V4 extraction audits and produce a source-bound manual review queue."""

import argparse
import json
from pathlib import Path


def triage(directory: Path) -> dict:
    review = json.loads((directory / "v4-extraction-review.json").read_text(encoding="utf-8"))
    reasons = review["blocked_reasons"]
    other = []
    for page in reasons.get("OTHER_EXTRACTION_FAILURE", []):
        path = directory / f"pages-{page:04d}-{page:04d}.audit.json"
        try:
            audit = json.loads(path.read_text(encoding="utf-8"))
            if any(audit.get(key) != review.get(key) for key in
                   ("source_sha256", "project_id", "document_id")) or (audit.get("page_start"), audit.get("page_end")) != (page, page):
                raise ValueError("source or page identity mismatch")
            stderr = audit.get("stderr", "")
            if not isinstance(stderr, str):
                raise ValueError("invalid stderr")
            message = next((line.strip() for line in reversed(stderr.splitlines()) if line.strip()), "no error text")
        except (OSError, ValueError, TypeError) as exc:
            message = f"AUDIT_UNAVAILABLE_OR_INVALID: {exc}"
        other.append({"page": page, "message": message})
    queue = [{"page": page, "reason": reason, "status": "BLOCK"}
             for reason, pages in reasons.items() for page in pages]
    queue.sort(key=lambda item: item["page"])
    return {"source_sha256": review["source_sha256"], "page_count": review["page_count"],
            "status": "BLOCK", "other_failures": other, "manual_review_queue": queue,
            "note": "Diagnostic inventory only; no evidence or engineering conclusion accepted."}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    result = triage(args.directory)
    target = args.directory / "v4-block-triage.json"
    temporary = target.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(target)
    print("OTHER_EXTRACTION_FAILURE:")
    for item in result["other_failures"]:
        print(f"  page {item['page']}: {item['message']}")
    print(f"MANUAL_REVIEW_QUEUE: {len(result['manual_review_queue'])} pages")
    print(f"REPORT: {target}")
    print("STATUS: BLOCK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

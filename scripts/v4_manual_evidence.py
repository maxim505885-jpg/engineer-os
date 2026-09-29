"""Validate partial, source-bound manual transcriptions without accepting a page."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def validate(source: Path, review_path: Path, evidence: dict) -> dict:
    review = json.loads(review_path.read_text(encoding="utf-8"))
    with source.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    if digest != review.get("source_sha256") or digest != evidence.get("source_sha256"):
        raise ValueError("source PDF SHA-256 mismatch")
    if review.get("status") != "BLOCK" or evidence.get("status") != "BLOCK":
        raise ValueError("manual evidence must retain BLOCK status")
    reasons = review.get("blocked_reasons")
    if not isinstance(reasons, dict):
        raise ValueError("blocked page list is invalid")
    blocked = {page for entries in reasons.values() if isinstance(entries, list)
               for page in entries if isinstance(page, int)}
    pages = evidence.get("pages")
    if not isinstance(pages, list) or not pages:
        raise ValueError("manual evidence needs pages")
    seen_pages = set()
    count = 0
    for entry in pages:
        if not isinstance(entry, dict) or not isinstance(entry.get("page"), int):
            raise ValueError("manual evidence page is invalid")
        page = entry["page"]
        if page not in blocked or page in seen_pages:
            raise ValueError(f"page {page} is not a unique blocked page")
        seen_pages.add(page)
        claims = entry.get("claims")
        if not isinstance(claims, list) or not claims:
            raise ValueError(f"page {page} has no claims")
        locators = set()
        for claim in claims:
            if not isinstance(claim, dict):
                raise ValueError("claim is invalid")
            locator, value = claim.get("locator"), claim.get("transcription")
            if (not isinstance(locator, str) or not locator.strip() or locator in locators
                    or claim.get("source") != "rendered_pdf" or not isinstance(value, str)
                    or (not value.strip() and claim.get("observed_blank") is not True)
                    or (value.strip() and claim.get("observed_blank") is True)):
                raise ValueError(f"page {page} has invalid or duplicate claim")
            locators.add(locator)
            count += 1
    return {"pages": len(seen_pages), "claims": count, "status": "BLOCK"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("review", type=Path)
    parser.add_argument("evidence", type=Path)
    args = parser.parse_args()
    evidence = json.loads(args.evidence.read_text(encoding="utf-8"))
    print(json.dumps(validate(args.source, args.review, evidence), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

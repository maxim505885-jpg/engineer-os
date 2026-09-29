"""Export source-bound PDF text from blocked V4 pages for offline comparison."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path


def export(source: Path, review_path: Path, output: Path, *, runner=subprocess.run) -> dict:
    review = json.loads(review_path.read_text(encoding="utf-8"))
    with source.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    if digest != review.get("source_sha256"):
        raise ValueError("source PDF SHA-256 mismatch")
    if review.get("status") != "BLOCK" or not isinstance(review.get("page_count"), int):
        raise ValueError("extraction review is not a blocked page inventory")
    page_count = review["page_count"]
    if page_count < 1 or not isinstance(review.get("blocked_reasons"), dict):
        raise ValueError("extraction review has invalid pages")
    blocked = [page for pages in review["blocked_reasons"].values() for page in pages]
    if (not blocked or any(not isinstance(page, int) or page < 1 or page > page_count
                           for page in blocked) or len(set(blocked)) != len(blocked)):
        raise ValueError("extraction review has invalid blocked page numbers")
    result = runner(["pdftotext", "-layout", str(source), "-"],
                    capture_output=True, text=True, check=True)
    content = result.stdout.split("\f")
    if len(content) == page_count + 1 and not content[-1].strip():
        content.pop()
    if len(content) != page_count:
        raise ValueError("PDF text page count mismatch")
    output.mkdir(parents=True, exist_ok=True)
    entries = []
    for page in sorted(blocked):
        text = content[page - 1].strip()
        raw = text.encode("utf-8")
        (output / f"page-{page:04d}.txt").write_bytes(raw)
        characters = len("".join(text.split()))
        route = "NO_TEXT_LAYER" if characters == 0 else (
            "SPARSE_TEXT_LAYER" if characters < 100 else "TEXT_LAYER_CANDIDATE")
        entries.append({"page": page, "characters_without_whitespace": characters,
                        "text_sha256": hashlib.sha256(raw).hexdigest(), "route": route})
    manifest = {"source_sha256": digest, "page_count": page_count,
                "blocked_page_count": len(entries), "status": "BLOCK", "pages": entries,
                "note": "Text-layer diagnostics only; tables and visual evidence require source-image verification."}
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                                           encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("review", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = export(args.source, args.review, args.output)
    routes = {name: sum(p["route"] == name for p in result["pages"]) for name in (
        "TEXT_LAYER_CANDIDATE", "SPARSE_TEXT_LAYER", "NO_TEXT_LAYER")}
    print("PAGES:", result["blocked_page_count"])
    print("ROUTES:", routes)
    print("MANIFEST:", args.output / "manifest.json")
    print("STATUS: BLOCK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

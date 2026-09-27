"""Resume bounded, serial local extraction of the verified V4 PDF."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

SOURCE_SHA256 = "b5d95b660b35bfb6b2441623635cba91c235efd754bc283dfe1405f075834916"
PROJECT_ID = "2c436f43-98e4-43ad-b3b1-533c6ef4f8b2"
DOCUMENT_ID = "f5e7c759-721f-48c3-8e0e-ced590eecce8"


def windows(total_pages: int, size: int = 20):
    if total_pages < 1 or size < 1 or size > 20:
        raise ValueError("invalid PDF page count or window size")
    for start in range(1, total_pages + 1, size):
        yield start, min(start + size - 1, total_pages)


def main() -> int:
    user_repo = Path(__file__).resolve().parents[2] / "engineer-os"
    source = user_repo / ".engineer-os" / "v4-drive-source.pdf"
    output_dir = user_repo / ".engineer-os" / "v4-docling-check"
    if not source.is_file():
        print(f"BLOCK: V4 source missing: {source}", file=sys.stderr)
        return 2
    with source.open("rb") as handle:
        actual_sha = hashlib.file_digest(handle, "sha256").hexdigest()
    if actual_sha != SOURCE_SHA256:
        print("BLOCK: V4 source checksum mismatch", file=sys.stderr)
        return 2
    import pypdfium2

    pdf = pypdfium2.PdfDocument(str(source))
    try:
        count = len(pdf)
    finally:
        pdf.close()
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"V4 SOURCE OK; PAGES={count}; serial chunks of 2 pages", flush=True)
    blocked = []
    for start, end in windows(count):
        command = [sys.executable, str(Path(__file__).with_name("local_docling_batch.py")),
                   str(source), "--start", str(start), "--end", str(end),
                   "--chunk-size", "2", "--sha256", SOURCE_SHA256,
                   "--project-id", PROJECT_ID, "--document-id", DOCUMENT_ID,
                   "--output-dir", str(output_dir)]
        result = subprocess.run(command, text=True)
        if result.returncode:
            blocked.append([start, end])
        print(f"WINDOW {start}-{end}: {'BLOCK' if result.returncode else 'UNCERTAINTY'}", flush=True)
    summary = {"source_sha256": SOURCE_SHA256, "project_id": PROJECT_ID,
               "document_id": DOCUMENT_ID, "page_count": count,
               "blocked_windows": blocked, "status": "BLOCK" if blocked else "UNCERTAINTY",
               "note": "Extraction only; no evidence acceptance or final audit"}
    summary_path = output_dir / "v4-extraction-summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"SUMMARY: {summary_path}", flush=True)
    review = subprocess.run([sys.executable, str(Path(__file__).with_name("v4_extraction_review.py")),
                             str(output_dir), "--pages", str(count)], text=True)
    print(f"STATUS: {'BLOCK' if blocked or review.returncode else 'UNCERTAINTY'}", flush=True)
    return 2 if blocked or review.returncode else 0


if __name__ == "__main__":
    raise SystemExit(main())

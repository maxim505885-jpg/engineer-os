"""Export a small V4 blocked-page region probe as one source-bound ZIP.

The archive is diagnostic input for manual comparison, never accepted evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

PRIORITY_PAGES = (57, 58, 78, 109, 397, 401)


def collect(source: Path, review_path: Path, target: Path,
            *, pages: tuple[int, ...] = PRIORITY_PAGES, runner=subprocess.run) -> dict:
    review = json.loads(review_path.read_text(encoding="utf-8"))
    if review.get("status") != "BLOCK":
        raise ValueError("extraction review must have BLOCK status")
    with source.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    if digest != review.get("source_sha256"):
        raise ValueError("source PDF SHA-256 does not match extraction review")
    reasons = {page: reason for reason, entries in review["blocked_reasons"].items()
               for page in entries}
    if not pages or len(set(pages)) != len(pages) or any(page not in reasons for page in pages):
        raise ValueError("selected pages must be unique members of the blocked queue")

    manifest = {"source_sha256": digest, "status": "BLOCK", "selected_pages": list(pages),
                "failed_pages": [], "exported_pages": [],
                "note": "Diagnostic Docling export; compare all content to the source PDF."}
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + ".tmp")
    try:
        with tempfile.TemporaryDirectory() as staging, zipfile.ZipFile(
                temporary, "w", zipfile.ZIP_DEFLATED) as archive:
            for page in pages:
                output = Path(staging) / f"page-{page:04d}.json"
                command = [sys.executable, str(Path(__file__).with_name("inspect_docling_tables.py")),
                           str(source), "--page", str(page), "--sha256", digest,
                           "--output", str(output), "--include-blocks"]
                result = runner(command, capture_output=True, text=True)
                if result.returncode:
                    manifest["failed_pages"].append({"page": page,
                                                     "error": result.stderr.strip()[-1500:]})
                    continue
                try:
                    data = json.loads(output.read_text(encoding="utf-8"))
                    if (data.get("source_sha256") != digest or data.get("page_start") != page
                            or data.get("page_end") != page or not isinstance(data.get("tables"), list)
                            or not isinstance(data.get("text_blocks"), list)):
                        raise ValueError("export identity or structure mismatch")
                except (OSError, UnicodeError, ValueError, TypeError) as exc:
                    manifest["failed_pages"].append({"page": page, "error": str(exc)})
                    continue
                archive.write(output, output.name)
                manifest["exported_pages"].append({"page": page, "reason": reasons[page]})
            archive.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
        temporary.replace(target)
    finally:
        temporary.unlink(missing_ok=True)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("review", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = collect(args.source, args.review, args.output)
    print("EXPORTED_PAGES:", len(result["exported_pages"]))
    print("FAILED_PAGES:", len(result["failed_pages"]))
    print("OUTPUT:", args.output)
    print("STATUS: BLOCK; compare exported regions with source images")
    return 2 if result["failed_pages"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

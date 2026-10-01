"""Resume and bundle Docling region exports for every blocked V4 page.

Run on the user's local Docling environment. The ZIP remains diagnostic input;
it cannot by itself clear a page or the document's BLOCK status.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import zipfile
from pathlib import Path


def _valid(data: dict, digest: str, page: int) -> bool:
    if (data.get("source_sha256") != digest or data.get("page_start") != page
            or data.get("page_end") != page or not isinstance(data.get("tables"), list)
            or not isinstance(data.get("text_blocks"), list)):
        return False
    for table in data["tables"]:
        if (not isinstance(table, dict) or not isinstance(table.get("cells"), list)
                or not isinstance(table.get("provenance"), list)):
            return False
        if any(not isinstance(ref, dict) or ref.get("page_no") != page
               for ref in table["provenance"]):
            return False
    for block in data["text_blocks"]:
        if (not isinstance(block, dict) or not isinstance(block.get("provenance"), list)
                or not block["provenance"] or any(not isinstance(ref, dict)
                or ref.get("page_no") != page for ref in block["provenance"])):
            return False
    return True


def collect(source: Path, review_path: Path, target: Path, cache: Path,
            *, runner=subprocess.run, timeout: int = 300) -> dict:
    review = json.loads(review_path.read_text(encoding="utf-8"))
    with source.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    if digest != review.get("source_sha256") or review.get("status") != "BLOCK":
        raise ValueError("source hash or review BLOCK status mismatch")
    reasons = {page: reason for reason, entries in review["blocked_reasons"].items()
               for page in entries}
    if len(reasons) != sum(len(v) for v in review["blocked_reasons"].values()):
        raise ValueError("a page has multiple blocked reasons")
    if not reasons or any(type(page) is not int or not 1 <= page <= review["page_count"]
                          for page in reasons):
        raise ValueError("blocked page list is invalid")
    cache.mkdir(parents=True, exist_ok=True)
    manifest = {"source_sha256": digest, "status": "BLOCK", "selected_pages": sorted(reasons),
                "exported_pages": [], "failed_pages": [], "reused_pages": [],
                "note": "Docling diagnostic exports; verify all regions against the source PDF."}
    for index, page in enumerate(sorted(reasons), 1):
        output = cache / f"page-{page:04d}.json"
        try:
            data = json.loads(output.read_text(encoding="utf-8"))
            reused = _valid(data, digest, page)
        except (OSError, UnicodeError, ValueError, TypeError):
            reused = False
        if not reused:
            command = [sys.executable, str(Path(__file__).with_name("inspect_docling_tables.py")),
                       str(source), "--page", str(page), "--sha256", digest,
                       "--output", str(output), "--include-blocks"]
            try:
                result = runner(command, capture_output=True, text=True, timeout=timeout)
                if result.returncode:
                    raise ValueError((result.stderr or result.stdout).strip()[-1500:])
                data = json.loads(output.read_text(encoding="utf-8"))
                if not _valid(data, digest, page):
                    raise ValueError("export identity, provenance, or structure mismatch")
            except (OSError, UnicodeError, ValueError, TypeError, subprocess.TimeoutExpired) as exc:
                output.unlink(missing_ok=True)
                manifest["failed_pages"].append({"page": page, "error": str(exc)[-1500:]})
                print(f"PAGE {index}/{len(reasons)}: {page} FAILED", flush=True)
                continue
        else:
            manifest["reused_pages"].append(page)
        manifest["exported_pages"].append({"page": page, "reason": reasons[page]})
        print(f"PAGE {index}/{len(reasons)}: {page} {'REUSED' if reused else 'EXPORTED'}", flush=True)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + ".tmp")
    try:
        with zipfile.ZipFile(temporary, "w", zipfile.ZIP_DEFLATED) as archive:
            for entry in manifest["exported_pages"]:
                path = cache / f"page-{entry['page']:04d}.json"
                archive.write(path, path.name)
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
    parser.add_argument("--cache", type=Path, help="Reusable per-page exports")
    args = parser.parse_args()
    cache = args.cache or args.output.with_suffix(".cache")
    result = collect(args.source, args.review, args.output, cache)
    print("EXPORTED:", len(result["exported_pages"]))
    print("FAILED:", len(result["failed_pages"]))
    print("ARCHIVE:", args.output)
    print("STATUS: BLOCK; source-image comparison still required")
    return 2 if result["failed_pages"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

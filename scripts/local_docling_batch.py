"""Run small Docling chunks in separate processes and save a resumable local audit."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

CHECK_VERSION = 4  # Bump when extraction or completeness checks change.


def reusable_output(output: Path, *, first: int, last: int, sha256: str,
                    project_id: str, document_id: str) -> bool:
    """Only reuse a complete, source-bound extraction for the exact page range."""
    try:
        data = json.loads(output.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or any((data.get(key) != value) for key, value in (
            ("source_sha256", sha256.lower()), ("project_id", project_id),
            ("document_id", document_id), ("page_start", first),
            ("page_end", last), ("status", "UNCERTAINTY"),
        )):
            return False
        blocks = data.get("blocks")
        if not isinstance(blocks, list) or not blocks:
            return False
        for block in blocks:
            if not isinstance(block, dict) or not isinstance(block.get("text"), str):
                return False
            refs = block.get("provenance")
            if not isinstance(refs, list) or not refs or any(
                not isinstance(ref, dict) or type(ref.get("page_no")) is not int
                or not first <= ref["page_no"] <= last for ref in refs
            ):
                return False
        return True
    except (OSError, UnicodeError, ValueError, TypeError):
        return False


def ranges(start: int, end: int, chunk_size: int):
    if start < 1 or end < start or end - start + 1 > 20 or chunk_size < 1 or chunk_size > 5:
        raise ValueError("select at most 20 pages and chunks of 1–5 pages")
    for first in range(start, end + 1, chunk_size):
        yield first, min(first + chunk_size - 1, end)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--start", type=int, required=True)
    parser.add_argument("--end", type=int, required=True)
    parser.add_argument("--chunk-size", type=int, default=2)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--project-id", required=True)
    parser.add_argument("--document-id", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    try:
        planned = list(ranges(args.start, args.end, args.chunk_size))
    except ValueError as exc:
        parser.error(str(exc))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    blocked = False
    for first, last in planned:
        stem = f"pages-{first:04d}-{last:04d}"
        output = args.output_dir / f"{stem}.json"
        audit = args.output_dir / f"{stem}.audit.json"
        if audit.exists():
            try:
                prior = json.loads(audit.read_text(encoding="utf-8"))
            except (OSError, UnicodeError, ValueError):
                print(f"BLOCK {stem}: existing audit is unreadable", file=sys.stderr)
                return 2
            if not isinstance(prior, dict):
                print(f"BLOCK {stem}: existing audit is invalid", file=sys.stderr)
                return 2
            if (prior.get("source_sha256") != args.sha256.lower()
                    or prior.get("document_id") != args.document_id
                    or prior.get("project_id") != args.project_id):
                print(f"BLOCK {stem}: existing audit belongs to another source", file=sys.stderr)
                return 2
            if (prior.get("exit_code") == 0 and prior.get("check_version") == CHECK_VERSION
                    and reusable_output(output, first=first, last=last,
                        sha256=args.sha256, project_id=args.project_id,
                        document_id=args.document_id)):
                print(f"SKIP {stem}: already extracted; semantic review still required")
                continue
        output.unlink(missing_ok=True)  # Never leave a prior successful extraction beside a new BLOCK.
        command = [sys.executable, str(Path(__file__).with_name("local_docling_smoke.py")),
                   str(args.source), "--start", str(first), "--end", str(last),
                   "--sha256", args.sha256, "--project-id", args.project_id,
                   "--document-id", args.document_id, "--output-json", str(output)]
        result = subprocess.run(command, capture_output=True, text=True)
        audit.write_text(json.dumps({"check_version": CHECK_VERSION,
            "project_id": args.project_id, "document_id": args.document_id,
            "source_sha256": args.sha256.lower(), "page_start": first, "page_end": last,
            "exit_code": result.returncode, "stdout": result.stdout, "stderr": result.stderr},
            ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"{stem}: {'UNCERTAINTY' if result.returncode == 0 else 'BLOCK'}")
        if result.returncode:
            blocked = True
            print(result.stderr[-1000:], file=sys.stderr)
    print("BLOCK: review failed chunks" if blocked else "UNCERTAINTY: extracted chunks require visual and semantic review")
    return 2 if blocked else 0


if __name__ == "__main__":
    raise SystemExit(main())

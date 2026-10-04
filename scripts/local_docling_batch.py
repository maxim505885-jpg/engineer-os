"""Run small Docling chunks in separate processes and save a resumable local audit."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

CHECK_VERSION = 9  # Preserve original page identity in independently normalized chunk block IDs.


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


def run_chunk(args, first: int, last: int) -> int:
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
            return 0
    output.unlink(missing_ok=True)
    command = [sys.executable, str(Path(__file__).with_name("local_docling_smoke.py")),
               str(args.source), "--start", str(first), "--end", str(last),
               "--sha256", args.sha256, "--project-id", args.project_id,
               "--document-id", args.document_id, "--output-json", str(output)]
    if getattr(args, 'artifacts_path', None) is not None:
        command.extend(['--artifacts-path', str(args.artifacts_path)])
    result = subprocess.run(command, capture_output=True, text=True)
    audit.write_text(json.dumps({"check_version": CHECK_VERSION,
        "project_id": args.project_id, "document_id": args.document_id,
        "source_sha256": args.sha256.lower(), "page_start": first, "page_end": last,
        "exit_code": result.returncode, "stdout": result.stdout, "stderr": result.stderr},
        ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{stem}: {'UNCERTAINTY' if result.returncode == 0 else 'BLOCK'}")
    if result.returncode:
        print(result.stderr[-1000:], file=sys.stderr)
    return result.returncode


def ranges(start: int, end: int, chunk_size: int):
    if start < 1 or end < start or end - start + 1 > 20 or chunk_size < 1 or chunk_size > 5:
        raise ValueError("select at most 20 pages and chunks of 1–5 pages")
    for first in range(start, end + 1, chunk_size):
        yield first, min(first + chunk_size - 1, end)


def reviewed_scope(manifest: dict, *, first: int, last: int, sha256: str) -> bool:
    if not isinstance(manifest, dict) or manifest.get('source_sha256') != sha256.lower():
        raise ValueError('reviewed map belongs to another source')
    rows = manifest.get('rows')
    if not isinstance(rows, list) or not rows:
        raise ValueError('reviewed map has no rows')
    for row in rows:
        pages = row.get('source_pages') if isinstance(row, dict) else None
        if not isinstance(pages, list) or not pages or any(
                type(page) is not int or not first <= page <= last for page in pages):
            raise ValueError('reviewed body regions outside requested batch')
    return True


def review_outputs(args):
    outputs = [args.output_dir / name for name in
               ('reviewed-regions.audit.json', 'reviewed-regions.candidates.json', 'batch-review-summary.json')]
    checked = [args.source, args.reviewed_manifest, *args.output_dir.glob('pages-*.json')]
    for output in outputs:
        if any(output.resolve() == path.resolve() or
               (output.exists() and path.exists() and output.samefile(path)) for path in checked):
            raise ValueError('review outputs must not alias inputs, Docling results or each other')
        checked.append(output)
    return outputs


def export_reviewed_regions(args) -> dict:
    """Explicit sidecar recovery. Never replaces Docling output or its audit."""
    audit, candidates, _ = review_outputs(args)
    failure = dict(status='BLOCK', document_status='BLOCK', evidentiary_status='NOT_EVIDENCE',
                   acceptance_granted=False, complete_document=False, blocks=[])
    try:
        manifest = json.loads(args.reviewed_manifest.read_text(encoding='utf-8'))
        reviewed_scope(manifest, first=args.start, last=args.end, sha256=args.sha256)
        # Invalidate old sidecars before invoking the verifier, including launch failures.
        for path in (audit, candidates):
            path.write_text(json.dumps(failure), encoding='utf-8')
        command = [sys.executable, str(Path(__file__).with_name('verify_pdf_recovery.py')),
                   str(args.source), str(args.reviewed_manifest), '--output', str(audit),
                   '--candidate-output', str(candidates), '--project-id', args.project_id,
                   '--document-id', args.document_id]
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode:
            raise ValueError('source-region verifier failed: ' + result.stdout[-1000:] + result.stderr[-1000:])
        # Scope-check the actual export too, in case the map changed during the subprocess.
        exported = json.loads(candidates.read_text(encoding='utf-8'))
        reviewed_scope(exported, first=args.start, last=args.end, sha256=args.sha256)
        return dict(status='UNCERTAINTY', source_binding_status='PASS',
                    audit_file=audit.name, candidate_file=candidates.name,
                    note='Reviewed table regions only; no full-page coverage or evidence acceptance')
    except (OSError, UnicodeError, ValueError, TypeError) as exc:
        failure['reason'] = str(exc)
        for path in (audit, candidates):
            path.write_text(json.dumps(failure, ensure_ascii=False, indent=2), encoding='utf-8')
        return dict(status='BLOCK', reason=str(exc), audit_file=audit.name, candidate_file=candidates.name)


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
    parser.add_argument('--artifacts-path', type=Path, help='Existing local Docling model folder')
    parser.add_argument('--reviewed-manifest', type=Path,
                        help='Explicit reviewed table map; source-checked candidates are separate sidecars')
    parser.add_argument('--reviewed-only', action='store_true',
                        help='Only recheck/export reviewed regions; Docling NOT_RUN and document remains BLOCK')
    args = parser.parse_args()
    if args.reviewed_only and not args.reviewed_manifest:
        parser.error('--reviewed-only requires --reviewed-manifest')
    try:
        planned = list(ranges(args.start, args.end, args.chunk_size))
        if args.reviewed_manifest:
            review_outputs(args)
    except ValueError as exc:
        parser.error(str(exc))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    blocked = False
    blocked_ranges = []
    for first, last in ([] if args.reviewed_only else planned):
        result = None
        if first < last:
            parent = args.output_dir / f"pages-{first:04d}-{last:04d}.audit.json"
            children = [args.output_dir / f"pages-{page:04d}-{page:04d}.audit.json"
                        for page in range(first, last + 1)]
            if parent.is_file() and all(child.is_file() for child in children):
                try:
                    prior = json.loads(parent.read_text(encoding="utf-8"))
                    if (isinstance(prior, dict) and prior.get("exit_code") != 0
                            and prior.get("check_version") == CHECK_VERSION
                            and prior.get("source_sha256") == args.sha256.lower()
                            and prior.get("document_id") == args.document_id
                            and prior.get("project_id") == args.project_id):
                        result = 2
                        print(f"SKIP pages-{first:04d}-{last:04d}: already isolated")
                except (OSError, UnicodeError, ValueError):
                    pass
        if result is None:
            result = run_chunk(args, first, last)
        if result and first < last:
            print(f"ISOLATE {first}-{last}: checking each page separately")
            for page in range(first, last + 1):
                run_chunk(args, page, page)
        if result:
            blocked = True
            blocked_ranges.append([first, last])
    if args.reviewed_manifest:
        any_docling_blocked = blocked
        reviewed = export_reviewed_regions(args)
        blocked = blocked or args.reviewed_only or reviewed['status'] == 'BLOCK'
        summary = dict(source_sha256=args.sha256.lower(), project_id=args.project_id,
                       document_id=args.document_id, page_start=args.start, page_end=args.end,
                       blocked_ranges=blocked_ranges,
                       docling_status='NOT_RUN' if args.reviewed_only else
                                      ('BLOCK' if any_docling_blocked else 'UNCERTAINTY'),
                       reviewed_regions=reviewed, status='BLOCK' if blocked else 'UNCERTAINTY',
                       document_status='BLOCK', evidentiary_status='NOT_EVIDENCE',
                       complete_document=False, acceptance_granted=False)
        review_outputs(args)[2].write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    if args.reviewed_only:
        print('BLOCK: reviewed regions exported or blocked; Docling NOT_RUN, document completeness unverified')
    else:
        print("BLOCK: review failed chunks or regions" if blocked else "UNCERTAINTY: extracted chunks require visual and semantic review")
    return 2 if blocked else 0


if __name__ == "__main__":
    raise SystemExit(main())

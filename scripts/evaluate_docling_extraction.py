"""Compare saved Docling JSON with a declared reviewed baseline; never accept evidence."""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def normalize(text: str) -> str:
    return " ".join(text.split())


def evaluate(baseline: dict, extraction: dict) -> list[dict]:
    require(isinstance(baseline, dict) and isinstance(extraction, dict), "inputs must be objects")
    require(type(baseline.get("schema_version")) is int and baseline["schema_version"] == 1,
            "unsupported baseline schema")
    require(isinstance(baseline.get("source_sha256"), str)
            and re.fullmatch(r"[0-9a-f]{64}", baseline["source_sha256"]), "invalid source SHA256")
    for key in ("project_id", "document_id"):
        require(isinstance(baseline.get(key), str) and bool(baseline[key].strip()), f"missing {key}")
    start, end = baseline.get("page_start"), baseline.get("page_end")
    require(type(start) is int and type(end) is int and 1 <= start <= end and end - start < 10,
            "baseline must cover 1-10 pages, matching the bounded smoke script")
    for key in ("source_sha256", "project_id", "document_id", "page_start", "page_end"):
        require(type(extraction.get(key)) is type(baseline[key])
                and extraction[key] == baseline[key], f"source identity/range mismatch: {key}")
    review = baseline.get("review")
    require(isinstance(review, dict), "baseline requires declared source review")
    for key in ("reviewer", "reviewed_at", "source_ref"):
        require(isinstance(review.get(key), str) and bool(review[key].strip()), f"missing review {key}")
    reviewed = datetime.fromisoformat(review["reviewed_at"].replace("Z", "+00:00"))
    require(reviewed.utcoffset() is not None, "review timestamp requires timezone")
    require(extraction.get("parser") == "docling" and extraction.get("status") == "UNCERTAINTY",
            "only unaccepted Docling extraction may be evaluated")
    pages = baseline.get("pages")
    require(isinstance(pages, list) and bool(pages), "baseline has no page expectations")
    expected_pages = set()
    for page in pages:
        require(isinstance(page, dict), "invalid baseline page")
        number = page.get("page_no")
        require(type(number) is int and start <= number <= end and number not in expected_pages,
                "invalid or duplicate baseline page")
        expected_pages.add(number)
        for key in ("required_text", "required_table_rows"):
            values = page.get(key)
            require(isinstance(values, list) and all(isinstance(v, str) and v.strip() for v in values),
                    f"invalid {key}")
        require(bool(page["required_text"] or page["required_table_rows"]), "page has no content checks")
    require(expected_pages == set(range(start, end + 1)), "baseline does not cover entire range")
    blocks = extraction.get("blocks")
    require(isinstance(blocks, list) and bool(blocks), "extraction has no blocks")
    by_page = {page: [] for page in expected_pages}
    seen = set()
    for block in blocks:
        require(isinstance(block, dict), "invalid extraction block")
        for key in ("block_id", "kind", "text"):
            require(isinstance(block.get(key), str) and bool(block[key].strip()), f"invalid block {key}")
        require(block["block_id"] not in seen, "duplicate block ID")
        seen.add(block["block_id"])
        refs = block.get("provenance")
        require(isinstance(refs, list) and bool(refs), "block has no provenance")
        located = set()
        for ref in refs:
            require(isinstance(ref, dict) and type(ref.get("page_no")) is int
                    and start <= ref["page_no"] <= end, "invalid or out-of-range provenance")
            located.add(ref["page_no"])
        require(len(located) == 1, "block has ambiguous page")
        for number in located:
            by_page[number].append(block)
    checks = []
    for page in pages:
        number = page["page_no"]
        page_blocks = by_page[number]
        for expected in page["required_text"]:
            checks.append({"page_no": number, "kind": "text", "expected": expected,
                           "passed": any(normalize(expected) in normalize(b["text"]) for b in page_blocks)})
        actual_rows = Counter(normalize(b["text"]) for b in page_blocks if b["kind"] == "table_row")
        for expected, count in Counter(normalize(v) for v in page["required_table_rows"]).items():
            checks.append({"page_no": number, "kind": "table_row", "expected": expected,
                           "expected_count": count, "actual_count": actual_rows[expected],
                           "passed": actual_rows[expected] >= count})
    return checks


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "duplicate JSON key")
        result[key] = value
    return result


def reject_constant(value):
    raise ValueError(f"invalid JSON constant: {value}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline", type=Path)
    parser.add_argument("extraction", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = {
        "schema_version": 1, "check_scope": "BASELINE_EXTRACTION_REGRESSION",
        "status": "BLOCK", "acceptance_granted": False, "document_status": "UNCERTAINTY",
        "evidentiary_status": "NOT_EVIDENCE", "baseline_review": "DECLARED_NOT_INDEPENDENTLY_VERIFIED",
        "observed_at": datetime.now(timezone.utc).isoformat(), "checks": [], "checks_passed": 0,
        "errors": [],
        "limitations": ["Source PDF bytes are not rehashed by this evaluator.",
                        "Only baseline expectations are checked; full table/document completeness is not proven.",
                        "No evidence registration, normative verification, calculation verification or FINAL AUDIT."],
    }
    try:
        commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=Path(__file__).resolve().parents[1],
                                capture_output=True, text=True)
        report["code_commit"] = commit.stdout.strip() if commit.returncode == 0 else None
    except OSError:
        report["code_commit"] = None
    output_safe = args.output is None or args.output.resolve() not in (
        args.baseline.resolve(), args.extraction.resolve())
    try:
        require(output_safe, "output must not overwrite an input")
        inputs = []
        for label, path in (("baseline", args.baseline), ("extraction", args.extraction)):
            raw = path.read_bytes()
            report[f"{label}_sha256"] = hashlib.sha256(raw).hexdigest()
            inputs.append(json.loads(raw.decode("utf-8"), object_pairs_hook=unique_object,
                                     parse_constant=reject_constant))
        report["checks"] = evaluate(*inputs)
        report["checks_passed"] = sum(item["passed"] for item in report["checks"])
        report["status"] = "PASS" if all(item["passed"] for item in report["checks"]) else "BLOCK"
    except (OSError, ValueError, TypeError, RecursionError) as exc:
        report["errors"].append(str(exc))
    if args.output is not None and output_safe:
        temporary = None
        try:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=args.output.parent,
                                             delete=False) as handle:
                temporary = Path(handle.name)
                json.dump(report, handle, ensure_ascii=False, indent=2)
                handle.write("\n")
            os.replace(temporary, args.output)
        except OSError as exc:
            report["status"] = "BLOCK"
            report["errors"].append(str(exc))
        finally:
            if temporary is not None:
                try:
                    temporary.unlink(missing_ok=True)
                except OSError as exc:
                    report["status"] = "BLOCK"
                    report["errors"].append(str(exc))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())

"""Keep the two V4 NOPRIZ extracts separate while checking their common identity."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.v4_manual_evidence import validate

COMMON = ("organization", "ogrn", "1.1", "1.2", "1.3", "1.4", "2.3", "3.1", "4.2")
DISTINCT = ("extract_number", "extract_date", "1.5", "1.6", "1.7", "2.1", "2.2", "4.1", "4.3")


def _claims(data: dict, fields: set[str]) -> dict[str, str]:
    values = {}
    for page in data["pages"]:
        for claim in page["claims"]:
            key = claim["locator"]
            if key not in fields:
                continue
            if key in values:
                raise ValueError(f"duplicate registry field {key}")
            values[key] = claim["transcription"]
    return values


def compare(survey: dict, design: dict, *, common=COMMON, distinct=DISTINCT) -> dict:
    if (survey.get("status") != "BLOCK" or design.get("status") != "BLOCK"
            or survey.get("source_sha256") != design.get("source_sha256")):
        raise ValueError("source identity or BLOCK status mismatch")
    fields = set(common) | set(distinct)
    left, right = _claims(survey, fields), _claims(design, fields)
    if any(k not in left or k not in right or left[k] != right[k] for k in common):
        raise ValueError("common organization identity mismatch")
    if any(k not in left or k not in right or left[k] == right[k] for k in distinct):
        raise ValueError("separate registry scopes are not distinguishable")
    return {"source_sha256": survey["source_sha256"], "status": "BLOCK",
            "survey_pages": [486, 487], "design_pages": [488, 489],
            "shared_identity": {k: left[k] for k in common},
            "distinct_fields": {k: [left[k], right[k]] for k in distinct},
            "note": "Image transcriptions only; QR and signature validity are unverified."}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("source", "review", "survey", "design", "output"):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    survey = json.loads(args.survey.read_text(encoding="utf-8"))
    design = json.loads(args.design.read_text(encoding="utf-8"))
    validate(args.source, args.review, survey)
    validate(args.source, args.review, design)
    result = compare(survey, design)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")
    print("SHARED_FIELDS:", len(result["shared_identity"]))
    print("DISTINCT_FIELDS:", len(result["distinct_fields"]))
    print("STATUS:", result["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

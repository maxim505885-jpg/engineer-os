"""Create one offline page-linked inventory for all blocked V4 extraction pages."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import sys
from pathlib import Path
from urllib.parse import quote

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.run_v4_local import DOCUMENT_ID, PROJECT_ID, SOURCE_SHA256
from scripts.v4_extraction_review import review


def _audit_detail(directory: Path, page: int) -> str:
    try:
        audit = json.loads((directory / f"pages-{page:04d}-{page:04d}.audit.json").read_text(encoding="utf-8"))
        if (not isinstance(audit, dict) or audit.get("source_sha256") != SOURCE_SHA256
                or audit.get("project_id") != PROJECT_ID or audit.get("document_id") != DOCUMENT_ID
                or audit.get("page_start") != page or audit.get("page_end") != page):
            return "Audit missing or bound to another source"
        stderr = audit.get("stderr")
        if isinstance(stderr, str):
            lines = [line.strip() for line in stderr.splitlines() if line.strip()]
            return lines[-1][:500] if lines else "No diagnostic recorded"
    except (OSError, UnicodeError, ValueError):
        pass
    return "Audit unreadable"


def render_report(result: dict, directory: Path, source: Path) -> str:
    if result.get("source_sha256") != SOURCE_SHA256 or result.get("status") != "BLOCK":
        raise ValueError("blocked review requires the verified V4 audit")
    if source.parent.resolve() != directory.parent.resolve():
        raise ValueError("source PDF must be next to the audit directory")
    blocked = [
        (int(page), reason)
        for reason, pages in result["blocked_reasons"].items()
        for page in pages
    ]
    blocked.sort()
    rows = []
    for page, reason in blocked:
        if page < 1 or page > result["page_count"]:
            raise ValueError("blocked page is outside the source PDF")
        detail = _audit_detail(directory, page)
        link = f"../{quote(source.name, safe='')}#page={page}"
        rows.append(
            f'<tr><td><a href="{html.escape(link, quote=True)}">{page}</a></td>'
            f'<td>{html.escape(reason)}</td><td>{html.escape(detail)}</td></tr>'
        )
    summary = " · ".join(
        f"{html.escape(reason)}: {len(pages)}" for reason, pages in result["blocked_reasons"].items()
    )
    return ("<!doctype html>\n<html lang=\"ru\"><meta charset=\"utf-8\">"
            "<title>V4: заблокированные страницы</title>"
            "<style>body{font:16px system-ui;max-width:1300px;margin:2rem auto;padding:0 1rem}"
            "table{border-collapse:collapse;width:100%}td,th{border:1px solid #bbb;padding:.5rem;vertical-align:top}"
            "tr:nth-child(even){background:#f4f4f4}td:last-child{overflow-wrap:anywhere}</style>"
            "<h1>V4: заблокированные страницы</h1>"
            f"<p>Статус BLOCK. Страниц для проверки: {len(blocked)}. "
            "Это очередь проверки, а не подтверждённые доказательства.</p>"
            f"<p>{summary}</p>"
            "<table><thead><tr><th>Страница PDF</th><th>Причина</th><th>Ошибка извлечения</th>"
            "</tr></thead><tbody>" + "\n".join(rows) + "</tbody></table></html>\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("source", type=Path)
    parser.add_argument("--pages", type=int, default=534)
    args = parser.parse_args()
    if not args.source.is_file():
        parser.error("source PDF is unavailable")
    with args.source.open("rb") as handle:
        if hashlib.file_digest(handle, "sha256").hexdigest() != SOURCE_SHA256:
            parser.error("source SHA-256 mismatch")
    result = review(args.directory, args.pages)
    report = render_report(result, args.directory, args.source)
    path = args.directory / "v4-blocked-review.html"
    temporary = path.with_suffix(".html.tmp")
    temporary.write_text(report, encoding="utf-8")
    temporary.replace(path)
    print(f"BLOCKED_PAGES: {result['blocked_chunks']}")
    print(f"REPORT: {path}")
    return 2 if result["status"] == "BLOCK" else 0


if __name__ == "__main__":
    raise SystemExit(main())

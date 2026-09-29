"""Render a bounded, source-checked sample of V4 blocked pages into one ZIP."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import zipfile
from pathlib import Path

SAMPLE = (3, 8, 30, 142, 148, 154, 176, 264, 336, 397, 486, 500)


def export(source: Path, review_path: Path, target: Path, pages: tuple[int, ...] = SAMPLE) -> None:
    import pypdfium2 as pdfium

    review = json.loads(review_path.read_text(encoding="utf-8"))
    with source.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    if digest != review.get("source_sha256"):
        raise ValueError("source PDF does not match extraction review SHA-256")
    reasons = {page: reason for reason, items in review["blocked_reasons"].items() for page in items}
    if any(page not in reasons for page in pages):
        raise ValueError("sample includes a page absent from the blocked review queue")
    pdf = pdfium.PdfDocument(str(source))
    if len(pdf) != review.get("page_count") or any(page < 1 or page > len(pdf) for page in pages):
        raise ValueError("source PDF page count does not match extraction review")
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + ".tmp")
    try:
        with zipfile.ZipFile(temporary, "w", zipfile.ZIP_DEFLATED) as archive:
            manifest = {"source_sha256": digest, "page_count": len(pdf),
                        "status": "BLOCK", "sample": [{"page": p, "reason": reasons[p]} for p in pages],
                        "note": "Visual sample only; no engineering fact accepted."}
            archive.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
            for page in pages:
                bitmap = pdf[page - 1].render(scale=1.8)
                image = bitmap.to_pil()
                buffer = io.BytesIO()
                image.save(buffer, format="PNG")
                archive.writestr(f"page-{page:04d}.png", buffer.getvalue())
                image.close()
        temporary.replace(target)
    finally:
        temporary.unlink(missing_ok=True)
        pdf.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("review", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    export(args.source, args.review, args.output)
    print(f"SAMPLE: {len(SAMPLE)} blocked pages")
    print(f"OUTPUT: {args.output}")
    print("STATUS: BLOCK; images require visual review")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

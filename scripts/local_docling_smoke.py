"""Bounded local Docling check; never registers extracted text as evidence."""

from __future__ import annotations

import argparse
import collections
import os
import sys
import time
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--end", type=int, default=1)
    parser.add_argument("--sha256", help="Expected source SHA-256")
    args = parser.parse_args()
    if args.start < 1 or args.end < args.start or args.end - args.start > 9:
        parser.error("use a page range of at most 10 pages")

    os.environ["ENGINEER_OS_DOCUMENT_INTELLIGENCE"] = "true"
    from engineering.document_intelligence.docling_adapter import DoclingDocumentParser

    started = time.monotonic()
    document = DoclingDocumentParser().parse(str(args.source), page_range=(args.start, args.end))
    pages = sorted({ref.page_no for block in document.blocks for ref in block.provenance})
    print("SHA256:", document.source_sha256)
    print("BLOCKS:", len(document.blocks))
    print("PAGES:", pages)
    print("KINDS:", dict(collections.Counter(block.kind for block in document.blocks)))
    print("UNLOCATED:", sum(not block.provenance for block in document.blocks))
    print("SECONDS:", round(time.monotonic() - started, 1))
    if args.sha256 and document.source_sha256 != args.sha256.lower():
        print("BLOCK: source checksum mismatch", file=sys.stderr)
        return 2
    if any(page < args.start or page > args.end for page in pages) or not pages:
        print("BLOCK: page provenance outside requested range", file=sys.stderr)
        return 2
    print("UNCERTAINTY: OCR and tables require visual verification before evidence registration")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

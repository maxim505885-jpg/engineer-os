"""Bounded local Docling check; never registers extracted text as evidence."""

from __future__ import annotations

import argparse
import collections
import logging
import os
import sys
import time
from pathlib import Path


class _TableLossMonitor(logging.Handler):
    def __init__(self) -> None:
        super().__init__(level=logging.WARNING)
        self.messages: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        message = record.getMessage()
        if "pdf cells matched neither a row nor a column band" in message and "dropped from the table" in message:
            self.messages.append(message)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--end", type=int, default=1)
    parser.add_argument("--sha256", help="Expected source SHA-256")
    parser.add_argument("--table-mode", choices=("accurate", "fast"), default="accurate")
    args = parser.parse_args()
    if args.start < 1 or args.end < args.start or args.end - args.start > 9:
        parser.error("use a page range of at most 10 pages")

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    os.environ["ENGINEER_OS_DOCUMENT_INTELLIGENCE"] = "true"
    from engineering.document_intelligence.docling_adapter import DoclingDocumentParser

    started = time.monotonic()
    monitor = _TableLossMonitor()
    root_logger = logging.getLogger()
    root_logger.addHandler(monitor)
    try:
        document = DoclingDocumentParser(table_mode=args.table_mode).parse(str(args.source), page_range=(args.start, args.end))
    finally:
        root_logger.removeHandler(monitor)
    pages = sorted({ref.page_no for block in document.blocks for ref in block.provenance})
    print("SHA256:", document.source_sha256)
    print("TABLE_MODE:", args.table_mode)
    print("BLOCKS:", len(document.blocks))
    print("PAGES:", pages)
    print("KINDS:", dict(collections.Counter(block.kind for block in document.blocks)))
    print("UNLOCATED:", sum(not block.provenance for block in document.blocks))
    print("SECONDS:", round(time.monotonic() - started, 1))
    print("TABLE_LOSS_WARNINGS:", len(monitor.messages))
    if args.sha256 and document.source_sha256 != args.sha256.lower():
        print("BLOCK: source checksum mismatch", file=sys.stderr)
        return 2
    if any(page < args.start or page > args.end for page in pages) or not pages:
        print("BLOCK: page provenance outside requested range", file=sys.stderr)
        return 2
    if monitor.messages:
        print("BLOCK: Docling dropped table cells; this chunk cannot be used as complete evidence", file=sys.stderr)
        return 2
    print("UNCERTAINTY: OCR and tables require visual verification before evidence registration")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

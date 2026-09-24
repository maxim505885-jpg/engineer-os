from __future__ import annotations

import argparse
import json
from .docx import DocxTextExtractor


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract text from a DOCX without inventing document facts.")
    parser.add_argument("path")
    args = parser.parse_args()
    document = DocxTextExtractor().extract(args.path)
    print(json.dumps({"source_path": document.source_path, "media_type": document.media_type, "paragraphs": list(document.paragraphs), "text": document.text}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

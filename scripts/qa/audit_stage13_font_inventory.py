#!/usr/bin/env python3
"""Inventory source Word font references and the local Word PDF font set.

Windows-only, read-only QA diagnostic. It reports source OOXML names, whether
font programs are embedded in the DOCX, exact Windows font-registration name
matches (including registered file hashes), and the fonts referenced by the
Word PDF export. A name mismatch is not proof that a font was used or replaced.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from xml.etree import ElementTree as ET

import fitz

try:
    import winreg
except ImportError as error:  # pragma: no cover - exercised on non-Windows hosts
    raise SystemExit("This diagnostic requires Windows font registrations") from error


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
W = f"{{{W_NS}}}"
FONT_ATTRIBUTES = {"ascii", "hAnsi", "eastAsia", "cs"}
EMBED_TAGS = ("embedRegular", "embedBold", "embedItalic", "embedBoldItalic")
EXPECTED_DOCX_SHA256 = "c0ca593f4dec5c101d01282523032e05b147e9169fb043a144af5fbd479a5685"
EXPECTED_WORD_PDF_SHA256 = "6dc88d91e41070bc9353e4d2cc6b2236fe4be39678935d4665816e841b2a8a14"


def hash_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_inventory(docx_path: Path) -> tuple[Counter[str], dict[str, dict[str, object]], list[str]]:
    references: Counter[str] = Counter()
    font_table: dict[str, dict[str, object]] = {}
    with zipfile.ZipFile(docx_path) as package:
        for part in package.namelist():
            if not (part.startswith("word/") and part.endswith(".xml")):
                continue
            try:
                root = ET.fromstring(package.read(part))
            except ET.ParseError:
                continue
            if part == "word/fontTable.xml":
                for font in root.findall(f"{W}font"):
                    name = font.get(f"{W}name")
                    if not name:
                        continue
                    font_table[name] = {
                        "alternate_name": (
                            font.find(f"{W}altName").get(f"{W}val")
                            if font.find(f"{W}altName") is not None
                            else None
                        ),
                        "embedded_variants": [
                            tag for tag in EMBED_TAGS if font.find(f"{W}{tag}") is not None
                        ],
                    }
            for element in root.iter(f"{W}rFonts"):
                for attribute, value in element.attrib.items():
                    if attribute.startswith(W) and attribute[len(W) :] in FONT_ATTRIBUTES:
                        references[value] += 1
        font_parts = sorted(part for part in package.namelist() if part.startswith("word/fonts/"))
    return references, font_table, font_parts


def registration_inventory(source_names: set[str]) -> dict[str, object]:
    registered: dict[str, dict[str, object]] = {}
    roots = (
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts"),
    )
    for hive, key_path in roots:
        try:
            key = winreg.OpenKey(hive, key_path)
        except OSError:
            continue
        with key:
            for index in range(winreg.QueryInfoKey(key)[1]):
                display_name, value, _ = winreg.EnumValue(key, index)
                file_path = Path(value)
                if not file_path.is_absolute():
                    file_path = Path(r"C:\Windows\Fonts") / file_path
                if not file_path.is_file():
                    continue
                registered[display_name] = {
                    "file_name": file_path.name,
                    "sha256": hash_file(file_path),
                }

    def normalized(value: str) -> str:
        return re.sub(r"\s*\((?:TrueType|OpenType)\)$", "", value, flags=re.IGNORECASE).strip().casefold()

    exact_matches = {}
    for name in sorted(source_names, key=str.casefold):
        matches = [
            {"registration": display, **metadata}
            for display, metadata in registered.items()
            if normalized(display) == normalized(name)
        ]
        exact_matches[name] = matches
    return {"registration_count": len(registered), "exact_name_matches": exact_matches}


def pdf_inventory(pdf_path: Path) -> tuple[int, list[dict[str, object]]]:
    fonts: dict[int, dict[str, object]] = {}
    with fitz.open(pdf_path) as document:
        page_count = document.page_count
        for page in document:
            for item in page.get_fonts(full=True):
                xref, extension, kind, base_name = item[:4]
                row = fonts.setdefault(
                    xref,
                    {
                        "xref": xref,
                        "base_font": base_name,
                        "type": kind,
                        "extension": extension,
                        "pages": set(),
                    },
                )
                row["pages"].add(page.number + 1)
        for xref, row in fonts.items():
            try:
                extracted = document.extract_font(xref)
                content = extracted[3] if len(extracted) > 3 else b""
                row["embedded_in_pdf"] = bool(content)
                row["embedded_sha256"] = hash_bytes(content) if content else None
            except Exception as error:  # keep each font outcome explicit
                row["embedded_in_pdf"] = "ERROR"
                row["error"] = str(error)
    output = []
    for row in fonts.values():
        row["page_count"] = len(row.pop("pages"))
        output.append(row)
    return page_count, sorted(output, key=lambda row: int(row["xref"]))


def audit(docx_path: Path, pdf_path: Path) -> dict[str, object]:
    docx_hash, pdf_hash = hash_file(docx_path), hash_file(pdf_path)
    if docx_hash != EXPECTED_DOCX_SHA256:
        raise ValueError(f"DOCX SHA-256 mismatch: {docx_hash}")
    if pdf_hash != EXPECTED_WORD_PDF_SHA256:
        raise ValueError(f"Word PDF SHA-256 mismatch: {pdf_hash}")
    references, table, font_parts = source_inventory(docx_path)
    registrations = registration_inventory(set(references))
    pages, pdf_fonts = pdf_inventory(pdf_path)
    exact_matches = sum(bool(items) for items in registrations["exact_name_matches"].values())
    return {
        "source_docx": {"name": docx_path.name, "size_bytes": docx_path.stat().st_size, "sha256": docx_hash},
        "word_reference_pdf": {"name": pdf_path.name, "size_bytes": pdf_path.stat().st_size, "page_count": pages, "sha256": pdf_hash},
        "source_font_reference_count": sum(references.values()),
        "source_font_names": [
            {"name": name, "reference_count": references[name]}
            for name in sorted(references, key=str.casefold)
        ],
        "source_font_table": table,
        "source_embedded_font_parts": font_parts,
        "windows_font_registration_count": registrations["registration_count"],
        "source_font_exact_registry_name_matches": exact_matches,
        "source_font_registry_matches": registrations["exact_name_matches"],
        "word_pdf_font_xrefs": pdf_fonts,
        "qualification": "inventory_only; a font-name mismatch does not prove visible use, substitution, or physical-layout equivalence",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--docx", type=Path, required=True)
    parser.add_argument("--word-pdf", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = audit(args.docx, args.word_pdf)
    except Exception as error:
        json.dump({"status": "BLOCK", "error": str(error)}, sys.stdout, ensure_ascii=True, indent=2)
        sys.stdout.write("\n")
        return 2
    json.dump(result, sys.stdout, ensure_ascii=True, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


#!/usr/bin/env python3
"""Compare three visually associated Word OLE previews with PDF image bounds.

This is a read-only, source-bound diagnostic for the Stage 13 QA dossier.  It
does not interpret PBrush print streams or qualify drawing semantics.  The
page associations below were established by visual review; this script checks
the corresponding OOXML relationship, VML size, PDF image XObject, and pixels.

Requires PyMuPDF, Pillow, and NumPy in the local QA environment.  It writes a
deterministic JSON report to stdout and never modifies either source document.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import posixpath
import re
import sys
import zipfile
from io import BytesIO
from pathlib import Path
from xml.etree import ElementTree as ET

import fitz
import numpy as np
from PIL import Image


EXPECTED_DOCX_SHA256 = "c0ca593f4dec5c101d01282523032e05b147e9169fb043a144af5fbd479a5685"
EXPECTED_WORD_PDF_SHA256 = "6dc88d91e41070bc9353e4d2cc6b2236fe4be39678935d4665816e841b2a8a14"
DOCX_NS = {
    "o": "urn:schemas-microsoft-com:office:office",
    "v": "urn:schemas-microsoft-com:vml",
}
REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"

# Page-level associations were established by visual comparison in the QA
# dossier.  Keeping those reviewed anchors explicit avoids claiming the script
# inferred semantic placement by itself.
OBJECTS = (
    {"ole_part": "word/embeddings/oleObject15.bin", "shape_id": "_x0000_i1039", "page": 74},
    {"ole_part": "word/embeddings/oleObject16.bin", "shape_id": "_x0000_i1040", "page": 84},
    {"ole_part": "word/embeddings/oleObject20.bin", "shape_id": "_x0000_i1044", "page": 99},
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def points_from_style(style: str, key: str) -> float:
    match = re.search(rf"(?:^|;){key}:([0-9]+(?:\.[0-9]+)?)pt(?:;|$)", style)
    if not match:
        raise ValueError(f"VML style has no {key} in points: {style!r}")
    return float(match.group(1))


def read_object_binding(docx: zipfile.ZipFile, item: dict[str, object]) -> dict[str, object]:
    document = ET.fromstring(docx.read("word/document.xml"))
    relationships = ET.fromstring(docx.read("word/_rels/document.xml.rels"))
    rel_targets = {
        rel.get("Id"): rel.get("Target")
        for rel in relationships.findall(f"{{{REL_NS}}}Relationship")
    }
    shape_id = str(item["shape_id"])
    ole = document.find(f'.//{{{DOCX_NS["o"]}}}OLEObject[@ShapeID="{shape_id}"]')
    shape = document.find(f'.//{{{DOCX_NS["v"]}}}shape[@id="{shape_id}"]')
    if ole is None or shape is None:
        raise ValueError(f"Missing OLEObject or VML shape for {shape_id}")
    image_data = shape.find(f'{{{DOCX_NS["v"]}}}imagedata')
    if image_data is None:
        raise ValueError(f"Missing VML imagedata for {shape_id}")
    relationship_id = image_data.get(f"{{{R_NS}}}id")
    target = rel_targets.get(relationship_id)
    if not relationship_id or not target:
        raise ValueError(f"Missing image relationship for {shape_id}")
    preview_part = posixpath.normpath(posixpath.join("word", target))
    style = shape.get("style", "")
    return {
        "shape_id": shape_id,
        "ole_progid": ole.get("ProgID"),
        "image_relationship_id": relationship_id,
        "preview_part": preview_part,
        "vml_width_pt": points_from_style(style, "width"),
        "vml_height_pt": points_from_style(style, "height"),
    }


def pixel_metrics(preview_bytes: bytes, xobject_bytes: bytes) -> dict[str, object]:
    preview = Image.open(BytesIO(preview_bytes)).convert("RGB")
    xobject = Image.open(BytesIO(xobject_bytes)).convert("RGB")
    preview_size = preview.size
    if preview.size != xobject.size:
        preview = preview.resize(xobject.size, Image.Resampling.LANCZOS)
    left = np.asarray(preview, dtype=np.float64).reshape(-1)
    right = np.asarray(xobject, dtype=np.float64).reshape(-1)
    left_centered = left - left.mean()
    right_centered = right - right.mean()
    denominator = np.linalg.norm(left_centered) * np.linalg.norm(right_centered)
    ncc = float(np.dot(left_centered, right_centered) / denominator) if denominator else None
    differences = left - right
    return {
        "preview_dimensions_px": list(preview_size),
        "pdf_xobject_dimensions_px": list(xobject.size),
        "ncc_after_lanczos_resize": ncc,
        "mae_rgb": float(np.mean(np.abs(differences))),
        "rmse_rgb": float(np.sqrt(np.mean(np.square(differences)))),
        "compressed_bytes_equal": sha256(preview_bytes) == sha256(xobject_bytes),
    }


def audit(docx_path: Path, pdf_path: Path) -> dict[str, object]:
    docx_hash = sha256_file(docx_path)
    pdf_hash = sha256_file(pdf_path)
    if docx_hash != EXPECTED_DOCX_SHA256:
        raise ValueError(f"DOCX SHA-256 mismatch: {docx_hash}")
    if pdf_hash != EXPECTED_WORD_PDF_SHA256:
        raise ValueError(f"Word PDF SHA-256 mismatch: {pdf_hash}")

    results: list[dict[str, object]] = []
    with zipfile.ZipFile(docx_path) as package, fitz.open(pdf_path) as document:
        page_count = document.page_count
        for item in OBJECTS:
            binding = read_object_binding(package, item)
            preview_bytes = package.read(str(binding["preview_part"]))
            page_number = int(item["page"])
            if page_number > document.page_count:
                raise ValueError(f"Word PDF has no page {page_number}")
            page = document[page_number - 1]
            width = float(binding["vml_width_pt"])
            height = float(binding["vml_height_pt"])
            candidates = []
            for info in page.get_image_info(xrefs=True):
                bbox = tuple(float(value) for value in info["bbox"])
                bbox_width = bbox[2] - bbox[0]
                bbox_height = bbox[3] - bbox[1]
                if abs(bbox_width - width) <= 1.0 and abs(bbox_height - height) <= 1.0:
                    candidates.append((info, bbox, bbox_width, bbox_height))
            if len(candidates) != 1:
                raise ValueError(
                    f"Expected one matching image XObject on page {page_number}; found {len(candidates)}"
                )
            info, bbox, bbox_width, bbox_height = candidates[0]
            xref = int(info["xref"])
            extracted = document.extract_image(xref)
            metric = pixel_metrics(preview_bytes, extracted["image"])
            width_delta = bbox_width - width
            height_delta = bbox_height - height
            results.append(
                {
                    "ole_part": item["ole_part"],
                    "ole_sha256": sha256(package.read(str(item["ole_part"]))),
                    **binding,
                    "preview_sha256": sha256(preview_bytes),
                    "word_pdf_page": page_number,
                    "pdf_page_rect_pt": [float(value) for value in page.rect],
                    "pdf_xobject_xref": xref,
                    "pdf_xobject_bbox_pt": list(bbox),
                    "pdf_xobject_dimensions_pt": [bbox_width, bbox_height],
                    "bounds_delta_pt": [width_delta, height_delta],
                    "bounds_within_0_2_pt": abs(width_delta) <= 0.2 and abs(height_delta) <= 0.2,
                    "pdf_xobject_format": extracted["ext"],
                    "pdf_xobject_sha256": sha256(extracted["image"]),
                    **metric,
                    "association_basis": "prior source-page visual review; this script checks OOXML binding and matching PDF bounds",
                }
            )
    return {
        "status": "BOUNDS_SCALE_MATCHED" if all(row["bounds_within_0_2_pt"] for row in results) else "BLOCK",
        "source_docx": {"path": docx_path.name, "size_bytes": docx_path.stat().st_size, "sha256": docx_hash},
        "word_reference_pdf": {"path": pdf_path.name, "size_bytes": pdf_path.stat().st_size, "pages": page_count, "sha256": pdf_hash},
        "objects_checked": len(results),
        "pixel_equality_claimed": False,
        "semantic_qualification": "NOT_PERFORMED",
        "objects": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--docx", type=Path, required=True, help="Immutable V4 DOCX source")
    parser.add_argument("--word-pdf", type=Path, required=True, help="Word reference export PDF")
    args = parser.parse_args()
    try:
        result = audit(args.docx, args.word_pdf)
    except Exception as error:  # emit a concise machine-readable diagnostic
        json.dump({"status": "BLOCK", "error": str(error)}, sys.stdout, ensure_ascii=True, indent=2)
        sys.stdout.write("\n")
        return 2
    json.dump(result, sys.stdout, ensure_ascii=True, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0 if result["status"] == "BOUNDS_SCALE_MATCHED" else 1


if __name__ == "__main__":
    raise SystemExit(main())


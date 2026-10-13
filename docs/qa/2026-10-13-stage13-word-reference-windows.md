# Stage 13 Word/PDF reference check — 2026-10-13

Status: **OPEN**. This record documents one bounded Windows reference pass; it does not qualify complete reading, visual equivalence, engineering correctness, or acceptance.

## Immutable source and reference environment

- Candidate base: `integration/release-candidate-v1` at `b2c29604d3a8a2a8079a670a7affca4f55b2b9c6`, tree `c1f44ad1839ecf763faedb98deaf87fd219e5e75`.
- V4 DOCX: 147,560,922 bytes, SHA-256 `c0ca593f4dec5c101d01282523032e05b147e9169fb043a144af5fbd479a5685`; 694 ZIP entries passed CRC checks.
- V4 PDF: 74,522,583 bytes, SHA-256 `b5d95b660b35bfb6b2441623635cba91c235efd754bc283dfe1405f075834916`.
- Windows 10 build 19045; Microsoft Word 2021 `16.0.14228.20204`. Word opened a byte-identical copy read-only, with macros disabled and no external links activated. Source and working-copy DOCX hashes were unchanged after close.
- Installed font file identities were recorded locally. Common Arial, Calibri, Times New Roman, and Cambria Math files are present. The source’s explicit font names/styles and embedded font programs were not fully qualified; no fonts were installed.

## Word fields and page comparison

Word exposed 147 body fields: 57 HYPERLINK, 57 PAGEREF, 21 EMBED, 11 SEQ, and one TOC. Only the 57 PAGEREF, 11 SEQ, and one TOC fields were updated. A shared header PAGE field was updated through the two section placements. HYPERLINK and EMBED fields were left untouched. Field update caused no change to extracted text or rendered raster hashes on any of the 491 Word pages.

The post-update Word PDF is 44,838,874 bytes, SHA-256 `6dc88d91e41070bc9353e4d2cc6b2236fe4be39678935d4665816e841b2a8a14`. It contains 491 pages against 534 pages in V4 PDF. Every page in the first 491 has a different page rectangle: Word `595.44 × 842.04 pt`, V4 `595.32 × 841.92 pt`. None of the 491 page raster hashes match; comparison on the common top-left raster extent is diagnostic only (different-pixel fraction min/median/max `0.00490 / 0.03077 / 0.28116`).

Native extracted text is exact on 483/491 pages and equal after whitespace removal on 489/491. The only non-whitespace character-multiset differences occur on the two table-of-contents pages and consist of dotted-leader counts; the other six text differences are whitespace. This does not prove matching layout or figure/table placement.

V4 pages 492–534 are a 43-page graphic appendix after the drawing index on page 491. The Word export ends at page 491. A full pass through all 43 source pages found 125 trimmed native-text characters total: 40 pages have no native text, and all 43 contain vector paths (2,513–67,955 paths per page). The application's existing native PDF audit marks all 43 pages `VECTOR_CONTENT_UNVERIFIED` and status `BLOCK`. The DOCX itself has 21 embedded OLE parts (44,983,296 bytes total; all 21 are `PBrush` objects), 696 image references, and 463 body paragraphs containing DrawingML.

A separate local OCR diagnostic subsequently covered all 43 appendix sheets at 300 dpi with Tesseract `5.5.3.20260724`, `rus+eng`, OEM 1 and PSM 11. It produced 19,644 word candidates and TSV coordinates for all 43 pages. Weighted mean word confidence was 71.35; 29.12% of words scored below 60, and per-page mean confidence ranged from 57.61 (PDF page 513) to 85.31 (page 523). This is candidate text, not a completeness or accuracy result: low-confidence labels, small dimensions, rotation, symbols, reading order and omissions have not been checked exhaustively against the vector sheets. The PDF hash remained `b5d95b660b35bfb6b2441623635cba91c235efd754bc283dfe1405f075834916`.

The 21 DOCX OLE relationships were mapped to 20 unique fallback PNG previews and body paragraph indices. OCR on those 20 previews produced 616 word candidates with mean per-image confidence 61.82. Two pairs of OLE objects share the same preview images. Preview coverage does not establish native OLE payload fidelity or printed page placement; those payloads and the relationship between these details and the 43 appended sheets remain unresolved. The source DOCX hash is unchanged. OCR is an isolated diagnostic tool on this workstation, not a production dependency. The official Tesseract 5.5.3 Windows installer SHA-256 was verified as `bee9e3434bd94fd65387d9be28cd467a41f61b1275383b55b0f59a1331270ae4`, with a valid Universität Mannheim Authenticode signature. Official `tessdata_best` models were pinned to commit `e12c65a915945e4c28e237a9b52bc4a8f39a0cec`; Git blob hashes and file sizes matched. The installer selected its default `C:\\Program Files\\Tesseract-OCR` location despite a requested `/DIR`; it did not add Tesseract to user or machine PATH. OCR TSV, per-page metrics, asset relationships and source-bound scripts remain private under `stage13-qa`.

The DOCX production audit returned 14,689 logical units: 1,807 paragraphs, 12,826 table cells, 41 equation units, 11 `unsupported_body` units, and 4 empty auxiliary units. Each of the 11 unsupported units was traced to an empty `bookmarkEnd` marker with no text, drawing, or object. This resolves those 11 markers as a conservative structural warning for this source; it does not qualify other object types or layout. Auxiliary placement remains unverified.

## Windows regression and code change

The complete existing suite ran after the proposed fix: 1,058 tests in 297.549 seconds, with zero assertion failures, 13 errors, and 49 skips. The 13 errors were:

- Five `test_data_backup` cases and `test_linked_database_is_rejected_without_modifying_external_database`: SQLite handles remained locked during Windows temporary-directory cleanup.
- `test_wrong_source_digest_is_rejected_before_inspection`: Windows rejected reading the still-open `NamedTemporaryFile` fixture.
- Six symlink cases in `test_local_docling_batch`, `test_region_readback`, `test_selected_ocr`, and `test_solver_execution_integrity`: the account lacks Windows symlink-creation privilege.

The 49 skips include unavailable local Russian/English OCR models at the time of the full-suite run, unavailable optional table OCR dependencies, Linux-only process/seccomp checks, and Windows symlink-related skips. No test was disabled or counted as passed. The full local log is retained outside the repository; SHA-256 `a4c805e12aaf4ca9a97deeacc602e5b7f2eaeaca0ce600eb30d9bcc00b317aa8e`.

The run reproduced a real CLI portability defect: a Cyrillic report raised `UnicodeEncodeError` when subprocess stdout used ASCII. `scripts/evaluate_docling_extraction.py` now emits escaped ASCII JSON to stdout while the separately saved report remains UTF-8. A real subprocess regression forces ASCII stdout and confirms status, Cyrillic recovery after JSON decoding, unchanged input, and unchanged acceptance gates. Full suite confirms this test passes. A separate test-fixture correction uses fixed ZIP entry timestamps so stage7 snapshot identity does not vary with wall-clock seconds; all three stage7 regression tests passed after this change.

## Remaining criteria

1. Validate OCR candidates for every vector sheet against full-resolution source visuals, including all labels, dimensions, orientation, symbols and omissions; determine whether the 43 PDF sheets are absent from Word or represented through other objects.
2. Decode and compare all 21 native OLE payloads, their 20 previews and exact Word print-page placements; preview OCR alone does not qualify them.
3. Qualify all relevant images, OLE/WDP/EMF layers, equations, headers/footers, fonts, physical pagination, and table geometry across the complete source.
4. Repeat the exact-head GitHub workflows and review the candidate PR. Preserve the 13 Windows-local errors and 49 skips as limitations unless separately resolved on supported CI environments.

This pass does not close item 13. It does not claim 100%, `ACCEPTED`, or a production Word renderer. LIRA/SCAD calculations remain deferred.


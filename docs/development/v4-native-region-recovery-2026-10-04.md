# V4: independent source-native region recovery

## Confirmed result

Original: 534 pages, 74,522,583 bytes; SHA256
`b5d95b660b35bfb6b2441623635cba91c235efd754bc283dfe1405f075834916`.

The new standalone native route recovered **59 declared vector regions on 54
original pages**, with **6,119 physical cells / 12,304 covered grid slots**, in
**39.60 seconds**. The difference in counts reflects original merged cells.
Each grid was re-detected on the original PDF. Native text, source SHA, original
coordinates, grid coverage and spans were checked. Image-containing regions and
native-empty cells containing visible ink remain blocked.

Result: `source_binding_audit.physical_grid_status=PASS`, selected-region
`status=UNCERTAINTY`, `document_status=BLOCK`, `NOT_EVIDENCE`, no acceptance or
page/document completeness. This is an independent extraction of selected
physical regions; it does **not** rewrite an archived Docling export or prove
semantic column headers, continuation relationships, surrounding page content,
OCR accuracy or engineering validity. The previous count of 103 blocked archived
page normalizations must not be reduced by subtracting these 54 pages.

## Root causes and changes

Docling can join body tables with drawing stamps, omit columns, move text across
columns and drop native cells. Disabling `do_cell_matching` on page 69 removed a
warning but duplicated labels and put text into wrong columns; this setting was
not enabled in the product.

`scripts/pdf_region.py` prepares SHA-bound PDF diagnostic crops and remaps their
Docling page references and both coordinate origins to the original page. It
rejects rotated/offset-crop pages, wrong hashes, invalid geometry and attempts to
overwrite source inputs. PDF/Docling serialization roundoff is bounded to
`1e-4 pt`; resizing and genuinely out-of-region geometry are rejected.

`scripts/recover_native_pdf_regions.py` reads an explicit schema2 manifest and
uses the existing source-text/grid verifier plus original vector detection and
empty-cell pixel checks. It does not require a neural table export. This avoids
making a correct native source grid depend on an incorrect neural bounding box.
The existing strict Docling replacement gate was not changed.

Initial fresh crop comparison: two regions on page 69 and regions on pages 142,
165, 397 passed strict source-grid replacement (344 cells). Page 139 remained
blocked in that comparison because Docling omitted the rightmost columns. Its
original native grid can be recovered by the independent route above.

## Environment and OCR

In this workspace's isolated `.venv-docling`, `libtorch_cpu.so` did not match its
installed RECORD and importing torch terminated with SIGBUS. Reinstalled only
`torch==2.14.1+cpu` from the official CPU wheel index. Fresh RECORD comparison and
imports of torch and `DocumentConverter` pass. Python 3.12.14; Docling 2.133.0.
This does not confirm or modify the user's Windows environments.

Fresh page-1 OCR with the original SHA: 18 blocks, 17 containing Cyrillic, all
located on original page 1; zero unlocated blocks and zero table-loss warnings;
12.6 seconds. It remains an unaccepted extraction candidate.

## Use

Use an isolated project Python containing PyMuPDF (`requirements-pdf-review.txt`).
Docling is unnecessary for the native-region command:

```text
python scripts/recover_native_pdf_regions.py ORIGINAL.pdf native-regions.manifest.json --project-id PROJECT --document-id DOCUMENT --output native-regions.recovered.json
```

The source manifest declares original coordinates, cells/spans, native text,
context, original SHA and `source_detection_clip` for every physical region.
Do not replace it with a model-generated table or a previous PASS audit. An
invalid input emits BLOCK with empty blocks and exit code 2, replacing stale
output candidates. Valid selected regions emit UNCERTAINTY with exit code 0;
that exit code is not full-document acceptance.

For a diagnostic crop:

```text
python scripts/pdf_region.py ORIGINAL.pdf --page 69 --bbox 55.904 24.920 573.400 317.490 --sha256 ORIGINAL_SHA --output region.pdf
```

Run Docling on the derivative, then call `remap_export` with the original, the
derivative, its mapping and the export; source-grid recovery must still be checked
against the original. The cropped region excludes surrounding content and PDF
annotations, so it cannot establish full-page completeness.

## Remaining work

- Continue independent OCR/visual checking for raster pages, signatures and
  drawings; low-resolution source scans remain unresolved.
- Preserve and inspect malformed/omitted grids, source images and ink-containing
  native-empty cells instead of treating them as empty or dropping them.
- Check semantic headers, table continuation and body/stamp separation on the
  original pages. A physical grid PASS does not settle those relationships.
- Assemble a page-by-page completeness audit across all 534 pages before any
  verified Evidence Register write. Engineering acceptance still requires
  FINAL AUDIT.
- These commands are local diagnostic/extraction tools. They have not been
  deployed or automatically enabled in the running application; main is unchanged.

## Validation

190 Python tests and 4 dashboard tests pass; JS syntax and Python compilation
pass. New tests cover real PDF crops, original-page coordinate restoration,
decimal serialization, invalid hashes/geometry/pages, merged native cells,
invented source text, visible ink in native-empty cells and stale CLI output.
Independent code review found no remaining significant issue.

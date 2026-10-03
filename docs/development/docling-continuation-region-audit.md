# V4 continuation region audit — 2026-10-03

The verified 534-page V4 source was investigated at pages 396–397 only.
Source SHA256: `b5d95b660b35bfb6b2441623635cba91c235efd754bc283dfe1405f075834916`.
The main-table region on source page 397 is `[60, 23, 545, 776]` PDF points,
TOPLEFT coordinates. Derived PDFs have separate hashes and local page 1;
their manifests map coordinates to the original source. They are not evidence.

| Experiment | Observed result | Adapter outcome |
| --- | --- | --- |
| Raster region | 12×4 grid, 47 cells; Cyrillic OCR errors | BLOCK: missing cell |
| Native/vector region | 12×4 grid, 48 cells; first body row falsely marked as header | BLOCK: suspected rebar body data in header |
| Native PDF line-grid experiment | 12×6, 72 cells, including 24 empty cells | Experimental candidate only; page remains BLOCK |

Both region experiments exclude the bottom stamp. A complete grid with Boolean
header flags alone was therefore insufficient: the previous adapter could emit
11 rows while silently using the first body row as headings. A supplementary,
conservative guard now blocks headings containing rebar quantity expressions
such as `8d20=25.133`. It is a narrow heuristic, not proof of header semantics;
a legitimate header containing such an example will require manual review.
Batch check version 6 invalidates earlier cached checks, including version 5.

The six column names were visually transcribed from source page 396. PDF vector
column boundaries align with page 397 within 0.005 points. Native text from the
first 11 rows matches an independent visual transcription in all 66 cells,
including the two empty outer columns. The twelfth row has an incomplete element
name in the source region; no missing axis or name was inferred. The header
mapping is case-specific and is not installed as automatic production recovery.

The raster region used 26.349 seconds and 1,615,896 KiB peak RSS; the vector region
used 26.307 seconds and 1,604,120 KiB. These are measured child-process values in
this Linux environment, not measurements of the user's Windows installation.
Docling 2.133.0 / docling-core 2.99.0 were used in an isolated Python 3.12 venv.
The native-grid reproduction uses separately available PyMuPDF 1.26.6;
PyMuPDF is not installed in the Docling venv and was not added as a project dependency.

Validation: 142 Python tests, JavaScript syntax checks, Python compilation,
actual diagnostic replay, and native candidate reproduction. Independent code
review found no critical or important defects. The private experiment archive
contains derived previews, manifests, diagnostics, logs, cell-level source
coordinates, visual comparison and a case-specific reproduction script.

Document status remains BLOCK; all experiment outputs are NOT_EVIDENCE with
acceptance disabled. No Evidence Register or Supabase writes, full-document
rerun, FINAL AUDIT, deployment, merge or main changes occurred.

Next: inspect the adjacent source page for the incomplete final row, then test
an explicit reviewed cross-page continuation mapping before broader batch work.

# V4: calculation screening, acceptance audit and archive readiness

Date: 2026-10-01. Document extraction remains **BLOCK**.

## Calculation books РР1–РР3

This is a targeted check of load-table arithmetic on PDF pages 18–25 and image verification of the cited discrepancies. It is not a complete check of the 429 + 286 + 298 = 1,013 calculation-book pages, normative applicability, reinforcement, stability, load combinations or solver results.

Source hashes, table bounding boxes, raw descriptions and per-row numerical checks are recorded in `v4_calculation_books_arithmetic.json`. All three sources are PROJECT evidence; their inputs cannot automatically replace the later V4 actual-structure inputs.

| Book | Tables screened | Rows with numerical products | Products outside printed rounding precision |
|---|---:|---:|---:|
| РР1 | 9 | 58 | 0 |
| РР2 | 9 | 53 | 0 |
| РР3 | 9 | 53 | 0 |

The arithmetic check compares normative load × factor with the printed design load, allowing half a unit of the last printed decimal. Approximate totals are not treated as exact equalities. РР1 has a table continuing onto page 23: only rows in regions with visible column headers enter the above count.

### Verified source discrepancies

All page numbers below are PDF pages; the drawing stamp's sheet number is one less.

| Sources and location | Printed inputs/output | Independent calculation | Conclusion |
|---|---|---|---|
| РР1, РР2, РР3, page 18, soil-pressure equation | 0.547 × (1.8 × 4.7 × 1.0) − 2 × 0.7 × √0.547 = 4.3 t/m² | 3.592187723 t/m²; with factor 1.152 from page 17: 4.295585963 t/m² | ERROR in printed equation arithmetic. Actual model factor/load unknown. |
| All three books, page 19, floor at −0.800, row 8 | Density 1800 kg/m³, thickness 50 mm; normative 387 kg/m², design 503 kg/m² | 1800 × 0.050 = 90 kg/m²; 90 × 1.3 = 117 kg/m² | UNCERTAINTY: description and tabulated load disagree. 387 × 1.3 = 503.1 rounds to the printed 503. |
| All three books, page 22, 200 mm partitions, row 3 | D500 label, density 600 kg/m³, normative 100 kg/m², design 130 kg/m² | 600 × 0.200 = 120 kg/m²; ×1.3 = 156 kg/m². 500 ×0.200 =100 kg/m². | UNCERTAINTY: density/material description and load disagree; intended input unknown. |
| All three books, page 23, 200 mm external walls, row 3 | Same density/thickness/normative/design values | Same 120 and 156 kg/m² | Same unresolved input inconsistency. |

These are 12 source occurrences in three repeated issue families, not 12 independent structural failures. Every cited region was inspected in rendered source images. Do not silently correct source documents or declare the solver wrong. Resolving them needs confirmation of intended layer thickness/material density/soil factor and the corresponding actual model load records.

The V4 heights 4.0/3.4 m and selfweight factor 1/1.1 remain unresolved as documented in `V4_PAGE_254_PROJECT_CALC_CROSSCHECK.md`. Page 254 recovery does not resolve these engineering assumptions.

## Evidence and final-status audit

Read paths: normalized document → evidence bridge → validation/persistence; EngineerCore result collection/final status; Supabase acceptance adapter. Existing tests cover missing page provenance, wrong source hash, changed content, batch rejection, evidence identifiers, accepting specialist proof, final-audit coverage, explicit BLOCK, missing/unavailable acceptance gate and foreign task responses.

55 targeted tests passed, including the archive/overlay/export tests; the full local suite subsequently passed all 163 tests. These are local unit tests with fake transports; no production Supabase database or live acceptance RPC was exercised. The database's live contents and enforcement are therefore not certified here.

A valid source/page link verifies identity and traceability; it does not prove that a partial document is complete or an extracted table is visually correct. No archive result is passed to the acceptance gate by this diagnostic workflow.

One misleading diagnostic counter was corrected: `remaining_blocked_pages` now retains all 137 original blocked pages. `remaining_manual_review_pages` separately records 135 pages after the manual route for pages 490–491. Both manual pages remain UNCERTAINTY; the original audit is unchanged and the document stays BLOCK.

## Incoming archive

`scripts/v4_region_archive_check.py` reads the ZIP without extracting or executing anything. It checks manifest identity, exact blocked-page coverage/reasons, missing/foreign/duplicate members, per-page identity/provenance, positive table dimensions, cell-span bounds, overlap and missing grid positions. Merged cells are counted without flattening them. Likely stamp labels in body tables are flagged.

Optional independent PDF candidates are compared by dimensions and nonempty text multisets. This does not prove region correspondence, cell placement, headers, captions, formulae, photos or colour semantics. Candidate mismatch is a review signal, not proof that either extractor is correct. All diagnostic page/document statuses remain BLOCK even when the ZIP is complete and text agrees.

Run after the archive is available:

```powershell
cd C:\Users\maxim\engineer-os
.\.venv\Scripts\python.exe .\scripts\v4_region_archive_check.py `
    "$HOME\Desktop\v4-blocked-regions.zip" `
    .\.engineer-os\v4-docling-check\v4-extraction-review.json `
    .\.engineer-os\v4-docling-check\v4-region-archive-check.json `
    --candidates .\docs\v4_offline_table_candidates.json
```

The checker can process an incomplete export bundle and preserve its failed-page list. Missing pages must be retried with the existing resumable exporter. The next required input is `v4-blocked-regions.zip`; automated completeness checks then precede source-image review and any evidence recovery.

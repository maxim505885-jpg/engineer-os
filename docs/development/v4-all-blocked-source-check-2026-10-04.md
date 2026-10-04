# All blocked native cell checks and bulk recovery — 2026-10-04

Original V4 source SHA256 was freshly checked. Audited every model-declared table cell on all147blocked pages:200declared tables,9,174cells. Matching uses original PyMuPDF native word centroids inside TOPLEFT cell boxes and whitespace normalization only.

| Native binding result | Cells |
| --- | ---: |
| Exact native literal match | 6,945 |
| Native text differs from declared text | 521 |
| No native words inside declared box | 1,707 |
| Missing source cell box | 1 |

These results are scoped to model-declared cell regions. They do not prove visual glyphs, clipped tails, actual source table topology, omitted tables, normative headings or full-page completeness. Text differences are discrepancies requiring review, not proven engineering errors. No native words is not a proof that a cell is blank.

73declared tables match all their cell literals. Of those,25also have non-overlapping complete model grids. Generated source-word partitions for these25grids and rechecked each resulting literal directly against the source using the existing schema2 verifier:652cellsPASS. Partition boundaries are inferred from text ink boxes and are not visually verified physical PDF rulings. Original header/section meaning is not inferred. Some model-classified tables may be page stamps. Candidates remain UNCERTAINTY/NOT_EVIDENCE; no full-page or evidence acceptance.

All25grids were also rechecked through the existing batch path, grouped by18original source pages:4,55,56,100,107,109,110,112,140,166,175,236,254,266,268,336,337,404. Reviewed-region binding PASS for each batch; Docling NOT_RUN for these sidecar-only reruns, documentBLOCK preserved. The original147blocked page audits were not overwritten.

## Page260 raster table

Visually transcribed the original embedded751×342table image into27physical cells covering32logical slots. Preserved vertical merged cells for row numbers1and2, the horizontal final-cell merge and four explicitly blank cells. Raw Docling's21nonempty cells omit row numbers1and3and omit four source blank cells. Corrected text is a separate declared visual transcript; raw OCR is unchanged. Mathematical subscripts are transcribed as Pₜ/Qₜ without making a claim about their normative applicability.

Rehashed the original PDF, checked original xref54654image bytes against the saved image and verified placement bounds. Image identity and declared grid coverage PASS. This does not automatically validate typed text: transcription review is DECLARED_NOT_INDEPENDENTLY_VERIFIED, independent review and normative/calculation checks remain unperformed. Recovery candidate is UNCERTAINTY; overall Docling/page/documentBLOCK is preserved.

## Outcome and remaining limits

All available automated native-binding checks for the147blocked pages are completed and retained. The original overall adapter result remains147BLOCK/387UNCERTAINTY, with37loss-warning pages. Recoveries add source-bound candidates, not a blanket override of extraction errors. The current176-test code remains unchanged in this diagnostic step.

Remaining work requires verifying source-image/outlined-vector content, cell discrepancies and missing source regions, then checking complete source-region coverage. It is not safe to replace these unresolved items with PASS merely because conversion finished or tests passed. No main change, merge, deployment or evidence database write.

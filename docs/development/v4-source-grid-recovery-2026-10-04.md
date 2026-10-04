# V4 source-bound merged table recovery — 2026-10-04

Docling's strict table adapter still blocks ambiguous or merged cells. It must not be weakened merely to mark the document accepted. The existing reviewed-region verifier now accepts an explicit schema-2 physical grid: source coordinates, row/column spans, original text, table/cell identities and review context. Schema-1 six-column continuation recovery remains unchanged.

The verifier hashes the original source, checks native word-region text, bounds and exact declared grid coverage, and rejects holes, overlaps, altered text and invalid spans. Merged cells are exported once with their original span. This PASS is limited to declared grid coverage and native text binding. It does not prove visual content, calculation correctness, actual PDF rulings or full extraction completeness. Candidate exports remain UNCERTAINTY / NOT_EVIDENCE, complete_document=false, document_status=BLOCK, acceptance_granted=false. This schema is a standalone recovery export and is not integrated into the Docling batch acceptance path.

## Fresh source result

- Original PDF: 74,522,583 bytes; 534 pages.
- SHA256: b5d95b660b35bfb6b2441623635cba91c235efd754bc283dfe1405f075834916.
- Page 259 visually inspected; seven eight-column tables.
- Seven merged total cells each span the first five columns.
- 220 physical cells cover 248 declared logical grid slots.
- Original native text-region binding audit: PASS, acceptance remains false.
- Includes previously omitted total: Итого | 1,071 | 1,3 | 1,393.
- Native strings are preserved, including potentially visually clipped labels. No normalization into invented engineering labels or calculation acceptance.

## Verification and review

- Baseline: 169 Python unit tests pass.
- Added merged-grid positive/negative tests and a regression for ambiguous table/cell identity concatenation. The regression failed before its fix.
- Final: 172 unit tests pass; browser JavaScript syntax and engineering/runtime/e2e compilation pass.
- Focused code review found the identity collision; exports now encode table/cell pairs unambiguously.

## Restored environment and unresolved stage

The execution environment reverted to an earlier snapshot. The saved archive was restored with results for pages 1–495. A separate benchmark export for page 499 is not a replacement for the missing full-pass results of pages 496–534. The prior observed full-pass totals (534 exports, 147 BLOCK and 387 UNCERTAINTY) are historical results, not a fresh rerun in this restored environment. An archived intermediate adapter report covers 331 pages.

The project virtual environment retained Docling packages but lost its Python executable link. The link was restored to the existing compatible Python 3.12.14 interpreter; isolated Docling import succeeds. No global installation was performed. The full-pass model files and derivative page PDFs are absent from the restored archive. Original derivative hashes cannot be reused for newly generated PDFs without fresh copy verification.

Remaining: restore model artifacts and source-verified page copies before regenerating missing exports; triage blocked tables using explicit source grids; visually verify pages 492–531 vector drawings and OCR disagreements; account for all 534 pages and warnings; run full extraction completeness gates before evidence promotion or FINAL AUDIT. No evidence database writes, main changes or merges.

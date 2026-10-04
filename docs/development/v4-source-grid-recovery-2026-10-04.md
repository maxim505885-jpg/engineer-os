# V4 source recovery and restored full export — 2026-10-04

## Confirmed result

- Original PDF rehashed: 74,522,583 bytes, 534 pages, SHA256 b5d95b660b35bfb6b2441623635cba91c235efd754bc283dfe1405f075834916.
- All 534 raw exports are now retained. Restored pages1–495; freshly regenerated pages496–534.
- Current adapter diagnostic: 147 BLOCK, 387 UNCERTAINTY; 37 pages with explicit dropped-cell warnings. No document acceptance.
- Block reasons: 80 missing/merged/ambiguous cells; 46 missing grids; 13 ambiguous header metadata; 3 mixed page stamps; 2 table captions without verified rows; 3 otherwise parseable pages with explicit loss warnings. Loss warnings on other blocked pages overlap these categories.
- The previous page15–16 conversion blocker is absent in a fresh accurate-mode run: 43 blocks, seven table rows, zero unlocated blocks, zero table-loss warnings, 27.0 seconds; reviewed baseline 8/8 PASS.
- Fresh offline source page1 conversion: 18 blocks, 17 with Cyrillic, all located with bounding boxes; no table loss warnings; 18.9 seconds.
- Fresh page499 export still fails two captions (ФС3 and ФС6), baseline9/11. Do not silently rewrite raw OCR.

## Code changes

The reviewed PDF recovery verifier formerly supported only six-column continuation rows. Schema2 now preserves explicit physical grids and row/column spans, rehashes the source, compares native word-region text, checks bounds and exact declared grid coverage, and rejects holes, overlaps, altered text and invalid spans. Merged cells export once with their original span and unambiguous table/cell identity encoding. Schema1 remains compatible.

PASS means declared grid coverage and native text binding only. It does not prove visual content, PDF rulings, calculations or full extraction completeness. Exports remain UNCERTAINTY / NOT_EVIDENCE, complete_document=false, document_status=BLOCK, acceptance_granted=false. This standalone export is not integrated into the Docling batch acceptance path.

Independently normalized pages previously reused text IDs such as docling:1. Text IDs now include original page identity, preventing collisions when combining disjoint page chunks; table row IDs already contain the page. CHECK_VERSION9 invalidates prior batch caches.

## Source-bound recovery

Page259 was visually inspected: seven eight-column tables, 220 physical cells covering248 logical slots. Each total row merges the first five columns. Native source binding PASS; includes the formerly omitted Итого | 1,071 | 1,3 | 1,393. Original native strings, including potentially clipped labels, are preserved. Engineering meaning and arithmetic are not accepted.

Legacy pages396–404 were freshly rechecked against the original PDF: 91 logical rows, 546 cells, 570 source fragments PASS for source binding; remain NOT_EVIDENCE/documentBLOCK.

## Environment restoration and limits

The execution environment reverted to an earlier snapshot. The saved495-page archive was restored; its separate benchmark page499 was not counted as a tail completion. The project venv retained packages but lost its Python executable link. Restored that link to the compatible existing Python3.12.14 interpreter; isolated Docling import succeeds, without global installation.

Official layout/table model files were restored and matched retained SHA256 checksums. Three OCR models were also hash-checked. An initial retry failed because OCR files were absent at the explicit artifacts path; the failure log was preserved and files copied to that path before rerun. All39 regenerated tail page copies passed original native-word and RGB72dpi identity checks, with fresh derivative hashes. Tail conversions exported39/39 pages in737.54 summed seconds, peakRSS3,371,964KiB (~3.22GiB).

The diagnostic adapter recheck distinguishes archived copy attestations for pages1–495 from fresh physical derivative hashes for pages496–534. Original page-copy files for the first495 remain unavailable; do not label their physical derivative identity freshly reverified. Original source identity is freshly checked. No OCR, visual or document completeness acceptance.

## Verification and remaining work

174 Python unit tests pass; browser JavaScript syntax and engineering/runtime/e2e compilation pass. Positive merged-grid and chunk-identity regressions failed before fixes. Focused review identified the first identity collision, which was fixed with a regression; follow-up review found no important issues in the page identity/cache changes.

Remaining: integrate reviewed source grids into an explicit extraction-completeness audit without overriding unresolved regions; source-check all147 blocked pages and37 loss warnings; verify outlined vector drawings492–531, including OCR disagreements; account for all source regions across534 pages before evidence promotion/FINAL AUDIT. The seven recovered tables on page259 are candidates, not a declaration that its entire page is complete. Windows checkout/Ollama remain unverified from this environment. No main changes, merges, deployments or evidence database writes.

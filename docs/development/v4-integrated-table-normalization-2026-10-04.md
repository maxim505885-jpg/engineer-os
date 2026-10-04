# Source-checked table normalization

Recovered grids previously remained separate sidecars and could not resolve failed table normalization. The existing batch now accepts an original single-page archived raw export through `--raw-export` with a reviewed schema2 manifest. It writes combined-extraction.json while preserving the original export and Docling audits.

The source PDF is rehashed and every grid fragment is read again from its original page. Recovery targets require the exact original Docling table index and canonical SHA256 digest. Model/source dimensions, spans and cell text must match; merged cells and source-bound empty text remain structured cells, without inferred headings. Other failed tables remain explicitly unresolved. Source-empty text does not establish visually blank content.

Raw body blocks use original PDF dimensions and checked page/bbox ranges, but their text remains marked UNCHECKED. Recovered cells are marked source binding PASS. Every result remains NOT_EVIDENCE, acceptance false and page/document completeness false; document BLOCK is preserved. Table normalization UNCERTAINTY is not a full-page extraction result.

Fresh real V4 batch runs:25 mapped grids/652 cells across18 pages. All declared source bindings passed. Table normalization resolved all exported table errors on pages4,55,100,107,110,112,166,236,404 (9 pages); the other9 retain concrete unresolved-table lists. The full534-page adapter audit has not been superseded or marked complete.

182 local unit tests pass, including real PDF source changes, target changes, unmapped tables, invalid page references, stale-output invalidation and input/output alias protection. The real-PDF test requires the existing optional requirements-pdf-review.txt dependency and skips when absent. Focused code review findings were reproduced and fixed. No main changes, merges or evidence database writes.

## Current source-grid continuation

Commit 35cee3cd4847fd8a82395d32946c8156b6e83ac8 adds measured bottom-stamp variants and explicit SOURCE_VECTOR_GRID replacement. The default MATCH_MODEL_GRID mode still requires exact model dimensions, spans and text. Vector replacement repeats original physical-cell detection in the declared clip, requires matching target-region geometry and rejects embedded images. Native-empty cell interiors are rendered and rejected when visible ink remains. Target digests and original SHA256 remain mandatory; oversized target coordinates fail closed. This repairs damaged model grids without asserting extraction completeness.

All 534 archived exports were rechecked through adapter check version 10: 128 BLOCK and 406 UNCERTAINTY, compared with the retained baseline of 147 BLOCK and 387 UNCERTAINTY. This is an adapter recheck, not a new full Docling conversion. The 26 newly recognized stamp token multisets matched original native source tokens; 19 pages lost stamp-only parser errors.

Thirty vector grids containing 1,226 cells passed physical-grid, image exclusion and native-empty-cell checks in the first bounded replacement probe. Page 10 was rejected because signature images occupy table cells. Its images must not become empty strings. The 23 actual batch invocations matched the direct normalization results: 18 UNCERTAINTY and five unresolved BLOCK, with overall batch exit code 2 because document completeness remains unverified.

A focused target-region search covered all 128 remaining parser-blocked pages. Combining its checked grids with earlier mapped recoveries resolves exported table normalization errors on 25 pages: 4, 55, 56, 71, 85, 100, 107, 109, 110, 112, 166, 175, 234, 236, 254, 265, 268, 304, 337, 404, 429, 450, 474, 477 and 490. The combined route therefore retains 103 blocked pages. This count concerns table normalization only; it does not supersede the adapter baseline or verify whole pages. All candidate body blocks, uncovered images and source completeness retain their existing unverified states.

Offline RapidOCR in an isolated Python 3.12 environment produced source-located candidates for pages 5–7. The original embedded ToR scans on pages 5 and 6 are only 570×775 and 568×806 pixels. Sixty-six of 98 and 75 of 108 recognized blocks, respectively, scored below 0.8; distorted text is not accepted. Two available Drive Word reports were inspected for better ToR originals, but their embedded ToR identifies a different object in Rostov region, Miusskaya 27. They cannot supply missing V4 requirements.

GitHub CI run 37225017681 for the code commit completed successfully. Local 182-test verification and focused review passed. FINAL AUDIT, complete-page/full-document extraction and evidence acceptance have not passed.

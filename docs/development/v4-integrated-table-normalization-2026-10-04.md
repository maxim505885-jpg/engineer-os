# Source-checked table normalization

Recovered grids previously remained separate sidecars and could not resolve failed table normalization. The existing batch now accepts an original single-page archived raw export through `--raw-export` with a reviewed schema2 manifest. It writes combined-extraction.json while preserving the original export and Docling audits.

The source PDF is rehashed and every grid fragment is read again from its original page. Recovery targets require the exact original Docling table index and canonical SHA256 digest. Model/source dimensions, spans and cell text must match; merged cells and source-bound empty text remain structured cells, without inferred headings. Other failed tables remain explicitly unresolved. Source-empty text does not establish visually blank content.

Raw body blocks use original PDF dimensions and checked page/bbox ranges, but their text remains marked UNCHECKED. Recovered cells are marked source binding PASS. Every result remains NOT_EVIDENCE, acceptance false and page/document completeness false; document BLOCK is preserved. Table normalization UNCERTAINTY is not a full-page extraction result.

Fresh real V4 batch runs:25 mapped grids/652 cells across18 pages. All declared source bindings passed. Table normalization resolved all exported table errors on pages4,55,100,107,110,112,166,236,404 (9 pages); the other9 retain concrete unresolved-table lists. The full534-page adapter audit has not been superseded or marked complete.

181 local unit tests pass, including real PDF source changes, target changes, unmapped tables, invalid page references, stale-output invalidation and input/output alias protection. The real-PDF test requires the existing optional requirements-pdf-review.txt dependency and skips when absent. Focused code review findings were reproduced and fixed. No main changes, merges or evidence database writes.

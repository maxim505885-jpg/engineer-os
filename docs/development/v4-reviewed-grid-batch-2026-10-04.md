# Reviewed physical grids in the Docling batch — 2026-10-04

The standalone verifier supported merged physical grids, but local_docling_batch still required legacy six-column row manifests and rejected schema2. The batch now accepts either reviewed format, checks original body page scope, validates source-binding output identity, unaccepted flags and counts, and reports declared-region coverage separately from Docling status. Successful recovery cannot erase an unsuccessful Docling audit or establish full-page/document completeness.

## Fresh checks

- Baseline174 unit tests; final176 pass, including a failing-before-fix grid integration regression. JavaScript syntax and runtime compilation pass.
- Focused review found no important issues;13 targeted batch/grid tests pass.
- Source page259: seven grids,220 physical cells,248 logical slots. Source binding PASS in the batch. Native Docling still rejects merged/ambiguous cells; overall document BLOCK remains.
- Source page260 visually inspected: the top table has20 physical cells,24 logical slots, merged first-five-column total Итого | 0,228 | 1,3 | 0,296. Source binding PASS through the batch; full-page completeness false.
- The lower table on page260 is an embedded751×342 image (xref54654), bounds[56.70000076293945,148.18997192382812,531.5499877929688,364.4399719238281]. No native words or vector table rulings exist inside it. Its image bytes and SHA256 were saved as an unresolved BLOCK region. Empty native text is not proof of empty cells; no normative or arithmetic conclusions were accepted.
- Legacy source pages396–404:91 logical rows/546 cells/570 fragments, source binding PASS through the batch, no completeness/evidence acceptance.

The actual combined Docling/review run initially exposed missing PyMuPDF inside the Docling venv. Installed only the repository-pinned optional requirements-pdf-review.txt (PyMuPDF1.26.6) into its existing isolated Python3.12.14 environment. Repeated the combined batch to check both subprocesses with the same interpreter. No global installation, new architecture, main change, merge or evidence DB write.

## Remaining stage

The complete534-page export is preserved. The last full adapter diagnostic remains147BLOCK/387UNCERTAINTY, with37pages reporting table-cell losses. Declared reviewed-region summaries are now usable within the bounded batch; they do not demonstrate that unreviewed page content is complete. Next work is raster-table OCR with source image verification and a source-region completeness ledger, retaining unresolved gaps and avoiding promotion of partial recoveries.

## Raster OCR probe

Ran cached Cyrillic RapidOCR directly on the embedded page260 table, with3× preprocessing and Python networking disabled. It produced60 located text candidates in2.96 seconds. Main numeric entries are present, but OCR changes punctuation (20,0→20.0 and100,0→100.0), omits/splits words and confuses Cyrillic/Latin glyphs. The raw strings and confidence scores remain unchanged. Candidates have original page coordinates and source image SHA256; they are UNCERTAINTY/NOT_EVIDENCE, while the raster region remains BLOCK for full transcription/grid verification. This is a diagnostic probe, not an accepted normative table.

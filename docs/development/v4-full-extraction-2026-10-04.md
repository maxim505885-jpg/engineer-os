# V4 full-document extraction checkpoint — 2026-10-04

## Result

The full raw Docling pass exported **534/534 pages without conversion failures**. Re-evaluation of all exports with the current adapter produced **147 BLOCK pages and 387 UNCERTAINTY pages**. This is a completed raw pass, not a verified document. Whole-document status remains **BLOCK**; `complete_document=false`, `acceptance_granted=false`. No Evidence Register/Supabase writes, main changes, merges or deployment occurred.

Source: `15.09.2026 ТЗК БЦ ул. Набережная 28А V4 сшито с графикой.pdf`; 74,522,583 bytes; SHA256 `b5d95b660b35bfb6b2441623635cba91c235efd754bc283dfe1405f075834916`. Each single-page derivative was checked against original native words and RGB rendering at 72 dpi; all 534 checks passed and derivative hashes were retained. This does not prove OCR or engineering accuracy.

## Confirmed checks and limitations

| Check | Observed result | Scope |
|---|---|---|
| Python regression suite | 169 tests passed | Code contracts only |
| CI at 9035ed6062bd396424cc7d90f7f106bd274eefb1 | Run 37183704821 succeeded | Core tests, compilation and JavaScript syntax |
| Raw Docling exports | 534/534 EXPORTED | Raw conversion only |
| Current adapter recheck | 147 BLOCK; 387 UNCERTAINTY | Structural and source identity gates |
| Explicit dropped-table-cell warnings | 37 pages | Actual model warning, not a hypothetical risk |
| Page 15–16 baseline | 8/8 passed | Declared table/text expectations only |
| Page 499 automatic OCR baseline | 9/11 passed: ФС3 and ФС6 failed | BLOCK regression; raw OCR unchanged |
| Page 499 visual caption review | 11 captions checked | Separate source-bound correction candidates; dimensions/geometry unverified |
| Reviewed recovery, pages 396–404 | 91 rows / 546 cells / 570 fragments source-bound | NOT_EVIDENCE; semantics/completeness unaccepted |
| Native inventory | 534 pages; 52,609 words | 40 pages have no native text; this is not empty-source proof |
| Native table/grid detector | 716 regions; 23,790 physical rectangles | Includes frames/figures, not 716 validated engineering tables |
| Fourteen region gap candidates | 1,626 native words preserved | Hierarchical ownership only; original grid statuses unchanged |

Page 259's omitted total-row fragments `Итого | 1,071 | 1,3 | 1,393` were rechecked against original words, rendered source and vector ruling endpoints, with the merged label cell preserved. They remain unaccepted recovery candidates.

Independent native reader differences on 41 pages reconcile mechanically through exact duplicate-paint removal and clipping policy. Some encoded caption tails are invisible in the rendered source (e.g. page 385); they must not silently become visually verified values.

## Code fixes

- Missing requested page provenance now yields BLOCK even when the chunk process exits successfully.
- Explicit local Docling model directory via `--artifacts-path` or `ENGINEER_OS_DOCLING_ARTIFACTS_PATH`; missing configured paths fail before initialization.
- BOTTOMLEFT text boxes normalize to TOPLEFT using actual exported page height; unavailable/invalid geometry keeps page-only provenance.
- Exact six-label bottom stamp variant on pages 34/51 recognized with literal labels, complete offsets, false header flags and bottom location. Damaged engineering tables remain blocked.
- Cache check version 8 invalidates prior audits. Independent code reviews found no important issues.

Docling 2.133.0, docling-core 2.99.0, Torch 2.14.1+cpu, RapidOCR 3.9.2, ONNX Runtime 1.30.0, pypdfium2 5.13.0 were used in the isolated Python 3.12 environment. No global Python 3.13 installation or paid API was used. Sum of page conversion times: 3,816.6 seconds; peak worker RSS: 3,495,900 KiB.

## Remaining work

1. Recover the 147 structurally blocked pages through source-bound cell/span/header/context mappings; do not waive missing-cell or dropped-cell gates.
2. Add controlled overlapping region OCR for large outlined-vector drawings, preserving source SHA, original page and coordinate transforms. A page-493 legend crop probe improved readability but still has errors and crop-boundary truncation; it is not a production fallback.
3. Review disagreement and OCR coverage before any document-completeness claim. Page 499's visually reviewed corrections are separate from the still-failing automatic regression.
4. Only after complete verified extraction, proceed to engineering evidence, normative checks, calculations and FINAL AUDIT. ACCEPTED remains unavailable.

The second built-in PDF reader exported page 493 in 19.58 seconds versus 277.23 seconds for the default reader, but its text inventory differed (140 versus 172 blocks); speed alone does not justify replacement. Both diagnostic outputs remain untrusted.

The user's Windows checkouts and local Ollama were not accessed. This Linux verification does not establish their installation state. Application remains at the Document Intelligence integration/recovery stage; these results do not establish an end-to-end accepted engineering conclusion.

## Artifact availability

A durable intermediate archive was saved at 495 processed pages. After the 534-page pass and complete adapter recheck, the execution service disconnected before final archive replacement. Do not describe the earlier archive as the complete raw-export package. The complete run counts above were observed before disconnection; this repository checkpoint preserves those results.

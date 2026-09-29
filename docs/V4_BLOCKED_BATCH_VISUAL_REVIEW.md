# V4 blocked pages: full image inventory and visual triage

Source PDF SHA-256: `b5d95b660b35bfb6b2441623635cba91c235efd754bc283dfe1405f075834916`  
Source page count: 534  
Extraction report: `v4-extraction-review.json`, 230 successful chunks, 137 blocked chunks, status `BLOCK`.  
Input: `v4-blocked-pages.rar`, received 2026-09-29; seven embedded ZIP portions with manifests and rendered page PNGs. The separate 12-page sample is recorded in [V4_VISUAL_SAMPLE_REVIEW.md](V4_VISUAL_SAMPLE_REVIEW.md).

## Inventory result

Each embedded ZIP manifest names the same source SHA-256 and 534-page source. The portions contain 20, 20, 20, 20, 20, 20 and 5 PNGs. Their union is 125 distinct page numbers; it exactly equals the 137 pages listed under `blocked_reasons` in the extraction report minus the 12 pages in the earlier visual sample. There are no duplicate, missing, or extra page numbers in this union. The input is a container of ZIP portions, so a simple archive listing can expose only the last portion; inventory verification must enumerate all seven.

The 125 supplied PNGs were inspected visually for **layout triage**. Together with the earlier sample, all 137 blocked page images have a visual route. This establishes neither correct extraction nor engineering validity. The original PDF was subsequently obtained from the connected Google Drive and independently hashed to the same SHA-256; it contains 534 pages.

A separate read of the PDF's embedded text layer found text on 136 of these 137 blocked pages. Page 500 has no extractable text in that layer and is a drawing sheet in the rendered image; it needs image/drawing review. The presence of an embedded text layer on the other pages is not evidence that Docling preserved their tables, photographs, ordering, colours or formulas.

### Page 500: drawing-only route

The source PDF sheet (A1, 1684 × 2384 pt) was rendered again at 120 dpi for a closer read. It has four plan views arranged as two upper views and two lower views. The title block calls it figure **Ж.9** and describes plans of the fifth floor, beams and slab, defects/damage and results of the detailed survey. The independent drawing register on PDF page 490, row 9, confirms `Ж.9` and the levels `+18.000` and `+21.800`. The large defect legend visibly groups numbered symbols for slabs, columns, walls, stairs and basement walls. A second legend maps coloured leaders and markers to openings, concrete-strength measurements, column marks, reinforcement counts and defect/photo callouts. These are separate evidence regions: a parser's table detection in the legend or title block cannot stand in for the plan annotations. The text layer is empty, so no searchable text from this page is available as a cross-check. Keep the page `BLOCK` until the plan labels, axes, marked locations and each legend key are transcribed at sufficient resolution and linked to exact source regions. The observed legend descriptions are not, by themselves, findings that every depicted element has those defects.

## Visual routes

| Pages and examples | Observed layout | Required comparison before resolving a block |
| --- | --- | --- |
| 142–165 | Long concrete strength measurement table; headings and aggregate values span many numbered measurements and page boundaries. | Match every row, group membership, measured value, units, and aggregate cell to the source image; carry headings across page boundaries without inventing duplicated cells. |
| 55–56, 224, 234–235, 244, 297, 304, 320, 396–403, 429, 449–452, 473–474 | Actual reinforcement and calculation comparison tables, some with red and green values and accompanying conclusions. Page 297 explicitly contains a conclusion about insufficient column reinforcement; page 474 contains an insufficient slab reinforcement conclusion. | Preserve colours and annotations as evidence, map all actual and required quantities to their elements and axes, and compare conclusions to extracted text. Never infer safety from colour or from a missing cell. |
| 69, 71, 78, 85, 97, 99, 101, 104, 106, 109 | Defect cards mix headers, narrative, photographs, and condition labels. | Verify each card's text, identifiers, severity wording, and links to its photographs. A merged region may be an actual card header. |
| 138–140, 171, 174–183, 246, 255–260, 265–269, 335–343, 345–346 | Instrument/calibration, geotechnical, load, and snow-load calculations; genuine tables alternate with equations, figures, and continuation text. | Compare table rows and totals, units, formulas and figure captions independently; preserve cross-page continuations. Page 335 is a prose conclusion with material engineering claims. |
| 5, 7–10, 261, 263, 343, 477, 481, 486–491 | Technical assignment, registers, standards excerpts, equipment list, verification document, registry extracts and drawing index. Signatures, QR codes, rotated pages and title blocks may coexist with real tabular rows. | Verify register fields and actual rows; separate stamps, title blocks, QR codes and signatures from table cells. Pages 487–489 contain registry tables and 490–491 contain drawing index tables. |
| 11, 17, 20, 22, 61–64, 113, 116, 118, 132–133, 136, 168, 173, 476, 500 | Predominantly prose, figures or drawing sheets. Some detections may concern a page frame, title block, or layout rather than a main data table. | Inspect the parser's reported table bounding box against the page and verify all prose, figures, legends and title-block content before classifying a table detection as spurious. |
| 28, 30, 44, 57–58, 264, 267, 292, 369 | Mixed drawings, photographs, diagrams, captions, formulas and/or small tables. Pages 57–58 have illustrated table captions despite `OTHER_EXTRACTION_FAILURE`. | Review text, captions and visual evidence as separate regions; verify whether an actual table lies within the reported region. |

The rows above are routing examples, not a disjoint classification or a claim that every table cell has been verified. Some pages belong to more than one route.

## Decision and next evidence

`MERGED_TABLE_CELL` (78 pages), `MISSING_TABLE_CELLS` (52), `DROPPED_TABLE_CELLS` (5) and `OTHER_EXTRACTION_FAILURE` (2) remain blocked. In particular, `DROPPED_TABLE_CELLS` on 78, 109, 397 and 401 affects actual cards or engineering comparison tables; treating all five as harmless would be unsafe. The footer retry on pages 18, 34, 51, 100, 170 and 254 produced `UNCERTAINTY`, not a pass.

The next check needs page-bound parser output, detected table geometry/cells, text and figure regions, and a verified source PDF for side-by-side comparison. Record a per-page, per-region disposition with evidence and retain `BLOCK` for any unverified content. The inventory and visual observations alone do not authorize a change to extraction status or downstream engineering conclusions.

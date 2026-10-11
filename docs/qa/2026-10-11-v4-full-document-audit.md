# V4 all534 native/table/source audit

Source: 74522583 bytes; SHA256 b5d95b660b35bfb6b2441623635cba91c235efd754bc283dfe1405f075834916. After audit: b5d95b660b35bfb6b2441623635cba91c235efd754bc283dfe1405f075834916. Repository candidate4641743. PyMuPDF 1.26.6. V2 implementation SHA256 d1f18823536abcfbef4210fed3a049e0fd9e4f1c89fcc065cbbfa13d3f87642b.

534 pages inspected computationally; 494 have native text; 374397 native characters. 716 V2 candidates on 494 pages; 57027 slots, 23790 non-null geometries, 33237 unresolved null slots. 528 large-frame heuristic suspects.

Clip comparisons: 19104 exact string mismatches, 959 whitespace-stripped order mismatches, 788 character-multiset mismatches. Character differences are candidates for review, not proof of a source or extraction error: clip and detector text can use different inclusion boundaries/deduplication. Exact page/candidate/row/column/bbox and both texts are in character-content-mismatches.json and cell-clip-comparisons.jsonl. Null-slot coordinates and complete candidate payloads are in all534-native-v2-audit.json and v2-payloads.jsonl.

Character-multiset mismatch pages: [244, 257, 258, 259, 348, 371, 372, 373, 374, 375, 376, 377, 378, 379, 380, 381, 382, 383, 384, 385, 386, 387, 388, 389, 390, 391, 392, 393, 394, 395, 405, 406, 407, 409, 410, 411, 413, 417, 421, 422, 423, 424, 425, 426, 427, 428, 449, 473].

All534 pages rendered successfully in visual/; source render hashes and per-page native hashes are in visual/manifest.json. Native text absent on492–531. Dense vector diagrams on532–534 have only32/36/60 native chars, so native-gap-only OCR misses those pages. OCR requested for empty pages but blocked: installed tesseract models eng/osd, local rus model unavailable. No OCR candidate or OCR correctness claim.

Representative rendered pages visually inspected:66 (two actual five-column tables; source narrative clips at right page edge),138 (merged multiline locations, vertical S3, formula header),371 (color-scale/column diagram; candidates1/2 are visually false table interpretations),492 (three dense vector plans with labels, no native text),532 (dense shaft measurement diagram; native32). These inspections are bounded examples, not all-cell qualified review.

Whole-sheet candidate0 on native pages generally includes page frame, body and title block. Actual table candidates coexist, e.g. page66 candidates1/2 (6x5,8x5) and138 candidate1 (40x7,66 null slots). Null slots preserve unresolved merged/missing relations; they do not certify merged anchors. Diagram candidates must not be promoted to semantic tables.

Concrete cell/clip mismatches:244/candidate1/r17/c4: detector Поперечная А240 vs clip extra preceding р;257/c1/r3/c3 detector0,025 vs clip а 0,025;258/c1/r2/c3 andc2/r3/c3 detector0,05 vs clip а 0,05. Page371 diagram/scale text exhibits duplicated native numbers and clipped decimal glyph differences.

Confirmed: original bytes retained, all page renders created, native candidate text hashed, V2 detector values/coordinates/null slots preserved in hashed payloads, no page scan exceptions. Remaining BLOCK/UNCERTAINTY: unread vector-label content492–534, unavailable rus+eng OCR, unresolved null-cell relations, false frame/diagram candidates, cell boundary/content mismatch review, graphics/formula engineering semantics and qualified approval. No semantic equivalence, acceptance, full table preservation, or FINAL_AUDIT asserted.

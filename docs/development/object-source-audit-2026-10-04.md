# V4 mixed source grids and eight additional object sources

Baseline: `c3d30b85c0c7e9c9e8b5881934aa875881df369b`, PR34. Work is isolated from main. This checkpoint does not grant evidence acceptance.

## Mixed grid capture

`scripts/capture_pdf_grid_assets.py` preserves selected original physical grid cells as native text plus rendered visual assets. The original schema2 manifest is verified against the original SHA256, native word locations and an independently detected vector grid. Images, signatures and diagrams are retained rather than interpreted as empty text. Each PNG carries its SHA256, original source SHA256, original page, bounding box and rendering metadata.

```sh
python scripts/capture_pdf_grid_assets.py source.pdf reviewed-schema2.json --project-id PROJECT --document-id DOCUMENT --output-dir selected-grid-assets
```

Actual V4 run: pages10,78,86,99,106,171; six selected physical grids,102 source assets,15 cells containing source images. Every PNG hash and byte-identical rerender from the original PDF was independently checked. Source binding and asset identity: PASS. Interpretation: UNCERTAINTY. Page/document completeness: BLOCK. Native-only recovery still rejects image-containing cells. OCR, completeness and acceptance gates remain enforced.

Output paths must not overwrite the source PDF or input manifest. A regression checks a manifest whose filename collides with a generated PNG. Asset paths in capture.json are relative to its output directory.

## New source inspection

All eight uploaded files were opened and their SHA256 values rechecked without changing their bytes. See the accompanying JSON for exact identities.

| Sources | Confirmed | Limits |
|---|---|---|
| Таблицы.xlsx |25 rows,125 nonempty cells; all125 agree with DOCX load table after whitespace/decimal normalization|Agreement does not verify application of loads to a model|
| Coordinate XLSX |Four cached formulas independently recalculated with decimal arithmetic; no cell errors|Four numeric coordinates stored as text; units and reference frame unverified|
| Calculation DOCX |490 paragraphs,6 native tables,31 embedded images; explicitly names Naberezhnaya28A,Block1|Merged table cells retained; engineering/normative assertions remain source statements|
| Legacy calculation DOC |OLE opened; six validated main-text pieces,16010 characters decoded as UTF16LE|Formatting, fields, table geometry, embedded images and whole-document equivalence not verified|
| Two LIR models |Both binary headers identify LIRA-SAPR2013|No binary semantic parser or solver run; cannot claim loads, supports, units or results verified|
| Geodesy22pages and graphics21pages |43 original source pages rendered for contact-sheet inspection; vector drawings with almost no searchable text|Each dimension and annotation still requires source-bound region extraction and checking|

The PDF source pages have no exact decoded-image matches to V4; vector sources cannot be linked to V4 solely through an embedded-image digest. No automatic document/page equivalence is claimed.

DOCX contains a readable soil-table image with the same dimensions and near-identical displayed content as the raster on V4p171 (mean RGB absolute difference1.8185/255). This is a comparison candidate, not identity proof. Correctly rotated local OCR of the V4 raster gives234 blocks,110 below confidence0.9. All234 polygons have been remapped to original page coordinates. Numeric meanings and table structure remain unverified.

## Findings and remaining work

- Self-weight coefficient in table/XLSX is1; prose states1.1. WARNING until factor staging is checked in actual model.
- Displayed floor permanent load rows sum2.31/2.72 versus reported2.32/2.73. WARNING; independent rounding may explain the difference. Do not change source values or label the calculation erroneous without full precision inputs.
- Low-resolution ToR on V4p5–6 still needs a confirmed readable original or independently verified transcription.
- Selected-grid preservation does not establish completeness of534pages. Do not subtract recovered selected grids from the archived103 page-normalization blocks: these measurements have different scope.
- Model units, geometry, materials, supports, load combinations, solver logs/results and actual-structure comparison remain unverified. Presence of two LIR files does not satisfy semantic audit.
- FINAL AUDIT has not run; no ACCEPTED status or verified Evidence Register/Supabase entries are created.

## Validation

Fresh local Python suite:191 tests PASS. Browser syntax check PASS; four dashboard tests PASS. Runtime/engineering/e2e/scripts compilation PASS. The image-cell regression confirms source provenance, retained images, blocked native-only recovery, fabricated-text rejection, no completeness/acceptance and input-manifest overwrite protection.

Detailed read-only source analyses, OCR candidate polygons, contact sheet, original-cell PNGs and independently checked hashes are preserved in the object-source checkpoint. Original uploads and V4 are not duplicated in that checkpoint.

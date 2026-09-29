# V4 blocked-page visual sample

Source PDF SHA-256: `b5d95b660b35bfb6b2441623635cba91c235efd754bc283dfe1405f075834916`  
Source page count: 534  
Input: `v4-visual-sample.zip` manifest and 12 rendered page images, inspected 2026-09-29.  
Extraction review: `v4-extraction-review.json`, status `BLOCK`.

The observations below describe page layout. They do not validate extracted cells, engineering values, calculations, or conclusions. The extraction gate remains `BLOCK`.

| PDF page | Extractor reason | Visual observation | Review route |
| ---: | --- | --- | --- |
| 3 | `MERGED_TABLE_CELL` | Contents page with dotted leaders; small title block at the bottom. | Inspect the detected table region; keep contents and title block separate. |
| 8 | `MISSING_TABLE_CELLS` | Continuation of a document register table, signatures, and electronic signature stamp. | Verify the actual register rows against the image; treat signatures separately. |
| 30 | `DROPPED_TABLE_CELLS` | Engineering prose, photograph, and reinforcement drawings; no main rectangular data table. | Route to mixed text/figure review; inspect the region reported as a table. |
| 142 | `MERGED_TABLE_CELL` | Concrete strength measurements in a nine-column table with section headers and cells spanning measurement rows. | Verify each measurement row and its shared group values. |
| 148 | `MERGED_TABLE_CELL` | Continuation of concrete strength measurements, with shared values spanning rows. | Verify the continuation and shared group values. |
| 154 | `MERGED_TABLE_CELL` | Continuation of concrete strength measurements, with shared values spanning rows. | Verify the continuation and shared group values. |
| 176 | `MISSING_TABLE_CELLS` | Two load tables with totals and text between them. | Verify both tables independently, including their totals. |
| 264 | `MISSING_TABLE_CELLS` | Snow-load calculation text, equations, and schematic figures; no main rectangular data table. | Route to mixed text/figure review; inspect the detected table region. |
| 336 | `MISSING_TABLE_CELLS` | Calculation narrative and the beginning of a load table at page bottom. | Verify the table and its continuation on the next page. |
| 397 | `DROPPED_TABLE_CELLS` | Continuation of a reinforcement comparison table with coloured entries and a row continuing past the page edge. | Verify cells and adjacent page context; preserve coloured distinctions. |
| 486 | `MERGED_TABLE_CELL` | Registry extract with grouped headings, merged rows, and a QR code. | Verify registry fields against the image; do not treat QR code as a cell. |
| 500 | `MERGED_TABLE_CELL` | Drawing sheet with four plans and a legend; no main rectangular data table. | Route to drawing/legend review; inspect the detected table region. |

These routes are hypotheses from the 12-page sample, not labels for all blocked pages. A reason such as `MISSING_TABLE_CELLS` appears both on a genuine load table (176) and a schematic calculation page (264). Do not automatically downgrade `BLOCK` based on the reason code or visual layout alone. Any remediation must retain page identity, region provenance, extracted content checks, and the final audit gate.

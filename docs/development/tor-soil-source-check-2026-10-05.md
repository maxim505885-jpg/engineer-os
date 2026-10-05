# Original DOCX alternative source, ToR and soil-table checkpoint

Baseline: PR35, `974ced48d78010d3992dcfe6c1f6b1a5af1e379b`. This follow-up changes source-audit documentation; it does not change application acceptance behavior.

## Confirmed sources

The uploaded compressed V3 was materialized and inspected:38,043,877bytes,534pages,SHA256 `64a84bd83df1832fbdefd8c2e4aba0ce560b323d8dd472e2928d27af39991f1b`. Its ToR images have the same570x775/568x806 dimensions as V4, with different decoded pixel digests. It is not a higher-resolution ToR source.

The original full report DOCX was found in the existing source collection and opened:147,210,288bytes,SHA256 `b253439bdd673a775eaf209ca7d398d766efae5f4a18ac33fa6679f7faae28a5`. This is an original user-uploaded document, not the generated corrected report with a similar name.

Read-only main-document extraction retained15651 raw paragraph elements and12826 raw table-cell elements across118 tables.186 cells carry horizontal spans,6114 carry vertical merge markup. These counts include continuations and container text; they do not mean12826 distinct visible semantic cells. Each copied cell/text fragment has a main-document member locator, namespace-independent element path, fragment SHA256 and original document SHA256. A fresh parse independently checked locators and exact XML text copies. Declared row widths, including gridBefore/gridAfter and gridSpan, match all118 table grids.631 embedded image members have recorded dimensions and SHA256 values.

This is an alternative native source inventory, not normalized semantic tables, PDF pagination, whole-document completeness or evidence acceptance. Fields, drawing alternatives, hidden text, image interpretation and headers/footers are not fully audited. A namespace-dependent display XPath is informational; the independently verified locator is `source_element_path`. Original-tree element lookup and fresh-parse locator indexing produced byte-identical full extraction outputs. All142 selected soil/ToR crop hashes were subsequently checked.

## Selected PDF/Word agreement

V4p15 has the original8x3 climate table. All24 native PDF cell strings agree with original DOCX table1 after Unicode/whitespace normalization. Both original PDF cell bounding boxes and DOCX element paths are retained. This confirms the selected table text, not whole-file equivalence, climate-value correctness or normative applicability.

65 displayed numeric fields of the raster soil table on V4p171 were visually transcribed and compared with the original calculation DOCX `word/media/image1.png`.130 crops retain both reproductions. Every selected field retains raw comma decimals/parenthesized secondary displays, original PDF polygon, source/member SHA256 and column spans. No values were filled into empty regions, converted between units, or accepted as calculation inputs. The reproductions are copies of report data, not independent geotechnical measurements. Descriptions, classification references and other unlisted content remain outside this selected transcription.

## Controlling ToR scope

The original report embeds ToR as PNG images4 and5 (570x829 and568x806). Twelve readable controlling clauses were visually reviewed and retained with member hashes, crop coordinates and review PNGs. Most entries are explicit paraphrases; the selected sentence from clause10.1 is recorded verbatim:

> Конструкции основания и фундаментов не входят в объем работ.

This scope exclusion must be considered before demanding foundation investigation as a report-compliance condition. It does not itself verify calculation boundary conditions or authorize omission of checks needed for a requested model audit.

Other reviewed obligations include geometric measurements, material/defect checks, capacity calculations, photos/defect schedule, editable Word/CAD/Excel delivery, PDF delivery and instrument verification records. Complete ToR transcription, normative edition identifiers, model hyperlinks, contract details and electronic-signature authenticity remain unverified. Selected source reading PASS does not mean ToR compliance PASS.

## OCR execution limitation

Automatic approval review rejected the OCR task because the runtime attempted an unintended Microsoft telemetry connection whose external payload was not verified. The OCR task was not retried or bypassed. Local candidate output exists:248blocks,185 below confidence0.9, with substantial transcription errors. It is retained as rejected/unverified diagnostic material and is NOT_EVIDENCE. Selected review above uses visual source inspection and direct XML/native-PDF reading.

## Remaining gates

The selected p15 table agreement and p171 values address concrete extraction uncertainties. No counts are subtracted from the archived103 page-normalization blocks because scopes differ. Full534page completeness, remaining raster/graphic interpretation, complete controlling ToR, model/solver checks, normative applicability and FINAL AUDIT remain required. Document status is BLOCK; acceptance is not granted. No verified Evidence Register or Supabase write is made. Fresh local regression:191Python and4Node tests passed.

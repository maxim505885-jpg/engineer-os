# V4 page 488: manual source-image table recovery

Source PDF SHA-256: `b5d95b660b35bfb6b2441623635cba91c235efd754bc283dfe1405f075834916` (534 pages). PDF page 488 was rendered directly from this source at 170 dpi and compared with its embedded text layer. The extraction review lists page 488 under `MERGED_TABLE_CELL`. The text layer has the surrounding drawing stamp but almost none of the NOPRIZ extract in the page body. The body is raster content; text-layer extraction cannot recover its records.

The source image has a registry extract dated **06.08.2026**, number **6150032997-20260806-1802**, concerning **ООО «Строительно-производственное управление»** (ОГРН **1026102234509**). The following records were read directly from the rendered source page. The table has a merged section heading above records 1.1–1.8 and a second merged heading above a three-column 2.1–2.3 rights summary. These headings are not data cells to repeat in each row.

| Source item | Field / observed value | Verification scope |
| --- | --- | --- |
| 1.1 | ИНН: `6150032997` | Visually read in the first numbered row. |
| 1.2 | Full name: `Общество с ограниченной ответственностью «Строительно-производственное управление»` | Two-line value in the right cell. |
| 1.3 | Short name: `ООО «СПУ»` | Right cell. |
| 1.4 | Address: `346400, Россия, Ростовская область, г. Новочеркасск, ул. Крупской, д. 76` | Multi-line right cell; the left label also mentions actual place of business. |
| 1.5 | Member of association `Объединение проектировщиков Южного и Северо-Кавказского округов` (`СРО-П-033-30092009`) | Multi-line right cell. |
| 1.6 | Member registration number: `П-033-006150032997-0861` | Right cell. |
| 1.7 | Admission decision effective date: `11.07.2017` | Right cell. |
| 1.8 | Exclusion decision/date field is visually blank | Blank is an observed cell state, not an inferred assertion about current membership. |
| 2.1 | Right to perform design documentation work in the first listed category: `Да, 11.07.2017` | Bottom left column. |
| 2.2 | Right in the second listed category: `Да, 16.01.2023` | Bottom middle column. |
| 2.3 | Right for atomic-energy-use facilities: `Нет` | Bottom right column. |

The source image also shows a QR code, page number `1` for the embedded extract and a separate drawing sheet number `488`. The QR destination, registry currency/authenticity and every word of the legal scope headings have **not** been independently checked. The values above are page-image transcriptions, not confirmation from the live registry and not engineering conclusions. The page remains `BLOCK` in the extraction review; this record provides a verified recovery target for a future section-aware table representation. Do not reinterpret the merged headings as lost data or silently populate blank item 1.8.

## Continuation on PDF page 489

The next source image is the second page of the same NOPRIZ extract. Its two section headings span the table width. The body visibly contains these numbered values:

| Source item | Observed value |
| --- | --- |
| 3.1 | Second responsibility level, maximum 50 million rubles. |
| 3.2 | Suspension/termination field blank. |
| 4.1 | `26.07.2017` (date for the contractual-obligations compensation fund). |
| 4.2 | Second responsibility level, maximum 50 million rubles. |
| 4.3 | Additional contribution date `17.09.2025`. |
| 4.4 | Suspension/termination field blank. |

A visible electronic-signature mark and another QR code are outside the table. Their cryptographic validity and the QR destination have not been verified. Thus this continuation also remains `BLOCK` in the original review despite the manually transcribed cells.

## Drawing register on PDF page 490

This is a separate appendix (`Приложение Ж`, `Ведомость чертежей`), not another page of the NOPRIZ extract. The register has a merged descriptive category heading followed by **18 numbered drawing entries** and an empty `Примечание` column. The numbered figure identifiers run consecutively from `Ж.1` to `Ж.18`; row 9 describes the fifth-floor plan at `+18.000`, and beam/slab plans at `+21.800`. PDF page 500's title block independently identifies that drawing as `Ж.9` with the same levels. This cross-page match corrects an earlier reading of the small page-500 title as `X.9`. It verifies the index-to-sheet identity for this one drawing, not every mark or dimension on the drawing. Page 490 remains `BLOCK` until all 18 descriptions and their drawing links are checked.

## Drawing register continuation on PDF page 491

The source image continues the same three-column register with rows **19–43**, no numerical gaps, and an empty `Примечание` column. Rows 19–21 list sections; a merged heading introduces `Результаты геодезических измерений`; rows 22–34 list elevation isolines for the basement and successive floors, rows 35–40 plan surveys of load-bearing structures, and rows 41–43 lift-shaft surveys. Each numbered row shows the corresponding `Ж.19`–`Ж.43` identifier. This checks index sequence and broad content categories, but not the geometry or findings on the referenced drawings. The page remains `BLOCK` pending cell-by-cell verification and drawing links.

The source-image transcriptions for all numbered register entries 1–43 are recorded in [`v4_manual_evidence_488_491.json`](v4_manual_evidence_488_491.json). Its 76-item minimum region checklist currently has 74 recorded claims and two unrecorded QR payloads (pages 488 and 489). This count measures transcription coverage within the declared checklist, **not** source truth, QR authenticity, complete page coverage or readiness to accept a page. In particular, no drawing-to-register link other than `Ж.9` has been verified. Both register pages still require independent visual checking of the transcribed wording and the referenced drawings before their blocks can be reconsidered.

An independent pass over the PDF text layer found two transcription errors in the first manual version: row 6 uses `+17,340` and `+18,976` with decimal commas, and row 24 uses the ordinary hyphen-minus in `-0.200`. The source-bound data file has been corrected. The `v4_drawing_levels.py` check now confirms that all 43 figure identifiers appear and their decimal-level token sequences match the text layer exactly (`43` checked, `0` mismatches). It does not compare every word, prove that the text layer matches the rendered image in every region, or validate the drawings themselves; the original `BLOCK` remains.

The subsequent `v4_drawing_register_check.py` comparison uses independently detected PDF table cells and checks the **complete wording and punctuation** of all 43 numbered descriptions after removing whitespace introduced by line wrapping. It caught a further punctuation error in row 7 (commas had been transcribed as semicolons), now corrected. Current result: `43` rows checked, `0` mismatches. The source image, text layer and independent table-cell extraction thus agree for the numbered register descriptions; the check does not verify all referenced drawing sheets or the legal/electronic-signature content on pages 488–489. The extraction review still reports `BLOCK` for pages 490–491 until a source-bound section-aware representation and page-level coverage gate are integrated.

# Native Word table grid — 2026-10-09

The full available147MB report contains118tables and12826native XML cells. Earlier extraction preserved6300merge declarations but exposed XML cell ordinals only. The new source_grid locator preserves ordinal coordinates and adds declared grid-column intervals plus exact vertical restart anchors. No cell values are inherited or propagated; no rendering, formula evaluation or engineering acceptance is granted.

The resolver reads tblGrid, gridSpan, gridBefore/gridAfter and vMerge. Omitted vMerge val means continue; a continuation requires the exact same grid interval in the immediately preceding valid row. Plain or empty rows interrupt continuity. Numeric parsing and grid width are bounded at1024columns; duplicate/missing/unsupported declarations, legacy hMerge, width conflicts, structural wrappers and tracked table/row/cell grid revisions remain unresolved. Bookmarks are transparent annotations. Original MERGED_CELL_UNVERIFIED warnings remain; consistent native structure does not establish displayed layout.

Initial native source read mapped all12826cells consistently and5759vertical continuations. All118source tblGrid declarations and6300merge declarations remain source data; the complete actual Store extraction and final CI receipts are recorded separately after finishing. Physical pages and qualified ground truth remain unverified.

Seven behavioral regressions reproduced missing locators and false consistent states before the corresponding fixes. Independent review identified skipped wrapped rows and ignored tracked properties; both fixed RED→GREEN, with no remaining Critical/Important findings. Existing Office behavior, exact originals and fail-closed acceptance are retained. The implementation hash and1024column bound are part of parser identity; previous Office jobs require fresh checkpoints.

Semantics grounded in Microsoft Open XML documentation:
- https://learn.microsoft.com/en-us/dotnet/api/documentformat.openxml.wordprocessing.verticalmerge?view=openxml-3.0.1
- https://learn.microsoft.com/en-us/dotnet/api/documentformat.openxml.wordprocessing.verticalmerge.val?view=openxml-3.0.1
- https://learn.microsoft.com/en-us/dotnet/api/documentformat.openxml.wordprocessing.gridbefore?view=openxml-3.0.1
- https://learn.microsoft.com/en-us/dotnet/api/documentformat.openxml.wordprocessing.gridafter?view=openxml-3.0.1

This implements native source topology only. Plan13/document completeness, qualified rendered tables/formulas/graphics, normative calculation/positive FINAL AUDIT, accepted memory/report, CAD/provider receipts, physical Windows and release remain open in their stated scope. Overall plan8complete/8partial/3open.


## 74.1. Итог — native Word grid и вертикальные объединения

[PR 98](https://github.com/maxim505885-jpg/engineer-os/pull/98) объединён в `integration/release-candidate-v1`: `9a92b96ec892d8e7bdf54a95d0875afbcf4b78b5`. Дерево `2c36ea304797f56e69562d1673f3ee018d364bbe` точно совпало с проверенным head `d6bb3976d0513828a2cf3b8517cc7fbe7ac7d23e` и локальным кодом. Все девять CI завершились SUCCESS; Linux 770 тестов (768 PASS, 2 Windows-only skips), 7 Node, 2 HTTP/DOM и 4 Chromium; Windows 23 теста, clean start/cache repair/restart, реальный Ollama qwen3:0.6b и 4 Chromium PASS. Независимое ревью: оставшихся Critical/Important нет.

Полный неизменённый DOCX 147 210 288 байт обработан штатным Store за 364.564 секунды: 14 678/14 678 единиц, 0 failed/truncated, 1 095 842 сохранённых символа. Во всех 118 таблицах независимый разбор XML оригинала подтвердил записанные интервалы 12 826 ячеек и 5 759 продолжений вертикальных объединений. SHA256 источника `b253439bdd673a775eaf209ca7d398d766efae5f4a18ac33fa6679f7faae28a5`.

Native координаты сохранены отдельно от XML ordinal; значения между объединёнными ячейками не переносятся. Неопределённые структуры, скрытые wrappers и tracked changes сохраняют запреты. Это доказательство структуры источника: rendered layout, смысл формул и инженерная приёмка не подтверждены. 7 022 единицы остаются BLOCK; acceptance=false. Физический Windows NOT_VERIFIED.

План: 8 готово / 8 частично / 3 открыто. №13 остаётся открыт: rendered tables/merged cells/formulas, графика и легенды, числовые OCR-конфликты, полный V4 PDF и квалифицированный эталон. Затем восемь семантических расчётных ролей, нормы/solver-run/actual correlation, положительный FINAL AUDIT и ACCEPTED→memory/report; CAD equivalence/roundtrip, live provider receipts; физический Windows и выпуск. Подробные receipts: `docs/qa/2026-10-09-word-table-grid-ci.json` и `docs/qa/2026-10-09-word-table-grid.md`.

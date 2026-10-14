# Selected region OCR — 2026-10-09

Scope: point 13, bounded recovery of small numeric labels. Not complete-document verification or accepted engineering evidence.

The original regional run read a dimension as `82406`; visual spot review showed `82400`. Whole-page OCR missed it. A selected crop `[760, 795, 950, 830]` on page 1 of source SHA256 `6092ab2298bf328a545379a850b0a740cc40f3c5592703fbf876c32f459913ce` now yields `82400` with original page coordinates. This is one assistant-reviewed spot, not qualified ground truth for the entire corpus. The older contradictory candidate is preserved.

Use `python -m scripts.local_ocr_region SOURCE --page N --bbox L T R B --sha256 EXPECTED --output NEW_JSON`. Points are unrotated and relative to the crop. Selected execution uses one pass, PSM 6 and scale up to 6, constrained by existing pixel, byte, word and deadline limits. Defaults retain whole-page/regional behavior. Output records settings, source SHA256 and boxes; flags for quality, full-page/document completeness and acceptance remain false.

The diagnostic probe initially produced empty TSV rows because this local model directory lacks Tesseract's named `tsv` configuration. Retrying with `-c tessedit_create_tsv=1` established the result; production already used this setting.

Tests were added before implementation: selected-region cases initially failed with missing API; CLI case failed with missing module. Passing checks cover cropped/rotated source coordinates, invalid selections, interrupted execution, original SHA guard, independent live numeric fixture, and refusal of existing source/symlink/hardlink output aliases. Review found inaccurate selected engine settings; these are now recorded explicitly in identity and per-pass dossier.

Pre-final suite: 745 tests, 743 passed, 2 native Windows-only skips. Additional live-numeric and CLI-alias tests passed; final complete suite and remote CI must be recorded separately before integration.

Real selected pass: 239400 pixels, 354 output bytes, 3 words, 1/1 completed pass. The source hash remained unchanged. The source still emits MuPDF xref warnings. Tables, formulas, merged cells, all drawing labels and full corpus completeness remain unverified. Project readiness stays 8 done / 8 partial / 3 open.

## 71.1. Итог выбранного OCR-фрагмента: PR 95 принят

Все 9 checks на `6b7674bc57ce62f8abac2cd702720e7c7c1d6488` SUCCESS. Кандидат `c4e1181a5f7463a03ec2fce279aab6641e420e61`, дерево `e404c539dcd28394980b937b5eb1fb0a9a676f9a` равно проверенному опубликованному и локальному `4e4ce1b`. Linux PR/push: 747 тестов / 745 PASS / 2 native Windows skips, 4 Node, 2 HTTP/DOM и 4 фактических Chromium сценария PASS. Windows: 23 теста, startup/cache/restart, реальный qwen3:0.6b через UI и все 4 Chromium PASS. Physical Windows по-прежнему NOT_VERIFIED.

Дополнительная выбранная сверка трёх исходных областей: размер 82400 и отметка -4.200 совпали; номер листа 513 не прочитан корректно (whole-page ранее прочитал его). Итого 2 MATCH / 1 MISMATCH, assistant spot review без qualified ground truth. Новый CLI — дополнительный проверяемый кандидат; он не заменяет прежнее извлечение и не подтверждает полноту. Оригиналы неизменны, старые противоречивые кандидаты сохранены.

Готовность 8✅ / 8🟡 / 3❌. Из 5 критериев закрыт программный CodeQL/единый кандидат; остальные частичны. Следующий шаг №13: эталонное покрытие чисел/таблиц/формул/графики полного V4, с фиксацией пропусков и конфликтов; после него реальные нормы/расчёты/FINAL AUDIT и остальные product gates. Полные CI receipts: docs/qa/2026-10-09-selected-region-ocr-ci.json.

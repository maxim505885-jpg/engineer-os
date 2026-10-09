# Передача состояния ENGINEER OS

Итог карты §73.1: PR 91–97 приняты в integration/release-candidate-v1, `f83c4d5fbaac8e602757ca6fac1646b86589cdff`. Дерево `2af4da649a69d4f60c7c51ffd7331af1ea6ccb80` равно проверенному `187b6d88448806f31781df7cf68f6bd6bf826b22` и локальному `9aa29f7724905137bb6c816a59101ef060a4cc57`. Main/release/tag остаются отдельными критериями.

Все 9 CI checks SUCCESS. Linux PR/push: 763 теста (761 PASS, 2 native Windows skips), 7 Node, 2 HTTP/DOM, 4 Chromium. Windows: 23 теста, clean start/cache repair/restart, настоящий Qwen qwen3:0.6b и 4 Chromium PASS. Физический Windows NOT_VERIFIED.

Полный доступный DOCX 147210288 байт: 14678/14678 logical units, failed/truncated 0, 1095842 chars, 7022 BLOCK. SHA b253439bdd673a775eaf209ca7d398d766efae5f4a18ac33fa6679f7faae28a5. Source XML 41 equations/6300 merge declarations/655 drawing elements/642 media members. Буквальные токены уравнений совпали; rendering/semantics/document completeness не подтверждены. Physical pages unknown. Оригинал неизменён; все 3 source-review решения на настоящем большом исходнике прошли без acceptance. Прежние Office665/OCR43 результаты сохранены как история; новый parser требует новых Office checkpoints.

Исправлены bounded large-office upload/XML paths, streaming source review, per-unit source hashing, обе stale-session races и fixture shutdown/cleanup. Начальные Linux DOM и Windows cleanup failures сохранены в receipts, воспроизведены и исправлены; финальные checks прошли после изменений, не простого rerun.

План 8 готово / 8 частично / 3 открыто (13,14,19). Далее №13: rendered tables/merged cells/formulas, вся графика, числовые OCR-конфликты, полный V4 PDF и qualified ground truth. Затем 8 semantic calculation roles, нормы/solver-run/actual correlation/FINAL AUDIT, ACCEPTED→memory/report, CAD equivalence/roundtrip, live provider receipts. Физический Windows и release последними. Детали docs/qa/2026-10-09-large-office-input.md и large-office-input-ci.json.

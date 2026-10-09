# Передача состояния ENGINEER OS

Итог карты §70.1: PR 91/92/93/94 приняты в integration/release-candidate-v1, `cca057f6fdd2e1f3751485727543d15b33e1879a`. Дерево `2ae639262b28d21707d3f8f628d49fd2370c9e91` равно проверенному опубликованному `6db015bb9ad5c38a5143f747f2508eabc5fe97eb` и локальному `2114726136e2f43db5a6eff767bec84b057e5ecf`. Main/release/tag отдельно.

Все 9 проверок CI SUCCESS. Linux PR/push: 741 тест (739 PASS, 2 Windows-only skips), 4 Node, 2 HTTP/DOM, 4 Chromium. Windows PR: 23 теста, реальный Ollama qwen3:0.6b, 4 Chromium и startup/cache/restart PASS. Физический Windows-ПК не проверен.

Optional ENGINEER_OS_OCR_LAYOUT=regions: целая страница + 4 перекрывающиеся области, исходные координаты и общие бюджеты. Альтернативы явно маркируются для модели; режим входит в parser identity. Два Important ревью исправлены RED→GREEN; minor про отдельный failed descriptor отложен, INCOMPLETE видим. 35 focused tests PASS.

Реальный финальный OCR 43/43 страниц / 215 проходов: 0 failed, 0 text truncation, оригиналы неизменны, координаты в пределах страниц. Максимум 32 080 286 пикселей / 326 472 TSV bytes / 2 432 слова. Все страницы BLOCK/UNVERIFIED. Визуальная сверка трёх чисел: 2 совпадения / 1 ошибка; полный эталон отсутствует и xref warnings сохраняются.

Единый план: 8 готовы в программном объёме, 8 частично, 3 открыты (13,14,19). Следующий №13 — числовые подписи/таблицы/формулы по эталону, графика и весь V4. Затем актуальные нормы/семантические расчёты/положительный FINAL AUDIT, принятая память/отчёт, CAD equivalence/roundtrip и optional-provider receipts. Физическая Windows/выпуск последними. Подробности: docs/qa/2026-10-09-regional-ocr.md, regional-ocr-ci.json, живая карта §70.1.

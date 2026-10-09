# Передача состояния ENGINEER OS

Итог карты §71.1: PR91/92/93/94/95 приняты в integration/release-candidate-v1, c4e1181a5f7463a03ec2fce279aab6641e420e61. Дерево e404c539dcd28394980b937b5eb1fb0a9a676f9a равно проверенному опубликованному 6b7674bc57ce62f8abac2cd702720e7c7c1d6488 и локальному 4e4ce1b. Main/release/tag отдельно.

Все9CI SUCCESS. Linux PR/push747 тестов (745PASS/2Windows skips),4Node,2HTTP/DOM,4Chromium. Windows23теста,startup/cache/restart,реальный Ollamaqwen3:0.6b и все4Chromium PASS. Physical Windows NOT_VERIFIED.

Optional regionsOCR: весь лист +4перекрывающиеся области, общие budgets и unverified alternatives. Реальный43/43страниц/215проходов,0failed/truncation,оригиналы неизменны,всеBLOCK. Новый SHA-guarded CLI python -m scripts.local_ocr_region: выбранный фрагмент PSM6/scale≤6, исходные координаты/настройки/лимиты, exclusive output; не подтверждает полноту/приёмку. Выбранный размер82400 восстановлен, но сверка3областей дала2MATCH/1MISMATCH (номер листа513 неверен; whole-page ранее верен). Xref warnings и отсутствие qualified ground truth сохраняются.

План8готово/8частично/3открыто(13,14,19). Далее №13: полное эталонное покрытие чисел/таблиц/формул/графики V4 с фиксацией пропусков/конфликтов. Затем8semantic calculation roles,действующие нормы/solverrun/actual correlation и положительный FINAL AUDIT,принятая память/отчёт,CAD geometry equivalence/roundtrip,providerreceipts. Physical Windows и выпуск последними. Детали: docs/qa/2026-10-09-selected-region-ocr.md,selected-region-ocr-ci.json, карта §71.1.

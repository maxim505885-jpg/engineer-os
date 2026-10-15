# Актуальное состояние — восемь направлений, 15.10.2026

PR152 объединён в candidate `e27cf79582e929421685169304ac873d20a3df3a`.
Новый программный пакет — PR153 / `codex/eight-point-completion-20261015`.
Сначала читать [сверенную матрицу восьми направлений](../qa/2026-10-15-eight-direction-completion.md).
1161tests OK (55skips),7Chromium PASS,guards PASS.29текущих источников сохранены;
встроенное ТЗ найдено;9LIR/279таблиц проверены,90запросов результатов UNAVAILABLE.
Полнота документов/нормы/реальный ACCEPTED/полный CAD/physical release остаются
BLOCK. Новые кодовые проверки не закрывают эти инженерные критерии.
Exact-head CI/merge нового пакета сверять по PR153; предшествующий CI не подменяет новый.

Исторические записи ниже сохранены и не являются текущей сводкой.

# Текущий результат — 15.10.2026, MASTER audit / optional engineering adapters

База GitHub `integration/release-candidate-v1` подтверждена через Git refs API:
`db29e4c946e4db5e088e8fdd727c6165365dcc4d`; Core1022/Windows222/Security845 success
относятся к базе. Ветка текущего пакета: `codex/master-engineering-audit-20261015`.
Исходный `C:/Users/maxim/engineer-os` содержит чужие staged/untracked изменения;
не переносить их, не менять его ветку. Пакет находится в managed worktree.

Читать сначала [матрицу19 и QA](../qa/2026-10-15-master-engineering-audit.md),
[план](master-engineering-pass-20261015.md), затем карту. Исправлены потерянные
Docling limitations, worker-thread table-loss и source mutation checks.
Реальная V4 page57 обработана offline существующим Docling:23 блока сохранены,
BLOCK TABLE_CAPTION_WITHOUT_VERIFIED_ROWS, source unchanged; private artifacts
в `.engineer-os/master-pass/` текущего managed worktree. Полный rerun не выполнен.
Optional IFC/DXF/Pynite CLI проверен на синтетических эталонах. Новые adapters
не подключены автоматически к UI/Evidence/acceptance. №13/14/19 остаются BLOCK.

Chromium7/7 PASS; pinned full suite1085:0failures/7errors/47skips (6symlink privilege,
1 transient app.lock cleanup; restart separately PASS). Целевые tests и повтор
независимого review PASS. Прямой Git network недоступен; GitHub connector работает.
В новом чате проверить PR/head/CI пакета; не выдавать проверки базы за новые.

Следующий предметный шаг: найти актуальный приватный v12 corpus, пересчитать
source-bound output с новой parser identity, сверить таблицы/формулы/числа с
оригиналом. Старый доступный review137 BLOCK отличается от documented v12
52BLOCK/55UNCERTAINTY; наборы не смешивать. Никаких 100%/ACCEPTED/release claims.

## Историческая передача — §92 / PR108

# Передача состояния ENGINEER OS

Активная задача: выполнение пяти критериев, раздел68 живой карты. Единый план содержит19 пунктов:8✅/8🟡/3❌.

PR91 merged вintegration/release-candidate-v1,head22ad4c153646a9a2a2c5c17cc3a582afdd1e4130;tree2670623 совпадает с проверенным90263af.29 CodeQL alerts reviewed individually/dismissed false positive;aggregateSUCCESS. Пункт1 пяти критериев выполнен. Main/final release не перенесены.

Проверены7 реальных источников:43PDF pages и660Office units,ошибок0,байты оригиналов сохранены. Графика,формулы ичасть таблиц остаются NOT_CHECKED;native LIR не заменяетsolver export. Intake BLOCK:8 отсутствующих ролей. Реального accepted case иоригинального DXF/DWG нет.

PR92/head e4eaf3509e953118e5e3ed8c979d5ea28bad121f:Windows clean start/cache repair/restart прошли первый запуск;Windows backup tests нашли byte-lock read иtest SQLite handles. Причины исправлены,18local testsPASS;повтор полногоWindows CI выполняется. Не считать физическийПК/перезагрузку подтверждёнными.

726Python,4Node,2HTTP/DOM,4Chromium былиPASS на исходном frozen tree;послеWindows исправления идёт новый full Python pass. Последний фактический результат проверять поCI иразделу68.

## Уточнение §68.5

DWG действительно сохранён среди исходников. Пять копий byte-identical, 1 уникальный AC1032. GNU LibreDWG0.14 создал отдельный DXF: 15 906 объектов, 287 блоков, 32 слоя. CAD_ENTITY_LIMIT и предупреждения/ошибки конвертации сохраняют BLOCK; original geometry equivalence NOT_VERIFIED. Это заменяет прежнюю формулировку «DWG отсутствует».

PR92 head6032367 исправляет DOM teardown race и канонизацию путей в Windows assertion. Локальный DOM дважды PASS exit0. Последний предшествующий native Windows: 23 tests + реальный Ollama qwen3:0.6b inference PASS; полный новый CI ещё выполняется. Программный результат не закрывает физическую перезагрузку, полноту инженерных источников и положительный FINAL_AUDIT.

## P0 промежуточный результат — 10.10.2026, PR109 (не объединён)

В ветке docs/coverage-stage13-handoff-20261010 введён явный переход оставшихся после остановки модели receipts из RUNNING в INTERRUPTED перед resume. Незавершённая попытка сохраняется в SQLite и учитывается в attempt/elapsed accounting, но не выдаётся за COMPLETED или reusable result. Изменены engineering/local_app/store.py и engineering/local_app/automatic_analysis.py, добавлен tests/test_analysis_receipt_recovery.py (2 регрессионных сценария); создан исполнимый план docs/development/implementation-plan-20261010.md. Опубликованный head cafeafd85b70f554896893ce9eba488807d1fbb0. Security guard CI success; Windows/Core CI на момент записи in_progress, PASS ещё НЕ заявляется. Локальное выполнение полного suite/реальный повтор большого DOCX ещё НЕ выполнялись; причина расхождения 1496 model calls / 1492 persisted receipts не установлена. №13 открыт; ENGINEER ACCEPTED не заявлен. Кандидат остаётся e0754b2; новая работа ещё не объединена.

# MASTER PLAN — ENGINEER OS

## Актуализация №15 — 15.10.2026, после merge PR150 и полного corpus rerun

Текущий официальный candidate: `integration/release-candidate-v1` `db29e4c946e4db5e088e8fdd727c6165365dcc4d`; PR150 слит. На merged commit PASS три GitHub workflows: [Core Tests](https://github.com/maxim505885-jpg/engineer-os/actions/runs/38593047699), [Windows local runtime](https://github.com/maxim505885-jpg/engineer-os/actions/runs/38593047938), [Repository Security Guard](https://github.com/maxim505885-jpg/engineer-os/actions/runs/38593047825). PR150 добавил ограниченный vector locator и fail-closed сохранение source-located текста при неразобранных таблицах.

- №13: полный local Docling v12 rerun V4 завершён по 534/534 страницам, 107 JSON output, 31 268 source-located blocks. Аудиты для всех чанков совпали с project/document identity и исходной контрольной суммой. Итог 52 `BLOCK`, 55 `UNCERTAINTY`, 31 table-loss warning, 19 outputs `TABLE_CELLS_DROPPED_BY_LAYOUT_PARSER`, 52 `TABLE_STRUCTURE_UNVERIFIED`, один `TABLE_CAPTION_WITHOUT_VERIFIED_ROWS`; все outputs сохраняют `acceptance=false`.
- Независимое сравнение нативного PDF-текста: 494 страницы имели минимум 10 source-native tokens, 352 достигли 90% recall уникальных токенов, взвешенный recall 74,8%. Это диагностика текста, не доказательство полноты OCR, изображений, порядка чтения, символов/размеров, таблиц или смысла. Визуальная проверка страницы5 подтвердила искажённую строку и отсутствие структуры видимой таблицы. Все 534 страницы требуют дальнейшей визуальной/семантической проверки; №13 остаётся BLOCK.
- DOCX: hash/size соответствуют приватному intake manifest. Stage7 обработал 553/553 logical units, 112 BLOCK; auxiliary image/layout placement не подтверждено. OOXML census обработал 12 XML частей, нашёл 49 media entries и расхождения lexical token set (113 уникальных токенов source `document.xml` не представлены в текущем извлечении). Это сигнал для reconciliation, не точный список потерь; merged table cells и presentation не проверялись. Word completeness остаётся BLOCK.
- №14: свежий Stage7/Stage8 run4 по одному реальному объекту завершился `BLOCK/BLOCK`, `ACCEPTED=false`; нет formal requirements/evidence set, успешных specialist findings и закрытых engineering gates. Частный source manifest и идентифицирующие сведения не публиковались.
- Локальный запуск 26 memory tests дал 24 PASS; backup/restore сценарий остановился на Windows ACL `PermissionError` при создании подкаталога под staging-папкой с mode 0700. Это ограничение локального окружения, не подтверждённый дефект приложения; на официальном candidate Core Tests и Windows local runtime CI зелёные.
- №6: нормативные и предметные gates открыты; реальные LIRA/SCAD расчёты по решению пользователя отложены. №15/16: software pathways проверяются на controlled fixtures, реальный ACCEPTED→knowledge/report flow невозможен до qualified case. №17: DWG→DXF inventory частично доступен, `CAD_ENTITY_LIMIT` и converter warnings оставляют геометрическую equivalence/roundtrip BLOCK. №18: optional-provider receipts и свежий live specialist execution не подтверждены. №9 физическая установка/перезагрузка не пройдена. №19 release audit не пройден.

Порядок: (1) исправлять воспроизведённые потери PDF/Word и сверить независимый mixed/raster corpus, сохраняя BLOCK до полного review; (2) закрыть доступные нормативные gates №6, не запуская отложенные расчёты; (3) получить актуальные ТЗ/требования/evidence и успешно провести specialist review для свежих Stage7/8 №14; (4) выполнить qualified real-case сценарии №15/16, DWG roundtrip №17 и локальный/provider receipts №18; (5) физический Windows №9; (6) полный release audit №19. Точные hashes, путь к user files и identifiers сохранены только локально. Подробное состояние — `ENGINEER_OS_PROJECT_MAP.md` §67.


## Актуализация №13 — 10.10.2026, после §92 / PR108

Источник истины по новейшему состоянию: `ENGINEER_OS_PROJECT_MAP.md` §92 и `docs/development/project-map-handoff.md`, ветка `docs/project-map-handoff-20261005`. Исторические показатели PR91–92 в начале этого плана не следует принимать за текущий candidate.

- PR108 объединён: `integration/release-candidate-v1` candidate `e0754b2a3dcfb24a55e68af9333ec9d35a67618f`; Core/Windows/Security CI успешны согласно §92.
- Реальный DOCX: native reader 14684/14684 logical units; Store/Worker/controlled-model после resume 14684/14684, 749/749 batches, 0 text truncated; исходник неизменён. Это не подтверждение визуального покрытия или реального пользовательского inference.
- Реальный V4: source-bound PNG journal 534/534; для 40 страниц без native text записаны OCR candidates; их содержание и ячеечная структура не квалифицированы.
- **Неурегулированная целостность receipts:** повторная проверка SQLite показала 1492 записей (1491 COMPLETED и 1 RUNNING) и 1496 model calls, несмотря на SUCCEEDED. До сверки всех вызовов и receipts и установления причины оставшаяся RUNNING запись не должна трактоваться как завершённая; не объявлять журнал полным.
- **Следующее предметное действие:** на сохранённом реальном Store связать receipt_id / вызовы модели / batch index / restart state и объяснить аномалию; затем на репрезентативных original Word+V4 source-bound местах сравнить raster/mixed таблицы по ячейкам, EMF/PNG подписи и 41 OMML с визуальным источником. Исправлять только воспроизведённую потерю/ложное подтверждение. Проверить OCR-conflicts и независимый корпус. Не изменять оригиналы.
- Принятие №13 требует не только 534 страниц или 14684 units, но и подтверждённого визуального соответствия и полноты источников; пока **❌**. №14 и №19 также **❌**. Общий баланс 8✅/8🟡/3❌. ЛИРА/RES/расчёты отложены по решению пользователя; установка на его ПК не выполнялась.


Единая нумерация: **19 пунктов**. Эта сводка заменяет противоречащие текущие статусы планов17/19; история сохранена в `master-plan-17-history.md`, `master-plan-19-history.md` и живой карте. Результат нельзя переносить между планами по номеру без названия и критерия.

**Активный план:** §68 — выполнение пяти оставшихся направлений. Критерий1 завершён:29 CodeQL alerts reviewed/dismissed FP,0open на refs/pull/91/head,check113609776255SUCCESS; PR91 merged. Официальный candidate22ad4c153646a9a2a2c5c17cc3a582afdd1e4130/tree2670623 равен проверенному90263af. Проверены7 реальных оригиналов:43/43 PDF страницы и660/660 Office units без ошибок;графика/формулы/табличная семантика остаются непроверенными. Расчётный intake BLOCK,8 roles отсутствуют;Положительный accepted case не подтверждён. Реальный DWG найден и отдельно преобразован; геометрия не принята. PR92 проверяетWindows clean startup/cache repair/restart/backup/browser/liveOllama;physicalWindows иинженерная приёмка не подтверждены. Исторические §§65–67 сохраняют состояние до triage/merge.

| № | Этап | Статус | Проверенный результат и оставшийся критерий |
|---|---|---|---|
| 1 | Единая рабочая версия | ✅ Кандидат | PR91 перенесён в официальный кандидат22ad4c1; tree2670623 совпадает с проверенным90263af. Финальный main/release отдельно. |
| 2 | Качество OCR и локальной модели | ✅ программный контур | Извлечение/метрики/отрицательные gates и живой Linux qwen3 проверялись. Это не полнота V4 и не Windows. |
| 3 | Большие документы: resume/recovery | ✅ программный контур | Checkpoints, identity, budgets, retry. Полнота инженерного документа отдельно в№13. |
| 4 | DOCX/XLSX/DOC и остальные заявленные форматы | ✅ программный контур | Оригиналы, logical locators, provenance, native/OCR маршруты; сложные таблицы отдельно. |
| 5 | ТЗ → источник → требование → вывод | ✅ программный контур | Полный индекс47 требований,42 исходные позиции, версионные оценки и глобальные gates. |
| 6 | Нормативная и расчётная верификация | 🟡 | 12 документальных нормативных решений BLOCK; native LIR identity/receipt integrity готовы. Семантический vendor export/run, полномочия и actual correlation открыты; расчёт отложен пользователем. |
| 7 | Реальный инженерный case workflow | ✅ отрицательный сценарий | Три оригинала,36 кандидатов, роли и нормативный replay воспроизводимы; объект не ACCEPTED. Положительный сценарий в№14. |
| 8 | FINAL AUDIT / acceptance boundary | ✅ программный контур | Immutable/stale/tamper/foreign source gates. Нет подтверждённого положительного инженерного объекта. |
| 9 | Windows one-click runtime | 🟡 | Native Windows CI: cold start/cache repair/restart,23 regression tests и live Ollama inference PASS. Полный browser CI повторяется; physical PC clean install/reboot открыт. |
| 10 | Консолидация и источник истины | ✅ Интеграция | PR91 merged squash по правилам репозитория; общий код официального кандидата22ad4c1. История исходного объединения сохранена на integration/engineering-streams-20261009. |
| 11 | Интерфейс и пользовательский маршрут | 🟡 интеграция | Дизайн кандидата сохранён вместе с формами источников/ТЗ/ролей/черновиков. Все4 browser маршрута, включая CAD/memory/mobile/session reset, прошли. Финальная приёмка интерфейса на реальном accepted объекте остаётся. |
| 12 | Backup/restore/recovery/security | 🟡 интеграция | Один bounded engine, чтение двух форматов, SHA256/SQLite/no-replace/key/derived/settings. Совместимость двух форматов проверена; воспроизведённые symlink/hardlink внутреннего DB/lock/settings/key устранены. Core/Security CI PASS; CodeQL29 alerts individually reviewed/dismissed FP,checkSUCCESS; физический Windows NOT_RUN. |
| 13 | Production completeness документов | ❌ полностью не закрыто | Автоматические native/OCR/Office routes есть; на реальной копии V4 обработаны534/534 native-страницы с явными ограничениями (все BLOCK). Сложные mixed/raster tables/графика, полный проверенный V4 и представительный completeness corpus открыты. |
| 14 | Реальный принятый инженерный кейс | ❌ | 2026-10-14: свежий Stage7/8 run на одном предоставленном реальном объекте по ограниченной трассировке дефекта завершён BLOCK/BLOCK, ACCEPTED=false. Локальная запись содержит входные hashes и подробности; пользовательские данные не добавлялись в публичный репозиторий. №6/13, формальное ТЗ, требования/evidence, DOCX/PDF completeness и успешный specialist run остаются блокерами. |
| 15 | Подтверждённая инженерная память | 🟡 программный маршрут | Версионное знание только из актуального принятого audit; scope/recall/revoke/delete/export/backup, повторная проверка обязательна. Реальный положительный ACCEPTED→memory сценарий ещё не выполнен. |
| 16 | Генератор отчётов | 🟡 | Редактируемый черновик, история, источники/координаты, dossier покрытия/stale guards,3 шаблона и источник-связанные иллюстрации DOCX/PDF реализованы. Общая проверка726/Node/DOM/Chromium и визуальная проверка DOCX/PDF PASS; выпуск принятого документа остаётся открыт. |
| 17 | CAD/DWG | 🟡 DXF программный маршрут | Импорт DXF/DWG сохраняет оригинал; DXF inventory/locator/отдельная аннотация/diff/export/backup с единицами и проверкой ресурсов. Реальный DWG найден: отдельная конвертация GNU LibreDWG 0.14, 15 906 объектов. CAD_ENTITY_LIMIT и предупреждения конвертации блокируют controlled edit; эквивалентность геометрии и roundtrip открыты. |
| 18 | Multi-AI connector | 🟡 локальная часть | Бесплатные Ollama/Open WebUI, настройки и isolated diagnostic готовы. Shared gateway защищён от ложных hostname/redirect/незавершённых/слишком больших ответов. Единый optional-provider receipt/gate сценарий полностью не проверен. |
| 19 | Финальный стабильный выпуск | ❌ | Требуются все продуктовые критерии, clean install, physical Windows, accepted case, release/tag и соответствующий main. |

✅ относится только к указанному критерию и набору данных. Программный PASS не означает ACCEPTED объекта. BLOCK означает отсутствие проверенного основания, а не установленный дефект конструкции. Тестовый model protocol/replay не выдаётся за новый живой inference/solver/expert review.

## Соответствие прежнему плану17

| Прежний17 | Единый19 | Название |
|---|---|---|
| 1 | 1/10 | Единая версия |
| 2 | 8 | Границы доверия |
| 3 | 12 | Backup/restore |
| 4 | 11 | Кабинет |
| 5 | 18 локальная часть | Модель/задачи |
| 6 | 4/13 | Форматы/полнота |
| 7 | 5/7 | ТЗ/ядро |
| 8 | 6 нормы | Нормативы |
| 9 | 6 расчёт | Solver, отложено |
| 10 | 16 | Черновики заключений |
| 11 | 17 | CAD |
| 12 | 14 | Принятый кейс |
| 13 | 15 | Память |
| 14 | 11 | Финальный UI |
| 15 | 12 | Надёжность |
| 16 | 9 | Windows, отложено |
| 17 | 19 | Release |

## Порядок дальнейшей работы

1. №1/10 выполнены:triage29 и PR91→candidate завершены. №12:Windows ACL иконкурентная подмена вне owner-controlled contract не подтверждены.
2. №13: independently verified полнота сложных mixed/raster таблиц/графики полного V4 и представительный корпус.534/534 обработанных страниц V4 остаются BLOCK.
3. №6/14: применимые свежие нормы,qualified actual evidence и vendor export/run/correlation, затем реальный положительный FINAL AUDIT. Расчёт ранее отложен пользователем.
4. №15/16/17: реальный ACCEPTED→knowledge маршрут,принятый документ,реальный CAD и DWG converter/roundtrip. Программные память/шаблоны/иллюстрации/DXF-аннотации уже реализованы и проверены.
5. №18: optional-provider live/receipt contract. Бесплатные локальные провайдеры не требуют облачного API.
6. №9/19: physical Windows cold-start/restart/reboot/end-to-end и clean install последними; затем FINAL RELEASE AUDIT,main/tag. Физический Windows ранее отложен.

Не снимать реальный BLOCK ради номера пункта. Финальный релиз не объявлять по числу тестов. Карту обновлять после каждого существенного результата с branch/PR/head/CI и ограничениями.

## Сводка текущего прохода

8 выполнены в указанном программном объёме,8 частично готовы,3 открыты (№13,14,19). Наличие программного маршрута №15/17 не закрывает реальный положительный сценарий. План исполнения: `master-pass-20261009.md`.

## Уточнение реальных источников и CI — §68.5

DWG предоставлен: пять одинаковых копий, один уникальный исходник AC1032. Отдельный DXF прочитан: 15 906 объектов; 1 304 строки предупреждений, 210 строки ошибок конвертера. Приложение BLOCK CAD_ENTITY_LIMIT=10000. Оригиналы не изменены; эквивалентность, controlled edit и приёмка не подтверждены.

Windows: 23 native tests и живой Ollama/browser inference PASS на b37646d. Исправления DOM teardown и Windows canonical path опубликованы в PR92 head6032367; свежий полный CI выполняется. Физическая установка/перезагрузка и release открыты.

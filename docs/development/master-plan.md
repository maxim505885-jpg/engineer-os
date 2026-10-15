# Актуальная передача: полный аудит и план1.0 — 15.10.2026

Проверенный candidate: `3f87eed93f1460715a35df0a6cbf0d8550d380e3`, PR153 merged;
tree `b91c33d7cbb11e008e15516ecae4a74d33ac69bd`. Exact-head CI PASS.
Читать сначала [полную матрицу19](../qa/2026-10-15-full-readiness-audit.md),
[определение готовности1.0](release-v1-definition-20261015.md) и
[исполняемый план13пакетов](../superpowers/plans/2026-10-15-engineer-os-v1-completion.md).
Главные product gaps: production verification issuer, Windows document qualification,
интеграция новых CLI tools в UI/Evidence, real ACCEPTED→memory→FINAL report, поставка.
ЛИРА/SCAD — отдельный vendor поток согласно исходному MASTER§8, не автоматический
block базового runtime. Первое исполнение:T01→T02→T03/T04 иT05. Процент готовности
не назначен. Старые записи ниже — история и не заменяют новую матрицу.

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

# MASTER PLAN — ENGINEER OS

## Приоритетное состояние — MASTER audit, 15.10.2026

Этот раздел заменяет устаревшие указатели кандидата ниже, не удаляя историю.
GitHub candidate подтверждён: `db29e4c946e4db5e088e8fdd727c6165365dcc4d`.
Рабочий пакет: `codex/master-engineering-audit-20261015`.
Полная матрица19: [MASTER audit](../qa/2026-10-15-master-engineering-audit.md),
план исполнения: [master-engineering-pass-20261015.md](master-engineering-pass-20261015.md).

Исправлены runtime Docling limitations/table-loss из pipeline threads и source
identity check. Добавлены изолированные optional IFC/GUID diff, DXF comparison,
Pynite analytical beam benchmark и CLI; базовый Ollama/UI не заменены.
7/7 Chromium PASS; полный pinned Windows suite1085 не зелёный:0 assertion failures,
7 errors,47 skips; детали и отдельные повторы в QA. Review findings исправлены.

Порядок: №13 реальный source-bound rerun/визуальная сверка → DWG converter loss
ledger/roundtrip → IFC formal requirements и геометрическая квалификация →
расширение control calculations. Нормы проверять только по законным актуальным
источникам. №14/15/16 требуют настоящего qualified ACCEPTED; №9/19 ждут physical
clean install/reboot и полного release audit. Ни один engineering BLOCK не снят.

## Актуализация №14 — 14.10.2026, PR150 / очередность до v1.0

Текущий проверенный candidate: `integration/release-candidate-v1` `091edd1c2881b1f7c416034b45c1d6f48899bcdd`. PR150 открыт на этом candidate, не слит. На его точном head `9189a124af95af0cfbcfa4b9688b7731307dc7ea` PASS все три GitHub checks: Core Tests, Windows local runtime и Repository Security Guard. Изменения включают bounded locator для vector graphics, сохранение source-located текста при неразобранной таблице с fail-closed `BLOCK`, а также защиту batch/evidence/V4 review от принятия частичного результата. Локально проверены 20 extraction/vector, 33 parser/evidence/batch tests и предыдущий полный набор 1,065 тестов (известные Windows symlink/temp ACL ошибки описаны в локальных логах; latest head подтверждён зелёным GitHub Core).

- №13 остаётся BLOCK. Сохранённый V4 extraction-review охватывает очередь всех534 страниц: 137 extraction BLOCK,19 visual table review,378 text semantic review. Старый triage содержит143 manual entries; шесть из его восьми `OTHER_EXTRACTION_FAILURE` имеют поздний page audit exit0, output и provenance, а две страницы (57,58) остаются exit1 без output. Значит 143−6=137 текущих extraction BLOCK; причины 78/52/5/2 совпадают после per-page reconciliation. Это снимает отчётную рассинхронизацию, но не проверяет полноту содержимого или всех страниц.
- Векторные страницы теперь могут записывать максимум100 bounding boxes на страницу и число пропусков. Это только локатор для review; `VECTOR_CONTENT_UNVERIFIED`, BLOCK и `acceptance=false` сохранены. Оригиналы не изменялись.
- Для двух воспроизведённых table-caption pages добавлен version12 partial output: source-located текст сохраняется, `TABLE_CAPTION_WITHOUT_VERIFIED_ROWS` ставит документу BLOCK, evidence validation и batch review не принимают его. На свежем read-only V4 run страницы57/58 вернули23/33 текстовых блока, без проверенных table rows; outputs/audits сохранены вне исходного проекта. Полный534-page rerun ещё не выполнен.
- №14: свежий узкий Stage7/8 run на реальном объекте закончился BLOCK/BLOCK; `ACCEPTED=false`. Подробные hashes/пользовательские метаданные хранятся только локально.
- Повторный run4 на пяти hash/size-совпадающих локальных intake-копиях также завершился свежим Stage7/Stage8 `BLOCK/BLOCK`, `ACCEPTED=false`. Intake `PARTIAL`; три PDF имеют image/vector content gates, DOCX имеет 112/553 blocked logical units и непроверенную layout/auxiliary placement, DWG `UNAVAILABLE`. Два локальных Qwen specialist calls завершились ERROR после 180-секундных тайм-аутов без findings/evidence. Audit дополнительно фиксирует отсутствие формального ТЗ/чек-листа/evidence candidates и незакрытые инженерные gates. Повтор не меняет статусы №13/14 и не устанавливает состояние объекта.
- №6: нормативные/расчётные предметные gates открыты; фактические LIRA/SCAD расчёты отложены пользователем. №9 physical Windows и №19 финальный release audit не пройдены.

Последовательность: (1) завершить review PR150 и включить его в официальный candidate после зелёного exact-head CI; (2) проверить extraction regression corpus и весь 534-page review без подмены выборкой; отдельно восстановить полный чтение PDF image/vector и DOCX layout/auxiliary data; (3) закрыть доступные нормативные и инженерные gates №6, оставив solver открытым до отмены отсрочки; (4) повторить полный fresh Stage7 + Stage8 на квалифицированном объекте для №14 после требований/evidence/специалистов; (5) завершить независимые реальные сценарии №15 memory, №16 accepted report, №17 DWG roundtrip и №18 local/optional provider receipts; (6) выполнить фактические Windows checks №9; (7) выполнить полный clean-release, backup/restore и документационный audit №19. Статусы всех пунктов — в `ENGINEER_OS_PROJECT_MAP.md` §66; историческая актуализация ниже не отражает newer state.

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

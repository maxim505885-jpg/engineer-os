# MASTER PLAN — ENGINEER OS

Единая нумерация: **19 пунктов**. Эта сводка заменяет противоречащие текущие статусы планов17/19; история сохранена в `master-plan-17-history.md`, `master-plan-19-history.md` и живой карте. Результат нельзя переносить между планами по номеру без названия и критерия.

**Активный план:** кандидат PR99 — §79; native LIR/API — §81, инвентарь ЛИРА2024 получен, подготовлен частичный экспортёр таблиц (draft PR100). Реальная выгрузка/полнота/RES/сайт ещё не проверены. План 8 ✅ / 8 🟡 / 3 ❌.

| № | Этап | Статус | Проверенный результат и оставшийся критерий |
|---|---|---|---|
| 1 | Единая рабочая версия | ✅ Кандидат | PR 91–98 приняты; кандидат 9a92b96e, проверенное дерево 2c36ea30; итог §74.1. |
| 2 | Качество OCR и локальной модели | ✅ программный контур | Извлечение/метрики/отрицательные gates и живой Linux qwen3 проверялись. Это не полнота V4 и не Windows. |
| 3 | Большие документы: resume/recovery | ✅ программный контур | Checkpoints, identity, budgets, retry. Полнота инженерного документа отдельно в№13. |
| 4 | DOCX/XLSX/DOC и остальные заявленные форматы | ✅ программный контур | Оригиналы, logical locators, provenance, native/OCR маршруты; сложные таблицы отдельно. |
| 5 | ТЗ → источник → требование → вывод | ✅ программный контур | Полный индекс47 требований,42 исходные позиции, версионные оценки и глобальные gates. |
| 6 | Нормативная и расчётная верификация | 🟡 Частично | Приём TXT/ALD/COP/log/ZIP готов в PR99; инженерная семантика, завершённые результаты и связь LIR→run/нормы остаются открыты; §79. |
| 7 | Реальный инженерный case workflow | ✅ отрицательный сценарий | Три оригинала,36 кандидатов, роли и нормативный replay воспроизводимы; объект не ACCEPTED. Положительный сценарий в№14. |
| 8 | FINAL AUDIT / acceptance boundary | ✅ программный контур | Immutable/stale/tamper/foreign source gates. Нет подтверждённого положительного инженерного объекта. |
| 9 | Windows one-click runtime | 🟡 | Native Windows CI полностью PASS: clean start/cache repair/restart, 23 tests, live Ollama, 4 Chromium routes. Physical PC clean install/reboot остаётся. |
| 10 | Консолидация и источник истины | ✅ Интеграция | PR 91–98 merged; все 9 CI SUCCESS, итог §74.1. |
| 11 | Интерфейс и пользовательский маршрут | 🟡 интеграция | Дизайн кандидата сохранён вместе с формами источников/ТЗ/ролей/черновиков. Все4 browser маршрута, включая CAD/memory/mobile/session reset, прошли. Финальная приёмка интерфейса на реальном accepted объекте остаётся. |
| 12 | Backup/restore/recovery/security | 🟡 интеграция | Один bounded engine, чтение двух форматов, SHA256/SQLite/no-replace/key/derived/settings. Совместимость двух форматов проверена; воспроизведённые symlink/hardlink внутреннего DB/lock/settings/key устранены. Core/Security CI PASS; CodeQL 29 alerts individually reviewed/dismissed FP,checkSUCCESS; физический Windows NOT_RUN. |
| 13 | Производственная полнота документов | ❌ | Полный DOCX 14 678/14 678, 0 failed/truncated, 7 022 BLOCK. Независимо сверены 12 826 ячеек/5 759 native vertical links. Rendering, формулы, графика, OCR-конфликты/V4/qualified ground truth открыты. |
| 14 | Реальный принятый инженерный кейс | ❌ | Требуется реальный квалифицированный объект с полным ТЗ, свежими источниками, нормами/расчётами и положительным FINAL AUDIT. |
| 15 | Подтверждённая инженерная память | 🟡 программный маршрут | Версионное знание только из актуального принятого audit; scope/recall/revoke/delete/export/backup, повторная проверка обязательна. Реальный положительный ACCEPTED→memory сценарий ещё не выполнен. |
| 16 | Генератор отчётов | 🟡 | Редактируемый черновик, история, источники/координаты, dossier покрытия/stale guards,3 шаблона и источник-связанные иллюстрации DOCX/PDF реализованы. Общая проверка726/Node/DOM/Chromium и визуальная проверка DOCX/PDF PASS; выпуск принятого документа остаётся открыт. |
| 17 | CAD/DWG | 🟡 Частично | Приложение читает 10 172 графические сущности реального DXF. Предел чтения 50 000, редактирования 10 000; геометрия, предупреждения конвертации и roundtrip не проверены. |
| 18 | Multi-AI connector | 🟡 локальная часть | Бесплатные Ollama/Open WebUI, настройки и isolated diagnostic готовы. Shared gateway защищён от ложных hostname/redirect/незавершённых/слишком больших ответов. Единый optional-provider receipt/gate сценарий полностью не проверен. |
| 19 | Финальный стабильный выпуск | ❌ | Требуются все продуктовые критерии, clean install, physical Windows, accepted case, release/tag и соответствующий main. |

✅ относится только к указанному критерию и набору данных. Программный PASS не означает ACCEPTED объекта. BLOCK означает отсутствие проверенного основания, а не установленный дефект конструкции. Тестовый model protocol/replay не выдаётся за новый живой inference/solver/expert review.

## Соответствие прежнему плану17

| Прежний17 | Единый19 | Название |
|---|---|---|
| 1 | 1/10 | PR 91–98 приняты; кандидат 9a92b96e, проверенное дерево 2c36ea30; итог §74.1. |
| 2 | 8 | Границы доверия |
| 3 | 12 | Backup/restore |
| 4 | 11 | Кабинет |
| 5 | 18 локальная часть | Модель/задачи |
| 6 | 4/13 | Форматы/полнота |
| 7 | 5/7 | ТЗ/ядро |
| 8 | 6 нормы | Нормативы |
| 9 | 6 расчёт | Solver, отложено |
| 10 | 16 | PR 91–98 merged; все 9 CI SUCCESS, итог §74.1. |
| 11 | 17 | CAD |
| 12 | 14 | Принятый кейс |
| 13 | 15 | Полный DOCX 14 678/14 678, 0 failed/truncated, 7 022 BLOCK. Независимо сверены 12 826 ячеек/5 759 native vertical links. Rendering, формулы, графика, OCR-конфликты/V4/qualified ground truth открыты. |
| 14 | 11 | Финальный UI |
| 15 | 12 | Надёжность |
| 16 | 9 | Windows, отложено |
| 17 | 19 | Release |

## Порядок дальнейшей работы

1. №1/10 выполнены:triage29 и PR91→candidate завершены. №12:Windows ACL иконкурентная подмена вне owner-controlled contract не подтверждены.
2. №13: independently verified полнота сложных mixed/raster таблиц/графики полного V4 и представительный корпус.534/534 обработанных страниц V4 остаются BLOCK.
3. №6/14: применимые свежие нормы,qualified actual evidence и vendor export/run/correlation, затем реальный положительный FINAL AUDIT. Расчёт ранее отложен пользователем.
4. №15/16/17: реальный ACCEPTED→knowledge маршрут,принятый документ,проверка эквивалентности реального DWG, controlled edit/roundtrip и обоснованное расширение поддерживаемой геометрии. Программные память/шаблоны/иллюстрации/DXF-аннотации уже реализованы и проверены.
5. №18: optional-provider live/receipt contract. Бесплатные локальные провайдеры не требуют облачного API.
6. №9/19: physical Windows cold-start/restart/reboot/end-to-end и clean install последними; затем FINAL RELEASE AUDIT,main/tag.

Не снимать реальный BLOCK ради номера пункта. Финальный релиз не объявлять по числу тестов. Карту обновлять после каждого существенного результата с branch/PR/head/CI и ограничениями.

## Сводка текущего прохода

8 выполнены в указанном программном объёме,8 частично готовы,3 открыты (№13,14,19). Наличие программного маршрута №15/17 не закрывает реальный положительный сценарий. План исполнения: `master-pass-20261009.md`.

## История промежуточных проверок — §68.5

DWG предоставлен: пять одинаковых копий, один уникальный исходник AC1032. Отдельный DXF прочитан: 15 906 объектов; 1 304 строки предупреждений, 210 строки ошибок конвертера. Приложение BLOCK CAD_ENTITY_LIMIT=10000. Оригиналы не изменены; эквивалентность, controlled edit и приёмка не подтверждены.

Windows: 23 native tests и живой Ollama/browser inference PASS на b37646d. Исправления DOM teardown и Windows canonical path опубликованы в PR92 head6032367; свежий полный CI выполняется. Физическая установка/перезагрузка и release открыты.

Реальный OCR завершён:43/43 страницы,66 349 символов,2 615 блоков,0 failed;43BLOCK из-за OCR_LOW_CONFIDENCE/непроверенной графики. Native Windows recovery/browser PASS; fixture subprocess cwd исправлен в ff586382, полный свежий CI выполняется. Актуальное состояние и доказательства: последний §68 живой карты.

Native Windows PR/push и полный Linux push на ff586382 SUCCESS:23nativeWindows tests,liveOllama,4browser routes;728Linux tests(2Windows-only skips),4Node,2HTTP/DOM,4 Chromium. Дублирующий required PR Linux CI ещё выполняется; merge PR92 pending. Physical PC и accepted engineering gates открыты.

## Итог §68.8

Все 10 проверок SUCCESS на ff586382; PR 92 принят в кандидат 8beb559, exact tree match f5f78d4 подтверждён Git API. Linux PR/push: 728 tests (726 PASS, 2 native-Windows-only skips), 4 Node, 2 HTTP/DOM, 4 Chromium. Windows PR/push: 23 tests, реальный Ollama qwen3:0.6b, 4 Chromium и supervisor/cache/restart PASS. Инженерные критерии 2–5 остаются частичными; physical PC, accepted case, графика/формулы/сложные таблицы, vendor exports/run и native CAD geometry/roundtrip не приняты. Следующие gates и полный отчёт: `docs/qa/2026-10-09-five-criteria-verification.md`. Актуальная живая карта: docs/development/ENGINEER_OS_PROJECT_MAP.md в docs/project-map-handoff-20261005.

## Итог §69 — большие CAD-источники

PR 93 принят после всех 9 проверок SUCCESS. Кандидат 9bf58d0 имеет проверенное дерево 2cb8e47. Linux: 731 тест (729 PASS, 2 пропуска только для Windows), 4 Node, 2 HTTP/DOM и 4 Chromium PASS. Windows: 23 теста, реальный Ollama и 4 Chromium PASS. Реальный DXF прочитан без изменения источника; запреты редактирования сохранены. Итог плана: 8 готовы в указанном объёме, 8 частично, 3 открыты. Следующий программный шаг — OCR по областям с проверкой покрытия и координат; эксперимент пока не является готовой функцией.


## Продолжение §70 — OCR по областям

Optional regions: целая страница + 4 перекрывающиеся области, исходные координаты, общие бюджеты. Альтернативы явно маркируются для модели. Локально 35 focused / 741 full tests PASS с 2 Windows-only skips; независимые Important исправлены RED→GREEN. PR 94 ожидает свежего CI и завершения реального повторного прогона. №13 остаётся открыт: эталонная сверка текста/чисел/таблиц/графики и полный V4 не приняты. Итог 8/8/3 сохраняется.


## Итог §70.1

PR 94 принят; все 9 CI checks SUCCESS. Финальный реальный OCR: 43/43 страниц, 215 проходов, исходники неизменны. Программный режим готов, полнота не доказана. Следующий №13 — локализация и эталонная сверка числовых подписей/таблиц/формул, затем графика и весь V4. Числа распознавателя не принимать автоматически: выборочная визуальная проверка выявила ошибку. Далее нормы/расчёты, реальный FINAL AUDIT, принятая память/отчёт/CAD; физическая Windows и выпуск последними. План 8 готовы / 8 частично / 3 открыты.

## 71. Выбранный OCR-фрагмент для мелких числовых подписей — 09.10.2026

PR 95: `6b7674bc57ce62f8abac2cd702720e7c7c1d6488`, дерево `e404c539dcd28394980b937b5eb1fb0a9a676f9a`, равно локальному `4e4ce1b`. Кандидат до завершения CI остаётся cca057f. Реализован `python -m scripts.local_ocr_region`: SHA-guard оригинала, исключительное создание нового JSON, выбранная область в исходных unrotated crop-relative координатах, один проход PSM 6 / scale≤6 и прежние общие лимиты. Настройки записаны в identity и dossier. Качество, page/document completeness и acceptance не подтверждаются.

Реальный размер на странице 1: предыдущий региональный кандидат 82406, визуально 82400; выбранная область [760,795,950,830] прочитала 82400, также две подписи 6000. Исходник SHA6092ab… неизменен. Один проход: 239400 пикселей / 354 TSV bytes / 3 слова. Это точечная сверка, не квалифицированный эталон всего корпуса; противоречивый старый кандидат сохранён. Xref warnings остаются.

RED→GREEN: отсутствовавшие API/CLI выявлены новыми тестами до кода. Отдельное ревью: Important неточные execution settings исправлен, добавлены прямые проверки CLI source/symlink/hardlink aliases. 6 selected tests PASS, полный локальный набор 747 (745 PASS, 2 native Windows skips), 4 Node, architecture/compile/diff PASS. Remote CI и интеграция фиксируются отдельным итогом после фактического завершения.

План остаётся 8✅ / 8🟡 / 3❌. №13 открыт: покрытие таблиц, формул, merged cells, всей графики и V4 по проверенному эталону. Затем нормы/семантические расчёты и положительный FINAL AUDIT, принятая память/отчёт, CAD equivalence/roundtrip, provider receipts, физический Windows и выпуск. Детали: docs/qa/2026-10-09-selected-region-ocr.md.

## 71.1. Итог выбранного OCR-фрагмента: PR 95 принят

Все 9 checks на `6b7674bc57ce62f8abac2cd702720e7c7c1d6488` SUCCESS. Кандидат `c4e1181a5f7463a03ec2fce279aab6641e420e61`, дерево `e404c539dcd28394980b937b5eb1fb0a9a676f9a` равно проверенному опубликованному и локальному `4e4ce1b`. Linux PR/push: 747 тестов / 745 PASS / 2 native Windows skips, 4 Node, 2 HTTP/DOM и 4 фактических Chromium сценария PASS. Windows: 23 теста, startup/cache/restart, реальный qwen3:0.6b через UI и все 4 Chromium PASS. Physical Windows по-прежнему NOT_VERIFIED.

Дополнительная выбранная сверка трёх исходных областей: размер 82400 и отметка -4.200 совпали; номер листа 513 не прочитан корректно (whole-page ранее прочитал его). Итого 2 MATCH / 1 MISMATCH, assistant spot review без qualified ground truth. Новый CLI — дополнительный проверяемый кандидат; он не заменяет прежнее извлечение и не подтверждает полноту. Оригиналы неизменны, старые противоречивые кандидаты сохранены.

Готовность 8✅ / 8🟡 / 3❌. Из 5 критериев закрыт программный CodeQL/единый кандидат; остальные частичны. Следующий шаг №13: эталонное покрытие чисел/таблиц/формул/графики полного V4, с фиксацией пропусков и конфликтов; после него реальные нормы/расчёты/FINAL AUDIT и остальные product gates. Полные CI receipts: docs/qa/2026-10-09-selected-region-ocr-ci.json.

## 72. Структура формул и объединений Office — 09.10.2026

PR 96: `1230aa3a24c1bb46fe4dbacb30d86b1777927388`, дерево `2ab64d8c8db402ed3146327162ab19356c9809ea` равно локальному `10d58f3`. Сохранены отдельные логические кандидаты Word OMML: нормализованный XML, буквальные токены, родительский абзац/ячейка, без выдуманного номера физической страницы. Это не линеаризованная и не вычисленная формула. Word gridSpan/vMerge/hMerge сохраняются с namespace-qualified атрибутами и исходным ordinal ячейки. XLSX merged-range declarations сохраняются независимо от наличия ячеек; значения не распространяются. Formula presence отделён от text, shared followers учитываются. Прежние warnings, limits, immutable originals и parser identity gates сохранены; старые checkpoints не являются результатом нового парсера.

Три реальных Office-оригинала: DOCX489/489, XLSX125/125 и51/51, всего665/665 (ранее660; добавлены2 equation units и3 range units). Failed0, text truncation0, оригиналы неизменны. Независимый source XML inventory совпал:2 Word equations и их буквальные токены,14 Word cells с merge declarations,3 XLSX ranges и4 formula cells. Исходные31 Word drawing/media members и7 XLSX media members не интерпретированы; XLSX содержит1 drawing reference. Rendering/layout/interpretation/evaluation НЕ подтверждены.

Поправка прежней статистики:48 MERGED_CELLS_UNVERIFIED были48 предупреждениями на уровне units одной worksheet, а не48 отдельными merged ranges. Точные source declarations —3 ranges. Исторические предупреждения сохраняются как история; текущий критерий исправлен.

TDD: четыре missing-structure asserts RED; formula count и shared-follower RED→GREEN. Ревью Important namespace collision и Minor sibling equation tail воспроизведены2RED, исправленыGREEN. Focused22PASS. Локальный frozen full755 тестов /753PASS /2native Windows skips,4Node,architecture/compile/diff PASS. Реальная parser implementation сверена по hash с проверенным кодом. Детали: docs/qa/2026-10-09-office-source-structure.md. Общий план8✅/8🟡/3❌.

## 72.1. Итог Office-прохода: PR 96 принят

Все 9 checks на `1230aa3a24c1bb46fe4dbacb30d86b1777927388` SUCCESS. Кандидат `f2a58399384dacaff600714cc79e7b85ad3e03a9`, дерево `2ab64d8c8db402ed3146327162ab19356c9809ea` равно проверенному опубликованному и локальному `10d58f3`. Linux PR/push: 755 тестов (753 PASS, 2 native Windows-only skips), 4 Node, 2 HTTP/DOM и 4 фактических Chromium сценария PASS. Windows: 23 теста, startup/cache/restart, реальный qwen3:0.6b через UI и 4 Chromium PASS. Physical Windows NOT_VERIFIED. Полные receipts: docs/qa/2026-10-09-office-source-structure-ci.json.

Три реальных Office-оригинала обработаны полностью в пределах объявленных logical units: 665/665; native source structure и literal tokens сверены, но page/layout/document completeness не подтверждены. Приёмка не выдана. Точный XLSX merged-range count — 3; прежние 48 — unit warnings, не число объединений.

План 8✅ / 8🟡 / 3❌. По пяти критериям: CodeQL/единый программный кандидат закрыт; документальная полнота, нормы/расчёты/реальный FINAL AUDIT, принятая память/отчёт/CAD/providers и physical Windows/release частичны. Далее №13: rendered tables/formulas/31 Word drawings/7 XLSX media members, числовые OCR-конфликты и полный V4 по qualified ground truth. После этого актуальные нормативные основания и 8 semantic calculation roles с реальным solver-run/actual correlation, ACCEPTED-кейс и оставшиеся product gates. Новый результат не снимает BLOCK автоматически.


## 73. Полный доступный DOCX: крупный Office-исходник — 09.10.2026

PR 97: `fd6f08ca51313bbf3db5415e6ba8191355da0a69`, tree `b05f085fa7110dc49feb3cd4822a2643c0432b98` равно локальному `dbceac93a4bbf3778d640d87507a39d7bb31be5e`. До завершения CI кандидат остаётся f2a58399. Полный доступный DOCX от15.09.2026 найден и обработан, исходник147210288байт, SHA256 b253439bdd673a775eaf209ca7d398d766efae5f4a18ac33fa6679f7faae28a5. Это не подмена отсутствующего qualified V4 PDF ground truth.

Сняты реальные входные блокировки: DOCX/XLSX256MiB во всех UI/HTTP/preservation/Drive путях; остальные форматы100MiB. ZIP declared expansion512MiB, XML aggregate32MiB/per-part16MiB; изображения не распаковываются. Parsed-byte SHA, per-unit stat и final SHA сохраняют immutable-source gates; повторное хеширование147MB на каждой единице устранено. Source review переведён на streaming SHA; устаревшая UI-подпись исправлена.

Фактически14678/14678 logical units за244.411секунды, failed0, truncated0,1095842 textchars. 7022units остаются BLOCK. Source XML:41 OMML equations/tokens совпали,6300 merge declarations,655 Word drawing elements,642media members. Не смешивать элементы/файлы и warnings: DRAWING_NOT_READ509, FIELD_NOT_EVALUATED68, NO_TEXT438, MERGED_CELL_UNVERIFIED6300, BODY_STRUCTURE_UNVERIFIED11, EQUATION_NOT_READ70. Warnings могут пересекаться. Physicalpages unknown; rendering/layout/formula semantics/graphics/document completeness UNVERIFIED. Исходник неизменён, acceptance=false.

На реальном147MBоригинале quote/logicalunit7 зарегистрирован через штатный provenance gate. Все3решения SOURCE_CONFIRMED/REJECTED/NEEDS_DATA прошли streaming identity check, каждое SOURCE_REVIEW_ONLY/actor_verified=false/acceptance=false. Это регрессия пути проверки цитаты, не квалифицированная приёмка.

Независимое ревью: Important100MBreviewcap и MinorUIwording воспроизведены/исправлены, остаточных Critical/Important/Minor0. Focused47Python и5Node PASS, architecture/compile/JS/diff PASS. Frozen full763/761PASS/2Windows skips с реальным rus+eng OCR; remoteCI pending. Parseridentity фактического full run точно совпал с frozenOfficeкодом.

План8✅/8🟡/3❌. №13 остаётся открыт: rendered tables/merged cells/formulas,655 drawing elements/642media нового полного DOCX, прежняя Office/OCRграфика и числовые конфликты, полный V4 и qualified ground truth. Далее нормы/8semanticroles/solver-run/actualcorrelation/FINAL AUDIT, реальный ACCEPTED→memory/report,CADroundtrip,liveproviderreceipts,physicalWindows/release. Детали docs/qa/2026-10-09-large-office-input.md.

Дополнительная проверка PR97: первый headfd6f08c получил763PythonPASS/761PASS/2skips, но LinuxPR DriveDOM упал на new-chat. PushLinux и Windows прошли. Детерминированно воспроизведены две stale bootstrap races: поздний список скрывал созданный чат и initial list мог переключить пользователя назад. Исправлены latest-request render guard и initial-consumer current/creating guard. Controlled-delay HTTP/DOM RED→GREEN, VMinitial-response RED→GREEN. Итог6Node/2localHTTP-DOM PASS, независимое ревью0остаточныхImportant. Новый head `2be525c674037aa87e498fd2abf25dd8ad0709f4`, tree `554b44515fe801ac20b92b31f373df21f0a29c9e` равно локальному `b1d724c8da4cfbd7a3f03fa386bd85b724a0bb86`; CI выполняется заново. Первое падение сохранено в receipts, не скрыто rerun.

Последний frozen head PR97 `187b6d88448806f31781df7cf68f6bd6bf826b22`, tree `2af4da649a69d4f60c7c51ffd7331af1ea6ccb80` равно локальному `9aa29f7724905137bb6c816a59101ef060a4cc57`. На предыдущем head Windows23/live Qwen/2Chromium прошли, но очистка intake fixture дала EBUSY app.lock. Windows журнал показывает EBUSY вскоре после PASS и не доказывает исполнение timeout-ветки. В исходном fixture ожидался exit, а не close; отдельно детерминированно воспроизведена timeout-ветка SIGKILL, которая разрешала удаление до закрытия процесса. Shared stop helper ждёт close, имеет bounded deadline и не удаляет каталог при неудачной остановке; rm имеет ограниченные retries для transient locks. Actual-cleanup RED→GREEN,7Node PASS, независимое ревью0Important. LocalChromium NOT_RUN: отсутствует browser binary; это не заменено заявлениемPASS. Финальная реальная проверка Windows/Linux выполняется на новомhead.

## 73.1. Итог полного Office-прохода: PR 97 принят

Все 9 CI checks на `187b6d88448806f31781df7cf68f6bd6bf826b22` SUCCESS. PR 97 принят в кандидат `f83c4d5fbaac8e602757ca6fac1646b86589cdff`. Дерево `2af4da649a69d4f60c7c51ffd7331af1ea6ccb80` равно проверенному опубликованному коду и локальному `9aa29f7724905137bb6c816a59101ef060a4cc57`. Linux PR/push: 763 Python-теста (761 PASS, 2 native Windows skips), 7 Node, 2 HTTP/DOM и 4 реальных Chromium-сценария PASS. Windows: 23 теста, clean start/cache repair/restart, настоящий Ollama qwen3:0.6b и все 4 Chromium-сценария PASS; очистка завершилась успешно. Физический Windows ПК по-прежнему NOT_VERIFIED. Receipts: docs/qa/2026-10-09-large-office-input-ci.json.

Полный доступный DOCX 147 МБ обработан: 14 678/14 678 логических единиц, 0 ошибок исполнения и обрезаний текста, исходник неизменён. Сохранены 41 OMML-уравнение с буквальными токенами и 6 300 объявлений объединённых ячеек; source XML сверка совпала. 7 022 единицы остаются BLOCK. 655 элементов графики и 642 media-файла, отображение таблиц, смысл и вычисление формул, полнота страниц/документа не приняты. Число физических страниц неизвестно; полный DOCX не объявлен проверенным V4 PDF. Три source-review решения на настоящем большом оригинале прошли без инженерной приёмки.

За проход закрыты конкретные программные дефекты: несовместимые входные лимиты большого Office, ограниченное чтение оригинала при source review, повторное полное хеширование на каждой единице, две гонки старых списков чатов и преждевременная очистка тестового процесса. Начальные падения CI сохранены, исправления проверены RED→GREEN и независимым ревью.

План остаётся **8 ✅ / 8 🟡 / 3 ❌**. Из пяти критериев закрыт CodeQL/единый программный кандидат; остальные частичны. Следующий шаг №13: квалифицированная сверка rendered tables/merged cells/formulas, всей графики и числовых конфликтов, V4 PDF и полного эталонного покрытия. Затем №6: восемь семантических расчётных ролей, актуальные нормативные основания, реальный solver-run и связь с фактической конструкцией. После этого №14: положительный FINAL AUDIT; на его основании принятая память и отчёт, CAD equivalence/roundtrip и live-provider receipts. Физический Windows и №19 release/main/tag — после закрытия продуктовых критериев. BLOCK не снят автоматически.


## 74. Сетка и связи объединённых ячеек Word — 09.10.2026

PR 98: head d6bb3976d0513828a2cf3b8517cc7fbe7ac7d23e, tree 2c36ea304797f56e69562d1673f3ee018d364bbe равно локальному843adfe3c5e17fdf3b98cb5429837e33c7ac304d. До завершения CI кандидат остаётся f83c4d5f. Добавлены source-grid intervals, gridBefore/gridAfter, gridSpan и точные vertical restart anchors; прежние XML-cell ordinals и исходный текст сохранены, значения не распространяются. Буквальная структура источника не является rendered layout или инженерной приёмкой.

Чтение полного147MBисходника:118таблиц,12826ячеек; все declared-grid intervals согласованы,5759vertical continuations восстановлены. Повторный полный Store extraction выполняется; завершение и независимая XML-сверка будут добавлены после факта. Исходные merge/layout/formula/drawing warnings сохраняются; число BLOCK искусственно не уменьшено.

Тесты на missing locators, grid gaps, orphan/changed-width continuations, bounds, invalid/duplicate declarations, missing/width mismatch, wrappers и tracked row/cell properties воспроизведеныRED→GREEN. Независимое ревью выявило2Important: пропущенные wrapped rows и structural revisions; оба исправлены, остаточныхCritical/Important0. Frozen full770тестов/768PASS/2nativeWindows skips с реальнымrus+engOCR;7Node,architecture/compile/diff PASS.

План8✅/8🟡/3❌. №13 открыт: rendered merged tables/formulas, графика и числовые конфликты, полныйV4PDF и qualifiedgroundtruth. После него нормы/8semantic roles/solver-run/actualcorrelation/FINAL AUDIT, accepted memory/report,CAD/providerreceipts,physicalWindows/release. Деталиdocs/qa/2026-10-09-word-table-grid.md.


## 74.1. Итог — native Word grid и вертикальные объединения

[PR 98](https://github.com/maxim505885-jpg/engineer-os/pull/98) объединён в `integration/release-candidate-v1`: `9a92b96ec892d8e7bdf54a95d0875afbcf4b78b5`. Дерево `2c36ea304797f56e69562d1673f3ee018d364bbe` точно совпало с проверенным head `d6bb3976d0513828a2cf3b8517cc7fbe7ac7d23e` и локальным кодом. Все девять CI завершились SUCCESS; Linux 770 тестов (768 PASS, 2 Windows-only skips), 7 Node, 2 HTTP/DOM и 4 Chromium; Windows 23 теста, clean start/cache repair/restart, реальный Ollama qwen3:0.6b и 4 Chromium PASS. Независимое ревью: оставшихся Critical/Important нет.

Полный неизменённый DOCX 147 210 288 байт обработан штатным Store за 364.564 секунды: 14 678/14 678 единиц, 0 failed/truncated, 1 095 842 сохранённых символа. Во всех 118 таблицах независимый разбор XML оригинала подтвердил записанные интервалы 12 826 ячеек и 5 759 продолжений вертикальных объединений. SHA256 источника `b253439bdd673a775eaf209ca7d398d766efae5f4a18ac33fa6679f7faae28a5`.

Native координаты сохранены отдельно от XML ordinal; значения между объединёнными ячейками не переносятся. Неопределённые структуры, скрытые wrappers и tracked changes сохраняют запреты. Это доказательство структуры источника: rendered layout, смысл формул и инженерная приёмка не подтверждены. 7 022 единицы остаются BLOCK; acceptance=false. Физический Windows NOT_VERIFIED.

План: 8 готово / 8 частично / 3 открыто. №13 остаётся открыт: rendered tables/merged cells/formulas, графика и легенды, числовые OCR-конфликты, полный V4 PDF и квалифицированный эталон. Затем восемь семантических расчётных ролей, нормы/solver-run/actual correlation, положительный FINAL AUDIT и ACCEPTED→memory/report; CAD equivalence/roundtrip, live provider receipts; физический Windows и выпуск. Подробные receipts: `docs/qa/2026-10-09-word-table-grid-ci.json` и `docs/qa/2026-10-09-word-table-grid.md`.


## 75. Расчётные комплекты трёх секций — проверка оригиналов 09.10.2026

По предоставленной папке Drive скачаны девять основных LIR (грунт/прогибы/сейсмика для каждой секции) и три DOCX. Размеры 12 файлов совпали с метаданными; SHA256 зафиксированы, все девять моделей различны, после проверки оригиналы неизменны. Всего в DOCX 72 таблицы и 415 media members; визуальная и числовая полнота здесь не подтверждена.

Шесть моделей секций 1/2 имеют распознанный source-format header LIRA-SAPR 2013 / 13.0.0.a. Три модели секции 3 имеют другой вариант ($ и без нулевого разделителя): текущий инспектор не распознаёт его, хотя буквальная строка присутствует. Это ограничение чтения, а не доказательство повреждения модели; формат 2013 не устанавливает версию программы расчёта. Во встроенной записи 0 найдено обозначение соответствующей секции; оно не подтверждает геометрию или связь с конкретным отчётом.

Исходный XML подтвердил четыре текстовые несогласованности: секция 2 — блок 2 в заголовке, блок 3/оси12–17 в задании и блок2/оси12–17 в названиях моделей; секция1 — загружения13/14 обозначены Y, но описаны X; секция2 — сейсмика таблицы X16/Y17 против описания X17/Y18; секция3 — таблица X15/Y16 против описания X14/Y15. Это противоречия текста, не установленная ошибка solver или дефект конструкции. Отчёты и модели не исправлялись.

№6 остаётся 🟡: описания семи semantic roles имеются в отчётах, native-validation не выполнена; отдельный SOLVER_LOG в трёх папках не найден (его отсутствие внутри LIR не утверждается). Связь отчёт→точная модель→run не подтверждена, solver-run NOT_RUN, acceptance=false. Следующий шаг: vendor exports узлов/КЭ, материалов/сечений, нагрузок/сочетаний, опор/освобождений, единиц, solver log/results с SHA исходного LIR и run/version identity; затем actual correlation и нормативный аудит. План остаётся 8✅/8🟡/3❌. Подробный источник-связанный отчёт сохранён как ENGINEER_OS_LIRA_SECTIONS_REVIEW.md; машиночитаемые доказательства — LIRA_SECTIONS_SOURCE_REVIEW.json.


## 78. ALD/COP и прерванный запуск секции1 — 09.10.2026

Прочитаны семь новых оригиналов. Два журнала_01/_01c byte-identical(SHA0b583256e7f62b05977ee91ef65627aaf22803720be313e50c962d91867ae45d). Журнал09.10.2026,FESolver2024.2.3.0,119779узлов/127776КЭ совпадает по числам с TXT секции1; после первой динамической итерации последняя строка «Расчет прерван пользователем». Уточнение прежнего solverNOT_RUN: агент solver не запускал; пользовательская попыткаINTERRUPTED_BY_USER подтверждена, successful full runNOT_CONFIRMED. Итоговые модальные массы/прогибы/усилия этим журналом не подтверждены; SHA входа в журнале не записан.

COP секций2/3 содержит четыре таблицы теоретической несущей способности65/61свай с единицамиtf по буквальному комментарию, не действующие усилия. Все ключи соответствуют КЭ57TXT; четыре раздела имеют одинаковые наборы ключей.65ключей секции2 точно равны65нулевым КЭ57 из§77: COP обозначает их как верхние КЭ57 свайных цепочек. Вывод о65неработающих сваях не обоснован; правильность жёсткости/грунта всё ещё требует проверки.

Все триALD читаются какXML; динамические строки совпали численно с документом15TXT(4/2/3строки). Оси1–5/6–11/12–17 добавляют основание проверить текстовое расхождение секции2. МетаданныеElemBlock не покрывают575/0/25ordinalКЭ, что не доказывает отсутствия этих элементов в модели.

№6 остаётся🟡;8✅/8🟡/3❌. Выполнены проверка новых источников, частичная связьTXT↔ALD/COP/log и уточнение статусаrun. Остаются завершённый журнал/результаты секции1, журналы/таблицы результатов секций2/3, точная связьLIR/TXT/run, семантика/опоры/сочетания/единицы/грунт и нормы/actualcorrelation. Принятие не выдано; код приложения не менялся. QA:docs/qa/2026-10-09-lira-workfile-review.md/.json.


## 79. Приём и автоматический разбор файлов ЛИРА — готово в кандидате, 09.10.2026

[PR 99](https://github.com/maxim505885-jpg/engineer-os/pull/99) объединён в `integration/release-candidate-v1`: `8009b9375de516fdce5d90b7237933441b562c61`. Проверенный head: `5586e5ec10a8aa2db0d85137a3d6559fd964b7c4`; локальное дерево: `097b72e53a9494fbae9aa3dab01b1f6da3597cd9`. На ПК пользователя эта версия не установлена; выпуск и физический Windows остаются непроверенными.

Штатный загрузчик сохраняет оригиналы и SHA256, автоматически разбирает полный UTF-8 TXT ЛИРА, протоколы, ALD/COP и ZIP-комплекты. Карточка файла и контекст анализа содержат наблюдения. Подсчёт узлов/КЭ и буквальная проверка ordinal-ссылок выполняются по всему TXT независимо от preview 100 000 символов. Прерванный журнал получает INTERRUPTED_BY_USER; статический контроль не считается завершением всего расчёта. COP отделён от фактических усилий; ALD не считается результатами. ZIP ограничен 64 записями и 100 MiB распакованных данных; без распаковки на диск, рекурсии, ZIP64/шифрования/ссылок.

Финальный Linux CI: 792 теста — 790 PASS и 2 Windows-only skip; 7 Node, 2 HTTP/DOM и 4 Chromium PASS. Windows: 23 теста, startup/restart, реальный Ollama qwen3:0.6b и 4 Chromium PASS. Все три финальных workflow завершились SUCCESS. 22 новых регрессионных теста PASS. Независимое ревью выявило пять ошибок повреждённых ZIP/TXT, все исправлены; повторное ревью без оставшихся Important. Реальная уязвимость XML через UTF16 без BOM исправлена parser-level RejectDTD и запретом NUL/неподдержанной кодировки; тесты UTF16/UTF32 и независимый parser callback PASS. Повторный CodeQL alert39 проверен как ложное предупреждение о нераспознанном callback, review thread закрыт с подтверждённым основанием.

На трёх исходных TXT получены узлы/КЭ 119779/127776, 37083/44086, 83152/94775; буквальных расхождений node/stiffness references не найдено. Реальный HTTP upload/download сохранил секцию2 побайтно. Один ZIP с десятью исходниками, 52 226 306 expanded bytes, распознал все десять файлов и оба прерванных журнала. Оригиналы не изменялись.

№6 остаётся 🟡; план 8 ✅ / 8 🟡 / 3 ❌. Готов только программный приём и ограниченный разбор источников. Binary LIR semantic decoder, RAR, квалифицированная грамматика/семантика/опоры/сочетания/единицы/грунт, фактические таблицы результатов, завершённые runs, точная связь LIR→TXT→run, нормы и actual correlation остаются открыты; acceptance=false. QA: `docs/qa/2026-10-09-lira-upload-final.md`. Следующий шаг — обновление приложения на ПК и подключение результатов расчёта, затем инженерная верификация.


## 80. Native LIR: официальный API, подготовка адаптера — 09.10.2026

Запрос пользователя: извлекать всю доступную информацию из загруженного .lir; тот же механизм должен работать в сайте. Полное извлечение пока НЕ выполнено. №6 остаётся 🟡, сводка 8 ✅ / 8 🟡 / 3 ❌, acceptance=false.

Исследован оригинал `секция 1 прогибы 16 08 2026 (1).lir`: 44 941 736 bytes, SHA256 `09acaf68e002e7dc846d4663cabf603dd7ed72be98a82a4842f1dbc3ba5adb99`. Он побайтно совпадает с ранее полученным из Drive файлом. Заголовок ULIRA-SAPR; внутри найден ZIP с метаданными и бинарным .sld (2 068 668 bytes). Это не декодирование модели: основная бинарная схема находится вне встроенного ZIP; её семантика и результаты не извлечены.

Официальный путь: COM API модели и отдельный RES API результатов. Современная документация описывает объект документа, таблицы ввода и единицы; форум разработчика подтверждает LiraSapr/LiraSaprRes в 2024. Нельзя переносить ProgID и методы версии2026 на2024 без проверки установленной библиотеки типов. Наличие API не доказывает полноту его покрытия. Источники:
- https://help.liraland.com/ru-ru/extensions/lira-fem-api.html
- https://help.liraland.com/ru-ru/extensions/lira-fem-res-api.html
- https://lira.land/forum/forum9/topic2666/messages/

Подготовлен read-only Windows probe: `tools/lira-api-probe/START.cmd`, `engineer_os_lira_api_probe.ps1`, README. Draft PR100: https://github.com/maxim505885-jpg/engineer-os/pull/100 ; проверенный head `6d35d70d1628ba317a9630f5c208c5436293e848`. Утилита ищет установленную/работающую ЛИРА, читает type libraries через LoadTypeLibEx(REGKIND_NONE), сохраняет JSON с GUID, методами, параметрами и константами; ZIP содержит только отчёт. Нет COM activation, запуска solver, изменения моделей или регистрации. Признаки model_exported/results_exported/source_model_opened=false.

Windows CI run37942829215/job113861325965 SUCCESS: PowerShell parse, C# compilation и чтение реальной системной stdole2.tlb через ту же утилиту; отчёт API_INVENTORY_RECORDED. Это НЕ тест реальной ЛИРА2024, НЕ извлечение .lir. Repository Security Guard37942829147 SUCCESS. Дистрибутив `ENGINEER_OS_LIRA_API_PROBE.zip` подготовлен для одного локального запуска.

Следующий план:
1. Получить инвентарь API установленной ЛИРА2024. В текущей Linux-среде отсутствуют Windows и пользовательская установка; необходим один запуск START.cmd на его ПК.
2. По фактическим сигнатурам реализовать чтение копии модели: перечень таблиц, данные, идентификаторы, единицы и явный отчёт недоступных разделов. Не выдумывать OpenDocument/GetContents и не выполнять методы изменения модели.
3. Отдельно подключить RES API и фактические файлы завершённых результатов. Один .lir не считать доказательством наличия всех результатов; связать результаты с hash модели/версией/запуском.
4. Проверить выгрузку на трёх секциях: полнота доступных таблиц/строк, ключи и связи, единицы, корректность чисел, сохранность оригиналов, отрицательные случаи отсутствующих API/результатов.
5. Подключить проверенный Windows-обработчик к upload pipeline сайта: файл→извлечение→нормализованные данные→анализ→отчёт покрытия. Для облачного развёртывания отдельно проверить допустимость установки/лицензирования ЛИРА; пока Windows backend не развернут. Недоступные данные показывать явно, не объявлять полное покрытие автоматически.

Готово: исследование оригинала, подтверждённый официальный маршрут, проверенный механизм инвентаризации, исходники в GitHub. Не готово: фактическая выгрузка через ЛИРА2024, проверка полноты модели/результатов, интеграция native-reader в сайт. Текущий кандидат приложения остаётся PR99 / `8009b9375de516fdce5d90b7237933441b562c61`; PR100 — отдельная подготовка.


## 81. Получен API-инвентарь ЛИРА2024; частичный native export — 09.10.2026

Пользователь выполнил probe и прислал `lira-api-inventory.json` (1 555 758 bytes; SHA256 `a1244c2ae5caf0d54d35264e415cdbab77a1eacf5d68d08aeb40b7bf57643027`). В отчёте TYPE_LIBRARY_READ для LiraSapr.exe (LiraSapr,36 типов) и LiraResAPI.dll (LiraSaprRes,77 типов), 64-bit. Это подтверждает чтение библиотек установленной2024, но не COM activation или доступ к реальной модели/результатам.

Теперь подтверждены точные методы ILiraApplication.OpenDocument(PathName,RestoreEnv,Silent,pMsgs), ILiraTables.CreateNewItem(Typ,Pars,ModelPart,Nam,AtPos), ILiraTable.GetContents(pData)/GetParameters(pVals). CLSID LiraApplication `b6a075ea-ca19-4011-86b9-6d22f7409c5b`. Есть31 конкретный тип таблиц2–32;0/1 — группы,33 — счётчик, не таблицы. RES API имеет requests для перемещений/усилий, РСН/РСУ, частот, армирования и main data; его наличие не доказывает наличие завершённых результатов.

Подготовлен `tools/lira-native-export/`: START.cmd → выбор .lir → EXPORT.ps1 → model-export.psm1. Contract JSON содержит точные CLSID/методы/перечисления из присланного инвентаря, без копирования vendor libraries. Экспортёр открывает приватную копию, RestoreEnv=0, создаёт табличные представления всей схемы и сохраняет TSV каждого доступного типа без обрезки предпросмотром. Создание input table меняет представление в памяти копии, но SetContents/Apply/Save не вызываются. Записываются SHA256 исходника до/после, метаданные, единицы с api_enumerations, предупреждения открытия, ошибки каждого типа и параметры. Закрывается только документ с подтверждённым путём копии. ZIP содержит manifest+TSV; исходная модель в ZIP не входит. Рабочая копия остаётся отдельно.

Дистрибутив `ENGINEER_OS_LIRA_NATIVE_EXPORT.zip` подготовлен. Следующий необходимый шаг пользователя — распаковать, запустить START.cmd, выбрать исходный LIR и прислать созданный ZIP (или ERROR JSON). Повторять инвентаризацию API не требуется.

Проверки: сначала Windows CI run37945785756/job113871556440 получил ожидаемый FAIL «native model exporter is not implemented». После реализации и последней правки head `69cd4d5d84f011b1a19aef41fbdd57bab7e758a8`, Windows CI run37946306152/job113873329930 SUCCESS: fixture подтверждает copy-only open, все31 попытки/30 успешных/1 недоступную таблицу, >100000 bytes без truncation, сохранение warning, original hash, закрытие собственного документа, архив и false completeness/results/acceptance. Probe compilation/real stdole2.tlb тоже PASS. Security37946306194 SUCCESS. Это тест программного механизма на моделях интерфейсов, НЕ реальный COM/runtime ЛИРА. Проверена точная связь contract→inventory SHA256 и перечисления единиц.

PR100 остаётся draft: https://github.com/maxim505885-jpg/engineer-os/pull/100 . Native export не объединён в кандидат и не подключён к сайту. Кандидат PR99/8009b937 остаётся текущей основной версией.

Ограничения: только whole-model таблицы с параметрами по умолчанию; варианты параметров РСН/таблиц не перечислены исчерпывающе; сохранённые таблицы не копируются отдельно; полные записи нагрузок, .sld и другие бинарные разделы не декодированы. RES export и связь результатов с hash модели ещё не реализованы. full_information_extracted/results_exported/acceptance_granted=false, solver=NOT_RUN. Реальная выгрузка пользовательского LIR и её полнота ещё не проверены. №6 остаётся 🟡; план 8 ✅ / 8 🟡 / 3 ❌.

Дальше: проверить первый реальный export; исправить COM/параметры при необходимости; сверить таблицы/единицы/ключи с исходными TXT и данными модели; реализовать отсутствующие варианты и отдельный RES export; после фактической проверки подключить общий Windows-обработчик к upload pipeline сайта. Запрос «вся информация файла» пока не закрыт.

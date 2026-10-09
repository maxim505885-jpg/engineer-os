# MASTER PLAN — ENGINEER OS

Единая нумерация: **19 пунктов**. Эта сводка заменяет противоречащие текущие статусы планов17/19; история сохранена в `master-plan-17-history.md`, `master-plan-19-history.md` и живой карте. Результат нельзя переносить между планами по номеру без названия и критерия.

**Активный план:** §73. PR97 опубликован, CI выполняется; кандидатf2a58399 остаётся до успешных checks. Полный147MB DOCX14678/14678,0failed/truncated,7022BLOCK; layout/графика/полнота не приняты. План8✅/8🟡/3❌.

| № | Этап | Статус | Проверенный результат и оставшийся критерий |
|---|---|---|---|
| 1 | Единая рабочая версия | ✅ Кандидат | PR 91/92/93/94/95/96 приняты; кандидат f2a58399, проверенное дерево 2ab64d8c. |
| 2 | Качество OCR и локальной модели | ✅ программный контур | Извлечение/метрики/отрицательные gates и живой Linux qwen3 проверялись. Это не полнота V4 и не Windows. |
| 3 | Большие документы: resume/recovery | ✅ программный контур | Checkpoints, identity, budgets, retry. Полнота инженерного документа отдельно в№13. |
| 4 | DOCX/XLSX/DOC и остальные заявленные форматы | ✅ программный контур | Оригиналы, logical locators, provenance, native/OCR маршруты; сложные таблицы отдельно. |
| 5 | ТЗ → источник → требование → вывод | ✅ программный контур | Полный индекс47 требований,42 исходные позиции, версионные оценки и глобальные gates. |
| 6 | Нормативная и расчётная верификация | 🟡 | 12 документальных нормативных решений BLOCK; native LIR identity/receipt integrity готовы. Семантический vendor export/run, полномочия и actual correlation открыты; реальный solver-run не выполнен без подтверждённого semantic export/run. |
| 7 | Реальный инженерный case workflow | ✅ отрицательный сценарий | Три оригинала,36 кандидатов, роли и нормативный replay воспроизводимы; объект не ACCEPTED. Положительный сценарий в№14. |
| 8 | FINAL AUDIT / acceptance boundary | ✅ программный контур | Immutable/stale/tamper/foreign source gates. Нет подтверждённого положительного инженерного объекта. |
| 9 | Windows one-click runtime | 🟡 | Native Windows CI полностью PASS: clean start/cache repair/restart, 23 tests, live Ollama, 4 Chromium routes. Physical PC clean install/reboot остаётся. |
| 10 | Консолидация и источник истины | ✅ Интеграция | PR 91/92/93/94/95/96 merged; 9 CI SUCCESS, §72.1. |
| 11 | Интерфейс и пользовательский маршрут | 🟡 интеграция | Дизайн кандидата сохранён вместе с формами источников/ТЗ/ролей/черновиков. Все4 browser маршрута, включая CAD/memory/mobile/session reset, прошли. Финальная приёмка интерфейса на реальном accepted объекте остаётся. |
| 12 | Backup/restore/recovery/security | 🟡 интеграция | Один bounded engine, чтение двух форматов, SHA256/SQLite/no-replace/key/derived/settings. Совместимость двух форматов проверена; воспроизведённые symlink/hardlink внутреннего DB/lock/settings/key устранены. Core/Security CI PASS; CodeQL 29 alerts individually reviewed/dismissed FP,checkSUCCESS; физический Windows NOT_RUN. |
| 13 | Производственная полнота документов | ❌ | Office 665/665; Word equations/merge declarations и XLSX ranges/formula presence сохранены. Rendered tables/formulas/графика, числовой OCR, полный V4 и qualified ground truth открыты. |
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

# MASTER PLAN — ENGINEER OS

Единая нумерация: **19 пунктов**. Эта сводка заменяет противоречащие текущие статусы планов17/19; история сохранена в `master-plan-17-history.md`, `master-plan-19-history.md` и живой карте. Результат нельзя переносить между планами по номеру без названия и критерия.

**Активный план:** расчёты отложены. №13: PR108 native tail fix и fullV4 render/OCR gap inventory;local857 PASS;real Store resume/Word render/CI выполняются (§92). Кандидат6d59ea1;qualified полнота ещё не подтверждена;8✅/8🟡/3❌.

| № | Этап | Статус | Проверенный результат и оставшийся критерий |
|---|---|---|---|
| 1 | Единая рабочая версия | ✅ Кандидат | PR 91–98 приняты; кандидат 9a92b96e, проверенное дерево 2c36ea30; итог §74.1. |
| 2 | Качество OCR и локальной модели | ✅ программный контур | Извлечение/метрики/отрицательные gates и живой Linux qwen3 проверялись. Это не полнота V4 и не Windows. |
| 3 | Большие документы: resume/recovery | ✅ программный контур | Checkpoints, identity, budgets, retry. Полнота инженерного документа отдельно в№13. |
| 4 | DOCX/XLSX/DOC и остальные заявленные форматы | ✅ программный контур | Оригиналы, logical locators, provenance, native/OCR маршруты; сложные таблицы отдельно. |
| 5 | ТЗ → источник → требование → вывод | ✅ программный контур | Полный индекс47 требований,42 исходные позиции, версионные оценки и глобальные gates. |
| 6 | Нормативная и расчётная верификация | 🟡 Частично | Расчётная часть отложена пользователем09.10.2026. Native input ZIP в кандидате PR101; R4 helper PR102 отдельно, real RES/KE57/нагрузки/полные сочетания/model→run/нормы открыты; §§85–87. |
| 7 | Реальный инженерный case workflow | ✅ отрицательный сценарий | Три оригинала,36 кандидатов, роли и нормативный replay воспроизводимы; объект не ACCEPTED. Положительный сценарий в№14. |
| 8 | FINAL AUDIT / acceptance boundary | ✅ программный контур | Immutable/stale/tamper/foreign source gates. Нет подтверждённого положительного инженерного объекта. |
| 9 | Windows one-click runtime | 🟡 | Native Windows CI PASS: cold/repeat/restart,49 tests,live Ollama и5 Chromium workflows (§91 итог). Physical PC clean install/reboot остаётся. |
| 10 | Консолидация и источник истины | ✅ Интеграция | PR 91–98 merged; все 9 CI SUCCESS, итог §74.1. |
| 11 | Интерфейс и пользовательский маршрут | 🟡 интеграция | Дизайн кандидата сохранён вместе с формами источников/ТЗ/ролей/черновиков.5 browser workflows включая CAD/memory/mobile/session иsource images/native EMF text/embedded raster PASS (§90 итог). Приёмка UI на реальном accepted объекте остаётся. |
| 12 | Backup/restore/recovery/security | 🟡 интеграция | Один bounded engine, чтение двух форматов, SHA256/SQLite/no-replace/key/derived/settings. Совместимость двух форматов проверена; воспроизведённые symlink/hardlink внутреннего DB/lock/settings/key устранены. Core/Security CI PASS; CodeQL 29 alerts individually reviewed/dismissed FP,checkSUCCESS; физический Windows NOT_RUN. |
| 13 | Производственная полнота документов | ❌ Открыто | PR108: native tail loss исправлен;V4 all534 render/40OCR gaps записаны. Real Store resume/Word rendering/CI выполняются;qualified table/formula/graphics/OCR corpus не подтверждён (§92). |
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
| 9 | Windows one-click runtime | 🟡 | Native Windows CI PASS: cold/repeat/restart,49 tests,live Ollama и5 Chromium workflows (§91 итог). Physical PC clean install/reboot остаётся. |
| 10 | 16 | PR 91–98 merged; все 9 CI SUCCESS, итог §74.1. |
| 11 | Интерфейс и пользовательский маршрут | 🟡 интеграция | Дизайн кандидата сохранён вместе с формами источников/ТЗ/ролей/черновиков.5 browser workflows включая CAD/memory/mobile/session иsource images/native EMF text/embedded raster PASS (§90 итог). Приёмка UI на реальном accepted объекте остаётся. |
| 12 | 14 | Принятый кейс |
| 13 | Производственная полнота документов | ❌ Открыто | PR108: native tail loss исправлен;V4 all534 render/40OCR gaps записаны. Real Store resume/Word rendering/CI выполняются;qualified table/formula/graphics/OCR corpus не подтверждён (§92). |
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


## 82. Первый реальный COM запуск: модель открыта, 0 таблиц; исправление V2 — 09.10.2026

Получен `ENGINEER_OS_LIRA_EXPORT_f42ba4e4bbdc41a7a0ca27c64f19495b.zip` (6840 bytes, только manifest.json68996 bytes). Исходник пользователя `секция 2 прогибы.lir`,16 266 163 bytes,SHA256 `34a24bc30f744476a35da42e3e18dd015953ed27dfd40e2a2ebb5a6aef4408d8`. COM activation и OpenDocument на реальной ЛИРА2024 прошли: title=секция2прогибы, system_label=5,current_load_case=1; прочитаны коды единиц приложения, existing_table_count=0. По manifest original_unchanged=true, owned_document_closed=true, solver=NOT_RUN.

Все31 таблицы получили «Несовпадение типов»; выгружено0 TSV. Статус V1 PARTIAL_MODEL_TABLE_EXPORT был некорректен для нулевого результата. Точный этап ошибки V1 не записывался, поэтому нельзя объявлять точную причину установленной или модель повреждённой.

Обоснованная гипотеза: передача Pars как null вместо пропущенного optional COM VARIANT и/или PowerShell by-reference marshalling. V2 добавляет `com-bridge.cs`: Reflection.InvokeMember с Missing.Value (VT_ERROR/DISP_E_PARAMNOTFOUND), явный ParameterModifier для GetContents/GetParameters. Прежний успешный OpenDocument не менялся. Записываются error_stage и HRESULT каждой ошибки. При0 таблиц теперь TABLE_EXPORT_FAILED, а не partial success. Никаких SetContents/Apply/Save/solver/result вызовов; source-copy guard и hash сохраняются.

Regression сначала FAIL на Windows run37947731826: «optional VARIANT produced no tables» (fixture воспроизводит отличие null и Missing; это не доказательство внутренней причины реальной ЛИРА). После исправления head `43d4c5b70f15b955876565676683852914d9caee`, Windows run37947898558/job113878839083 SUCCESS. Проверены Missing/ref object, большой TSV,0-table failure,stage/HRESULT,hash/copy/close и реальное представление Missing в native VARIANT: VT_ERROR+DISP_E_PARAMNOTFOUND. Security37947898569 SUCCESS. Реальный LIRA runtime повторно не запускался; устранение ошибки на пользовательском файле ещё НЕ подтверждено.

Подготовлен `ENGINEER_OS_LIRA_NATIVE_EXPORT_V2.zip` (6 файлов, включая com-bridge.cs). Пользователю: распаковать в новую папку, START.cmd, выбрать тот же .lir, прислать новый export ZIP. Повторять API inventory не требуется. PR100 остаётся draft, сайт/кандидат PR99 не изменён этой утилитой; №6 🟡, план8✅/8🟡/3❌, full_information_extracted/results_exported/acceptance=false.

Следующее действие: получить реальный V2 export и проверить таблицы/ошибки/хеши; затем полноту исходных данных, отдельный RES export, грунт и подключение Windows reader к сайту. Запрос всей информации пока открыт.


## 83. V2: таблицы созданы, сбой GetContents; V3 подтверждён native COM regression — 09.10.2026

Получен `ENGINEER_OS_LIRA_EXPORT_4d0b9481c2b74590bd0555d1be66b738.zip`:7075 bytes,SHA256 `ada0f97ed88aa1f4295867a15a9ef5f6f75e8ebe9d686ba10bde345c94d3fe98`, внутри только manifest76770 bytes. Тот же source LIR секция2:16 266 163 bytes,SHA25634a24bc30f744476a35da42e3e18dd015953ed27dfd40e2a2ebb5a6aef4408d8. Модель открыта, все31 CreateNewItem прошли и свойства Type/InitialModelPart проверены; все31 ошибки теперь точно на GET_CONTENTS, HRESULT0x80020005. Значит V2 устранён/обойдён сбой создания таблиц, но данных ещё0. TABLE_EXPORT_FAILED корректен; original_unchanged/owned_document_closed=true; solver/results NOT_RUN/false.

Воспроизведение выполнено через настоящую unmanaged границу IDispatch: test-native-dispatch.cs создаёт native vtable и проверяет VARIANTARG реального InvokeMember. V2 реально передаёт VT_BSTR|VT_BYREF (0x4008); GetContents ожидает ref VARIANT (инвентарь описывает pData как VARIANT). Тест на Windows run37948754157 получил ожидаемый FAIL: native GetContents received VT=0x4008 и0x80020005. Прежний managed-only fixture эту ошибку не обнаруживал; недостаток тестового покрытия устранён. Ранняя ошибка компиляции теста из-за неоднозначного DISPPARAMS исправлена явным ComTypes alias перед воспроизведением.

V3 минимально меняет ReadReference: VariantWrapper(initial)+ParameterModifier, результат разворачивается при необходимости. CreateNewItem/OpenDocument не менялись. VariantWrapper предназначен именно для VT_VARIANT|VT_BYREF через InvokeMember: https://learn.microsoft.com/en-us/dotnet/api/system.runtime.interopservices.variantwrapper?view=netframework-4.8.1 . Это подтверждённая ошибка COM транспорта экспортёра; успешное чтение пользовательской ЛИРА всё равно проверяется следующим фактическим запуском.

Проверенный head `2fe90734fa064bf1234827e816c63d4663075204`; Windows run37948917501/job113882318826 SUCCESS. Native GetContents принял0x400C и вернул TSV; existing optional/ref/нулевой статус/этап/HRESULT/source hash/копия/закрытие/>100k TSV регрессии PASS. Probe compilation+real stdole2.tlb PASS. Security37948917504 SUCCESS. Native fixture не содержит ЛИРА/её модель/результаты: подтверждён механизм COM marshalling, а не вся выгрузка .lir.

Подготовлен `ENGINEER_OS_LIRA_NATIVE_EXPORT_V3.zip`,6 runtime файлов (START.cmd,EXPORT.ps1,module,com-bridge.cs,contract,README); тестовый native vtable код в дистрибутив не входит. Пользователю: распаковать в новую папку,START.cmd,тот же .lir,вернуть export ZIP. Переустановка ЛИРА/API inventory не нужны.

№6 остаётся🟡; план8✅/8🟡/3❌. PR100 draft; кандидат PR99 и сайт без native integration. Полные нагрузки/parameter-dependent варианты/soil/RES и корреляция с расчётом ещё открыты. Следующий шаг — проверить реальный V3 TSV, его полноту/ключи/единицы/соответствие источникам; затем завершить недостающий export и подключить проверенный reader к сайту. Acceptance=false.

## 84. Реальная V3 выгрузка секции2: 31 таблица прочитана, полнота остаётся открытой — 09.10.2026

Получен ENGINEER_OS_LIRA_EXPORT_c099d41396484fd9a9227714961bd1ae.zip; SHA256 70f2c2932bab9e2fcac854351831a7f8cb4f6623980e8e6d8ddcc767cd3787f3. В архиве32 записи (manifest+31 TSV),8 843 076 распакованных bytes. ZIP CRC, полное UTF-8 декодирование и SHA256 всех31 TSV проверены: PASS. Source секция 2 прогибы.lir:16 266 163 bytes,SHA25634a24bc30f744476a35da42e3e18dd015953ed27dfd40e2a2ebb5a6aef4408d8. Реальный GetContents теперь подтверждён на пользовательской ЛИРА2024; V3 транспорт исправлен.

Извлечено37 083 узла,44 086 КЭ (10:4594;44:29419;42:6758;57:3315),22 обычные жёсткости,16 именованных загружений,346 жёстких тел,5 групп объединённых степеней свободы,248 конструктивных блоков,15 осей,20 отметок. ID узлов/КЭ уникальны, недействительных узловых ссылок0. Сверка с исходным TXT SHA256880410cbb166561fa2867f626084b62a7b926cb3daba561180d9338465307c34: количества/типы/связи совпали полностью; максимальная разница координат5.000000001587068e-6м соответствует округлению TXT. Обычные назначения жёсткостей совпали.

Ограничение полноты: все3315 КЭ57 в default API table10 имеют stiffnessID0, тогда как TXT содержит отдельные auxiliary stiffness IDs23+. Table9 выдаёт только1–22. Это подтверждённый пробел данного способа извлечения, НЕ установленный дефект модели и НЕ вывод о3315 неработающих опорах. Нужен отдельный маршрут для auxiliary stiffness/soil. GetParameters недоступен для типов2,3,8,22,23, но GetContents прочитан. Пустые TSV7,8,20,21,23,26 не доказывают отсутствия соответствующих данных во всём LIR. Default DCL и имена загружений не заменяют полные нагрузки/все сочетания; таблица материалов с пустыми полями не доказывает отсутствие материалов (параметры имеются в жёсткостях).

Manifest заявляет original_unchanged/owned_document_closed=true; это сведения экспортёра, не независимое наблюдение Windows. solver NOT_RUN, results_exported/full_information_extracted/acceptance=false. Перемещения/усилия/реакции/армирование/завершённый расчёт не выгружены. Native TSV ZIP ещё НЕ интерпретируется текущим сайтом; ZIP inventory не равен интеграции native reader.

CI head2fe90734fa064bf1234827e816c63d4663075204: Core37948917618,Security37948917504,LIRA API37948917501 — completed/success. PR100 остаётся draft; кандидат PR99 без изменений. №6 🟡, общий план8✅/8🟡/3❌. Закрыт подэтап «реальная выгрузка31 default таблиц и сверка геометрии», а не весь native LIR/расчётный критерий.

Следующие действия: (1) подключить проверку manifest/hash/TSV и наблюдения к сайту; (2) извлечь auxiliary KE57, полные нагрузки и parameter-dependent сочетания; (3) отдельный RES export с привязкой к исходной модели и завершённому расчёту; (4) инженерная/нормативная проверка полноты. Повторная V3 выгрузка секции2 не требуется.

## 85. Native TSV ZIP подключён к загрузчику приложения — 09.10.2026

Ветка feat/lira-native-upload-reader-20261009, PR101 https://github.com/maxim505885-jpg/engineer-os/pull/101, проверенный head4410878aef76d48495398086f40e822c4bbe7349; merged candidate f8746896d9731011fc0cf65ca6b6ee58841e6f40. Три файла: engineering/calculation/native_tables.py, upload_analysis.py, tests/test_lira_native_tables.py. Опубликованные файлы прочитаны обратно, точное совпадение PASS. Ветка создана от кандидата8009b937; helper PR100 не включён.

Существующий analyze_upload/extract_preview/preserve_file теперь распознаёт schema2 ENGINEER_OS_LIRA_MODEL_TABLE_EXPORT ZIP, проверяет inventory/type/scope/file/bytes/SHA256/UTF-8/unique IDs/finite coordinates, сохраняет отчёт таблиц и русскую заметку. Обычные ZIP сохраняют прежнее поведение и path/encryption/expansion/recursion limits. Некорректный native пакет не получает числовую сводку. Отдельно отражены empty/failed/parameter-unavailable таблицы; нулевой экспорт не выдаёт успешную проверку хешей. Source LIR hash остаётся claim: оригинал отдельно не сверялся. Никакие флаги manifest не дают full_information/results/engineering/acceptance=true. KE57 omission назван ограничением извлечения, не дефектом.

Реальный архив §84 прошёл именно через путь вложения приложения:31 таблица,37 083 узла,44 086 КЭ,16 загружений,3315 KE57 auxiliary stiffness не извлечены; все хеши PASS. Пример результата пользователю: «ЛИРА: проверено таблиц31. Узлов:37083; КЭ:44086; загружений:16. Жёсткости КЭ57 не извлечены:3315; это ограничение выгрузки. Полные нагрузки, сочетания и результаты расчёта не подтверждены».

RED: существующий reader не распознавал native package; затем persistence и zero-table/hash tests воспроизвели отдельные FAIL. GREEN:35 focused tests PASS (13 новых+22 прежних). Полная финальная локальная регрессия805 tests/66.210с OK,17 skipped из-за условий окружения; это не Windows live run. Architecture guard, compilation,diff checks PASS;7 Node dashboard tests PASS. Локальный DOM smoke не запущен: jsdom не установлен, повтор с runtime NODE_PATH также подтвердил отсутствие зависимости; DOM/HTTP/Chromium проверяются в CI с lockfile dependencies.

Финальный CI head4410878aef76d48495398086f40e822c4bbe7349: Security37951932042 и Core37951931844 SUCCESS. Core job113892643228:805 tests/91.565с OK,2 Windows-only skipped; DOM/HTTP и Chromium SUCCESS. Прежние проверки раннего head не используются как proof финального кода. PR101 MERGED (expected_head guard), candidate f8746896d9731011fc0cf65ca6b6ee58841e6f40. Независимый review завершён без оставшихся важных замечаний. Пользовательский установленный экземпляр Windows не обновлялся. №6 остаётся🟡;8✅/8🟡/3❌. Закрыт подэтап реализации приёма native TSV ZIP; полные нагрузки/сочетания, auxiliary KE57/soil, RES и инженерная верификация всё ещё открыты.

Review исправления подтверждены RED→GREEN: actual UNAVAILABLE/NOT_ATTEMPTED статусы совместимы; native проверка выполняется до generic member sniffing (invalid package не сохраняет детские числовые наблюдения); UTF-8 TSV читается потоком, до split ограничены200000 строк/1024 колонки/65536 символов строки, общий бюджет10000000 ячеек. Реальный ZIP содержит2302572 ячейки, max1002 колонки и1078 символов строки: PASS. 5MiB delimiter/newline bombs отклоняются, peak tracemalloc0.14/13.77MiB. Повторная финальная загрузка пользовательского ZIP и сохранение отчёта PASS. Осталось: auxiliary KE57/soil, полные нагрузки/parameter-dependent сочетания, RES и связь model→completed run, инженерная/нормативная проверка. Для следующего чата: native ZIP import уже готов в кандидате; не просить повторно V3 секции2 и не повторять этап transport/debug.

## 86. R4: выгрузка основных сохранённых результатов — 09.10.2026

Создан самостоятельный Windows экспортёр в tools/lira-native-export: RESULTS.ps1/cmd, results-package.psm1, results-reader.cs, results-contract.json и RESULTS_README.md. Ветка feat/lira-results-export-20261009; draft PR102 https://github.com/maxim505885-jpg/engineer-os/pull/102, head b623bc3abd58adbf46432fbc4e3adb96d647235c. PR102 основан на helper PR100; не объединён в кандидат. Кандидат приложения остаётся f8746896d9731011fc0cf65ca6b6ee58841e6f40 (§85).

R4 получает реальные sparse ID из таблиц2/3 приватной копии, затем обращается к установленному RES API2024 по имени задачи. Потоком сохраняет основные LC перемещения/усилия, результатные нагрузки на фрагмент/продавливание, доступные модальные массивы. Контекст shape0/history0/SuperElement0; actual LoadCase.Number и сечения1..count. Для РСН/РСУ/армирования — только доступность, не полный числовой экспорт. Все10 типов запросов отражаются в сводке. Ошибочный scalar остаётся UNAVAILABLE с HRESULT, не нулём. Пустые ID не дают запросов с неопределённым селектором.

Source hash сверяется до/после; solver NOT_RUN, Save оригинала не вызывается. full_information_extracted/source_result_binding_verified/completed_solver_run_verified/engineering_verified/acceptance_granted=false. Имя и совпавшие количества не доказывают model→results→completed run. Нагрузки фрагмента — не исходные приложенные нагрузки. Histories/other shapes/superelements/полные сочетания/армирование/auxiliary KE57/soil остаются открытыми.

Лимит50M scalar attempts; MaxBytes — TSV_ONLY (default1GiB/max2GiB). R4 отдельно ограничивает source512MiB, одну таблицу128MiB, все таблицы512MiB, входной manifest16MiB. Для копии+таблиц+TSV+ZIP предусмотрено6GiB свободного места. Только локальный OutputRoot; UNC явно отклоняется. Ошибка COM activation создаёт RESULT_ERROR.json. Сводка и part_*.zip сохраняют хеши/статусы/контекст; counts_scope=WHOLE_RUN_NOT_PART.

RED до реализации reader/package подтверждён Windows CI; отдельный packaging FAIL выявил обнуление Application, исправлено. Независимый review важных оставшихся замечаний не нашёл; замечание UNC закрыто явным ограничением и инструкцией. Финальный Windows37962746217/job113929426018 SUCCESS: C# compile, прежний native IDispatch input test, managed RES fixtures, sparse IDs/реальные LC/аргументы/scalar errors, лимиты, полный ZIP маршрут/хеши/исходник/диагноз без результатов и при отсутствии приложения. Security37962746141 SUCCESS. Core37962746150 на момент записи выполняется; итог ранних head не подменяет проверку финального. Это тесты с fixtures, не реальный RES run ЛИРА.

Доставка ENGINEER_OS_LIRA_RESULTS_R4.zip:9 runtime файлов,28647 bytes,SHA2569822b42026b08ebe189e63116b1cec97b7f7d23fbaf76d08b6555015a3443713; CRC и точное совпадение содержимого PASS. START.cmd в архиве соответствует RESULTS.cmd; V3 launcher в репозитории сохранён. Все10 опубликованных runtime/test/readme файлов совпадают с локальными bytes. Архив сохранён как libfile_f4a5b33913408191861b6596fd131458.

Следующее действие пользователя: открыть в ЛИРА секция2 прогибы с сохранёнными результатами, распаковать R4, START.cmd, выбрать тот же LIR; прислать RESULT_SUMMARY.json и все part_*.zip либо RESULT_ERROR.json. Повторно присылать прежний V3 ZIP не требуется. Установленная ЛИРА доступна только на пользовательском ПК; реальный RES экспорт ещё НЕ получен. Сайт пока НЕ интерпретирует новый result ZIP: реализован только native input ZIP §85. Следующий этап — проверка реальных RES данных, их безопасный приём сайтом и связь model→completed run; затем полные нагрузки/сочетания/KE57/нормативная семантика. №6🟡, общий план8✅/8🟡/3❌.

## 87. Расчёты отложены; №13 — колонтитулы и сноски DOCX — 09.10.2026

По указанию пользователя от20:09:58 Europe/Moscow расчёты/ЛИРА/RES отложены. Запуск R4 сейчас не требуется. Следующий приоритет действующего MASTER PLAN — №13, производственная полнота документов. R4 PR102 остаётся отдельным draft, не объединён с приложением; все три финальных проверки его head b623bc3 (Windows37962746217,Security37962746141,Core37962746150) теперь SUCCESS, но это не реальная ЛИРА.

Ветка feat/document-coverage-next-20261009 от кандидата f8746896, PR103 https://github.com/maxim505885-jpg/engineer-os/pull/103, head3d480c6022220e0a18f2415a54fedeb823491451. DOCX reader теперь читает native текст header/footer/footnotes/endnotes, таблицы и OMML syntax, сохраняет part/component/лексический note_id/type. Основная часть читается прежним алгоритмом. Части обнаруживаются по стандартным именам и внутренним document relationships, включая нестандартные пути. Внешние/отсутствующие связи явно оставляют HEADERS_FOOTNOTES_NOT_READ; сетевые обращения не выполняются. Неправильный XML/root/конфликт идентичности/дубликаты числового ID (7/007) отвергаются.

Границы: максимум128 вспомогательных частей/связей, прежние XML/expanded/text/unit budgets; новая граница включена в parser identity, старые checkpoints не принимаются как новый parser. Scope PACKAGE_PART_PLACEMENT_UNVERIFIED, физические страницы/место применения колонтитула/связь сноски с текстом не придуманы. DRAWING_NOT_READ/FIELD_NOT_EVALUATED/EQUATION_NOT_READ и запреты completeness/acceptance сохранены. Manifest tables разделены по part/note/table; UI кнопки источников и таблицы показывают различимую часть и номер примечания. Это приём содержимого пакета, не утверждение о прочитанной странице или инженерное принятие.

Реальный исходный отчёт «15.09.2026 ТЗК БЦ ул. Набережная28А на диск(1).docx»:147210288 bytes,SHA256b253439bdd673a775eaf209ca7d398d766efae5f4a18ac33fa6679f7faae28a5 неизменён. Новый reader сохраняет14678 прежних logical units и добавляет6: два колонтитула с34+62=96 native w:t tokens, четыре пустых служебных separator/continuationSeparator в footnotes/endnotes (IDs-1/0). Итого14684. Независимый ZIP/XML проход подтвердил сохранение всех native tokens четырёх частей; nonempty units2. Это проверка реального reader, а не полный новый Store/model run большого отчёта. Сквозной Store/Worker/model/receipt/original/no-acceptance маршрут подтверждён контролируемым DOCX fixture.

Тесты сначала воспроизвели отсутствие содержимого/пропуск unsafe auxiliary XML; review выявил nonstandard target без предупреждения и одинаковые UI подписи, обе ошибки подтверждены RED→GREEN. Числовые alias ID также подтверждены RED→GREEN. После всех исправлений36 focused Python,8 Node tests,architecture guard,compileall,JS syntax,diff checks PASS. Финальный полный локальный run813 tests/68.819s OK,17 skips по окружению; это не native Windows. Локальный DOM попытался запуститься и не прошёл из-за отсутствующего jsdom; DOM/HTTP/Chromium и Windows проверяются в CI. Пять опубликованных файлов прочитаны через git и byte-identical локальным:PASS. CI финального head: Security37965442777 SUCCESS; Core37965442708 и Windows37965442627 на момент записи выполняются. PR103 пока не объединён.

№13 остаётся❌ по критерию полной производственной верификации, хотя подэтап auxiliary native extraction готов. План8✅/8🟡/3❌. Следующие пробелы: rendering/графика/растровые и mixed таблицы, визуальная проверка формул без запуска расчётов, покрытие полного V4/представительный корпус и квалифицированная сверка. №6/14 расчётные доказательства отложены; не просить сейчас R4/ЛИРА и не возвращаться к transport debug.

### Итог §87 — включено в кандидат

Все финальные CI head3d480c6022220e0a18f2415a54fedeb823491451 SUCCESS: Core37965442708/job113938516701 —813 tests/150.721s OK,2 Windows-only skips,8 Node tests, HTTP/DOM и4 Chromium маршрута; Windows37965442627/job113938516379 —23 tests/7.128s OK, cold/repeat/restart, real Ollama qwen3:0.6b inference и4 browser routes; Security37965442777 PASS. Локальный отсутствующий jsdom не заменён предположением: DOM проверен именно CI с locked dependencies. Independent Important fixes подтверждены RED→GREEN и полным зелёным финальным suite; deferred minors нет.

PR103 MERGED squash с expected_head guard: кандидат3bfba1edc54f38bacc7ac696beec0feab5c41a5b. Полное дерево кандидата точно совпало с проверенным локальным деревом; интерфейсные подписи и auxiliary reader включены в общую версию. Это не обновление установленного приложения на пользовательском ПК. Полная производственная верификация №13 не закрыта: графика/fields/rendering/mixed-raster таблицы/V4/qualified corpus остаются. Расчётная работа отложена, R4 сейчас запускать не требуется. План8✅/8🟡/3❌. Следующая работа — графическое содержимое документов и проверка покрытия, без возобновления ЛИРА.

## 88. №13: source-linked изображения DOCX и безопасный просмотр — 09.10.2026

Расчёты/ЛИРА/RES остаются отложенными. Ветка feat/docx-image-sources-20261009 от кандидата3bfba1ed, PR104 https://github.com/maxim505885-jpg/engineer-os/pull/104; опубликованный head6fc1e34de36abe969a35e41255d640b768e53941, tree d279258eff146113934f2dd538ce266b139cd381 точно совпадает с проверенным локальным деревом. На момент записи PR OPEN, кандидат не изменён; Security37968999726 SUCCESS, Core37968999520/Windows37968999638 выполняются.

Reader связывает DrawingML blip и VML r:id/o:relid с содержащим абзацем/ячейкой и точной частью DOCX, включая auxiliary parts и нестандартные пути. Сохраняются relationship ID, image ordinal, asset part/bytes/SHA256, native declared labels; существующие номера логических элементов не сдвигаются. Внешние/отсутствующие/не-image связи явно UNAVAILABLE; сеть не вызывается. Неоднозначные ID/unsafe URI/конфликт VML identities отвергаются. Поддерживаемый ID — bounded ASCII NCName subset; необычные Unicode IDs fail-closed. Лимиты4096 refs,32MiB/asset,256MiB unique assets и прежние package/XML/text budgets входят в parser identity вместе с hash нового word_images.py.

В результатах по частям доступны кнопки изображений. Authenticated preview перепроверяет session/job/original/parser/exact checkpoint/asset hash, выдаёт bounded PNG<=1600px/10MiB; прозрачность сохраняется. Показывается исходный raster payload, НЕ отрисованная страница Word: crop/rotation/placement/effects не применены, page/note placement и содержимое не подтверждены. EMF/vector/invalid/oversized previews явно недоступны. DRAWING_NOT_READ/FIELD_NOT_EVALUATED/EQUATION_NOT_READ и запреты completeness/acceptance сохранены. Метаданные ссылок не выдаются за OCR или изображение, рассмотренное моделью.

Реальный исходник147210288 bytes/SHAb253439bdd673a775eaf209ca7d398d766efae5f4a18ac33fa6679f7faae28a5 неизменён.14684 logical units сохранены;510 units содержат671 refs к631 distinct assets. Независимый XML count —671. По ссылкам397 PNG+116 JPEG+9 JPG+149 EMF; это подсчёт форматов/связей, не полнота графики. На текущем коде первые2 элемента реального оригинала прошли Store extraction/checkpoint/revalidation/PNG preview; processed2/14684,cycle_complete=false,model NOT_RUN. Полный новый Store/model run большого отчёта не выполнялся.

RED→GREEN воспроизвёл прежнюю потерю refs/HTTP404/отсутствие UI; review findings malformed IDs/URI,legacy VML,equation sibling association и alpha loss устранены отдельными воспроизведениями. Independent review: Critical/Important нет; minor Unicode-ID исправлен explicit supported subset. Финальный локальный suite825 tests/64.290s OK,17 environment skips;12 новых focused,9 Node,2 HTTP/DOM и5 Chromium routes PASS;architecture/compile/JS/diff PASS. Публичное дерево получено обратно git fetch и совпало по полному tree SHA. Это не обновление приложения на ПК пользователя.

№13 остаётся❌; общий план8✅/8🟡/3❌. Следующий конкретный шаг — source-bound чтение/отрисовка EMF и проверка визуального соответствия графики/формул, затем raster/mixed tables/OCR-conflicts, V4 и qualified corpus. Расчёты сейчас не требуются. QA:docs/qa/2026-10-09-docx-image-sources.md.

### Итог §88 — включено в кандидат

PR104 MERGED squash с expected_head guard; кандидат8274587137754a4df56dd537fd148d90ade8f40f. Полное дерево d279258eff146113934f2dd538ce266b139cd381 совпало с проверенным локальным и опубликованным head6fc1e34d. Все три final-head CI SUCCESS: Core37968999520/job113950507929 —825 tests/94.369s OK,2 Windows-only skips,9 Node,2 HTTP/DOM и5 Chromium маршрутов; Windows37968999638/job113950508285 —23 tests/8.002s OK,cold/repeat/restart,real Ollama qwen3:0.6b и5 browser маршрутов,включая DOCX source image; Security37968999726 SUCCESS. Программный CI не заменяет physical PC/qualified engineering review.

Финальная ограниченная Store/checkpoint/preview проверка первых2 элементов реального DOCX повторена именно финальным parser:2/14684,cycle_complete=false,model NOT_RUN;SHA оригинала неизменён. PNG1:658216 bytes/SHAea20aba0fb422ae21f68d36637d19716e0cfeb9fa004c1d493cbd8fcd0ae283a;PNG2:6823 bytes/SHA44b5bc8048dfea1843f6a9abcf7771bb9665d39ee1481c408ae6d4062a5b4a17. Alpha сохранён. Новый полный Store/model run большого отчёта не заявляется. Физические страницы/crops/transforms/содержание/EMF/V4/полный корпус не подтверждены.

Закрыт только подэтап source association+raster preview; №13 остаётся❌,план8✅/8🟡/3❌. На ПК пользователя версия не обновлялась. Следующий шаг — проверенное чтение/отрисовка EMF и визуальная сверка формул/графики, без возвращения к расчётам.


## 89. №13: native Unicode-записи EMF в DOCX — 09.10.2026

Расчёты ЛИРА/RES остаются отложенными по решению пользователя. Кандидат до этого шага8274587137754a4df56dd537fd148d90ade8f40f (PR104). PR105 https://github.com/maxim505885-jpg/engineer-os/pull/105, ветка feat/emf-source-preview-20261009, опубликованный head7533c6c46beda549f5f00b6173776a23a0ae6ee3; полное дерево24469b658b2bf3a3fd5888b13c30cc766cce13f7 совпадает с проверенным локальным деревом. На момент записи PR OPEN; Core37980537335/Windows37980537449/Security37980537379 выполняются, merge ещё не заявляется.

Добавлен pure Python reader EMR_EXTTEXTOUTW: literal UTF16-LE text/code units, record ordinal и byte offsets record/string/spacing, logical reference coordinates, graphics mode/options/scale. Точный image part и SHA сохранены в прежней DOCX привязке к абзацу/ячейке/auxiliary part. Glyph indices сохраняются отдельными числовыми кодами без выдуманного Unicode. Framing/header byte count/record count/EOF, bounds/alignment/string/spacing spans и strict Unicode проверяются; malformed/unsupported EMF остаётся bound original image, но native text явно UNAVAILABLE. Превышение ресурсного лимита прекращает чтение fail-closed. Лимиты100000 records/asset,10000 text records/asset,250000 UTF16 code units/asset,16MiB serialized native metadata по всем references плюс прежние image/package/text limits; hash reader и limits включены в parser identity.

UI результатов по частям показывает native текст с record offset; первые100 записей показаны явно, остальные сохранены в source locator. Физическая страница неизвестна. Full image locators остаются в receipts; inference refs содержат только компактную логическую идентичность/count, сами image payload/labels исключены. Unicode-текст передаётся модели только через обычный budgeted source text. Независимый review воспроизвёл обход лимитов через полный native_emf в refs: marker вне сохранённого текста попадал в model prompt. Regression RED→GREEN; повтор review подтвердил отсутствие marker во всех model calls, сохранение full receipt и уменьшение первого prompt34189→8406 chars. Финальный review: Critical/Important/Minor нет.

Реальный оригинал147210288 bytes/SHA b253439bdd673a775eaf209ca7d398d766efae5f4a18ac33fa6679f7faae28a5 неизменён;14684 logical units и671 image refs сохранены.138 distinct EMF assets содержат3357 Unicode records: независимая binary сверка raw UTF16 spans и record offsets совпала точно по всем assets.149 EMF references дают3394 referenced records с повторными использованиями assets. Это НЕ число восстановленных таблиц/доказательств. Первый native-text asset word/media/image300.emf находится в logical unit11451,569 text records; его label/number strings доступны reader. Полный новый Store/model run большого DOCX не выполнялся. Контролируемый DOCX прошёл Store/Worker/model/receipt и browser UI, сохраняет оригинал, physical page=None и acceptance=false.

Отдельный Linux QA Inkscape1.2.2 через network-denied doc_sandbox отрисовал image12.emf и image300.emf в1600px PNG. На image300 проверены отдельные видимые подписи «№ п/п», «КМ1-1-1», «19,64» против literal source records. Image12 содержит видимые подписи схемы при0 native text records — raster/vector glyph outlines этим reader не читаются. Отрисовка image300 имеет перекрытия текста и не сверена с оригинальной страницей Word; она не принята как визуальный эталон. Production EMF preview в приложении по-прежнему недоступен, Windows renderer не добавлен. Нет выводов о дефектах/армировании/расчётах: строки таблицы — только данные источника.

Локально837 Python tests/67.056s OK,17 environment skips;24 focused tests,10 Node,2 HTTP/DOM и5 Chromium маршрутов PASS. Последний browser маршрут проверяет одновременно source PNG и native EMF text/offset/limitations. Architecture guard/compile/JS/diff PASS. Windows workflow включает12 новых профильных native EMF tests без дополнительного renderer. CI ещё выполняется; физический ПК пользователя не обновлялся.

№13 остаётся❌: закрыт только программный подэтап literal native EMF text и bounded inference. Графика/rendering/font mapping/shaping/порядок чтения/placement, восстановление raster/mixed tables, визуальное соответствие формул, OCR conflicts, полный V4 и qualified corpus остаются открытыми. Общий план8✅/8🟡/3❌; №14 положительный ACCEPTED и №19 стабильный выпуск не объявлены. Следующий шаг — управляемый source-bound preview EMF и сверка визуального покрытия с реальным Word/PDF, затем raster/mixed tables; расчёты не требуются. QA:docs/qa/2026-10-09-docx-emf-native-text.md.


### Итог §89 — включено в кандидат

PR105 MERGED squash с expected_head guard7533c6c46beda549f5f00b6173776a23a0ae6ee3; кандидат01c86061e6d3f51f9d6c98c57beee7ee9ce6f524. Git fetch подтвердил точное полное tree совпадение24469b658b2bf3a3fd5888b13c30cc766cce13f7 с опубликованным/проверенным локальным кодом. Все final-head CI SUCCESS: Core37980537335/job113989610969 —837 tests/90.187s OK,2 Windows-only skips,10 Node,2 HTTP/DOM и5 Chromium маршрутов; Windows37980537449/job113989611233 —35 tests/9.451s OK (включая12 native EMF tests),cold/repeat/restart,real Ollama qwen3:0.6b inference и5 browser workflows; Security37980537379 SUCCESS. Последний browser workflow проверяет source PNG и native EMF text/byte offset/limitations на Windows и Linux. Это CI Windows runner, не пользовательский ПК.

Независимая реальная reader сверка138 EMF/3357 Unicode records выполнена без изменения исходного DOCX,14684 прежних логических элемента сохранены.3394 записи по повторным references не являются3394 уникальными фактами. Полный Store/model прогон большого отчёта не выполнен; standalone rendering двух real assets не заменяет app preview или полную визуальную сверку Word/PDF. Block/limitations по графике/таблицам/формулам не сняты. №13 остаётся❌;8✅/8🟡/3❌. На ПК пользователя обновление не выполнялось, инженерное принятие отсутствует. Далее — production source-bound EMF preview/rendering и visual coverage, затем raster/mixed tables/OCR conflicts/V4/qualified corpus; ЛИРА/RES отложены.


## 90. №13: исходные растры внутри EMF доступны в приложении — 09.10.2026

Кандидат до шага01c86061e6d3f51f9d6c98c57beee7ee9ce6f524. Расчёты ЛИРА/RES отложены. PR106 https://github.com/maxim505885-jpg/engineer-os/pull/106, ветка feat/emf-embedded-raster-20261009; head5951370b9aa11341f002ae8f48b1ab003d0ffa4f, tree54c6d29f95636df516df7c9edb66424ef21c7378 совпадает с проверенным локальным деревом и полученным git fetch. На момент записи PR OPEN; Security37986925016 SUCCESS, Core37986924886/Windows37986925006 выполняются. Merge пока не заявляется.

Reader обнаруживает embedded DIB в EMR_BITBLT(76)/EMR_STRETCHDIBITS(81) и сохраняет record ordinal/type/byte offsets, exact BMI/bits spans, dimensions/row orientation/bit depth/stride/ROP, SHA256(header+bits), status и ограничения. Поддержаны BITMAPINFOHEADER40,BI_RGB24/32,DIB_RGB_COLORS,без palette. Source-free raster operations не выдаются за изображения. Bounds/alignment/non-overlap/row bytes проверены; unsupported/malformed payloads явно UNAVAILABLE. Лимиты16M pixels/32MiB bitmap bytes/512 bitmap records плюс прежние package/image/reference/text budgets; implementation hash и limits входят в parser identity. Другие bitmap record kinds явно OTHER_BITMAP_RECORDS_NOT_DECODED.

Authenticated существующий images endpoint принимает положительный bitmap ordinal и повторно проверяет session/child source/original/parser/exact checkpoint/asset hash/descriptor/payload hash. Декодируется исходный BGR/BGRX растр, top-down/bottom-up и DWORD padding; резервный четвёртый байт32-bit BI_RGB не считается alpha. Preview PNG<=1600px/10MiB. UI предлагает «Растр EMF» и указывает record offset; unsupported bitmap показывает reason. Подпись прямо сообщает: полный EMF не отрисован, команды/crop/ROP/transform/compositing/Word placement не применены, содержание не подтверждено. Нет GDI execution, внешнего renderer, платного API, OCR или передачи пикселей модели; модель получает прежний budgeted source text/metadata и компактные inference refs.

Реальный исходник147210288 bytes/SHA b253439bdd673a775eaf209ca7d398d766efae5f4a18ac33fa6679f7faae28a5 неизменён. В138 EMF assets обнаружены120 bitmap sources:119 доступны, word/media/image465.emf явно UNSUPPORTED_DIB_HEADER;1530 source-free BITBLT operations не прибавлены к bitmap count. Все119 source pixel arrays совпали с независимым BMP-wrapper/Pillow BMP decoder по всем29880267 RGB pixels (сверка полного массива, без perceptual threshold). Это не visual ground truth всей страницы Word/PDF. Внутри контрольного процесса первые168 из14684 элементов оригинала прошли Store extraction/checkpoint; затем текущий source binder/PNG preview unit168, image12.emf/bitmap1 совпал с independently decoded792x395 source pixels. cycle_complete=false,model NOT_RUN,acceptance=false; PNG SHA250f5bcad4ccf091e8c1dcdf2fc7683394a2c6ac98b6633d7bc9bc8e685c56c4. Reload всего реального Store и полный model run не заявляются. Контролируемый mixed DOCX прошёл Store/Worker/model/receipt/authenticated HTTP/Chromium с явной неполнотой и без создания evidence.

Локально844 Python tests/64.855s OK,17 environment skips;31 focused tests,10 Node,2 HTTP/DOM и5 Chromium workflows PASS. Последний browser маршрут теперь проверяет и исходный PNG, и native EMF text, и embedded raster PNG с честной подписью. Windows CI включает7 bitmap tests. Architecture/compile/JS/diff PASS. Independent review: Critical/Important нет; minor coverage suggestions закрыты nonzero reserved byte/source-free/unaligned/unsupported header/byte-boundary/auth+invalid ordinal HTTP сценариями, новых дефектов не установлено. Первичная RED проверка воспроизвела потерю raster metadata и отсутствие preview API.

Закрыт подэтап source-bound embedded raster extraction/preview; №13 остаётся❌,план8✅/8🟡/3❌. Полный EMF playback/vector graphics, unsupported image465, full Word/PDF visual coverage, raster/mixed tables/OCR conflicts/formula visual correspondence, V4 и qualified corpus открыты. Physical PC не обновлялся, инженерное принятие отсутствует. Следующий шаг — чтение unsupported bitmap header и визуальное покрытие смешанной графики/таблиц на реальном источнике, без возвращения к расчётам. QA:docs/qa/2026-10-09-emf-embedded-raster.md.


### Итог §90 — включено в кандидат

PR106 MERGED squash с expected_head guard5951370b9aa11341f002ae8f48b1ab003d0ffa4f. Кандидатebcafaa69c1a715f3e969fbcf1aa614f2e115533; git fetch подтвердил точное полное дерево54c6d29f95636df516df7c9edb66424ef21c7378, совпавшее с проверенным локальным и опубликованным head. Все final-head CI SUCCESS: Core37986924886/job114011117658 —844 tests/91.266s OK,2 Windows-only skips,10 Node,2 HTTP/DOM и5 Chromium workflows; Windows37986925006/job114011117953 —42 tests/12.909s OK (включая7 bitmap tests),cold/repeat/restart,real Ollama qwen3:0.6b inference и5 browser workflows; Security37986925016 SUCCESS. Embedded raster UI/HTTP/source identity/bitmap ordinal/explicit unrendered scope проверены на Windows и Linux CI. Программный PASS не означает проверку пользовательского ПК.

В реальном оригинале доступны119 embedded raster sources из120 обнаруженных; полные RGB arrays точно совпали с независимым BMP decoder. Неизменность исходного SHA подтверждена. В отдельном контрольном процессе real Store extraction/checkpoint/source revalidation/preview для unit168 прошёл, processed168/14684,cycle_complete=false,model NOT_RUN;792x395 PNG SHA250f5bcad4ccf091e8c1dcdf2fc7683394a2c6ac98b6633d7bc9bc8e685c56c4. Это не полный Store/model прогон и не проверка reload всего большого Store. Старые/неполные промежуточные probe snapshots не считаются полным прогоном; утверждения о persistent history основаны на контролируемых regression/CI workflows, не на этом real-file probe.

№13 остаётся❌: bitmap pixel extraction/preview закрыт в указанном объёме; image465/полная EMF vector отрисовка/Word placement/full visual coverage/таблицы/OCR conflicts/формулы/V4/qualified corpus открыты.8✅/8🟡/3❌. На ПК пользователя не установлено; инженерно не принято. Следующий конкретный пробел — unsupported bitmap header и смешанная графика/таблицы; расчёты ЛИРА/RES отложены.


## 91. №13: маскированный исходный растр EMF и просмотр при усечённом тексте — 09–10.10.2026

До шага кандидатebcafaa69c1a715f3e969fbcf1aa614f2e115533. Расчёты отложены. PR107 https://github.com/maxim505885-jpg/engineer-os/pull/107, ветка feat/emf-bitfields-coverage-20261010, head21114ab273a5927f34af985126afb0a804f6b422; полное дерево7898926d5b8121e655a0b16ccdaf904c7b136dee совпало с проверенным локальным кодом. На момент этой записи PR OPEN, CI ожидается; merge не заявляется.

Реальный пропуск word/media/image465.emf: record76 offset54676 содержит BITMAPINFOHEADER40+3DWORD маски (52bytes),compression3 BI_BITFIELDS32bit,17x19. Reader теперь читает явно заданныеRGB555/RGB565/RGB888 профили16/32bit; zero/overlap/noncontiguous/out-of-depth маски отвергаются, неподдержанные профили явно UNAVAILABLE. Маски включены в payloadSHA и exact descriptor revalidation. Прежние byte/pixel/package limits не увеличены. Alpha/ROP/transform/crop/compositing/vector playback/Word placement не интерпретируются.

Родительский элемент оригинала12572 содержит54282 символа, больше Store20000. RED regression воспроизвела блокировку preview. Новый image-only binder принимает отмеченный TEXT_LIMIT точный source prefix после повторной проверки session/child/originalSHA/parser/full locator; возвращает source_confirmable=false. Quote binder и candidate acceptance продолжают отвергать усечённый текст. Подмена text/locator/truncation state блокируется; asset и selected bitmap payloadSHA повторно проверяются перед PNG. Это доступ к исходному изображению, не подтверждение неполной цитаты.

Реальный неизменённыйDOCX SHA b253439bdd673a775eaf209ca7d398d766efae5f4a18ac33fa6679f7faae28a5:120/120 bitmap sources в138EMF доступны; все29880590 RGB pixels точно совпали с независимым BMP-wrapper/Pillow BMP decoder.14684 logical units/671 image refs сохранены. image465 RGBSHA4aeb840401b2942dd782b70db5c08b363237e8ed4750ff9be54f56a58d9a9969. Контролируемый производныйDOCX с точным оригинальнымimage465 asset прошёл Store/Worker/model/receipt/PNG17x19,stored20000/text_truncated=true,strict quote BLOCK,acceptance=false. Это isolated source asset fixture, не полный original Store/model прогон и не подтверждение original logical parent/physical page.

Локально851 tests/99.990s OK,17 environment skips;38 focused,10Node,2HTTP/DOM,5Chromium PASS; architecture/compile/JS/diff PASS. Первый DOM session-switch timeout повторно PASS; причина не установлена и не выдана за исправленный production defect. Windows suite теперь49tests, реальное выполнение ожидается вCI. Независимый review двух изменений: Critical/Important/Minor нет;65536 значений каждого16bit555/565 совпали с прямым mask scaling. Контролируемый browser проверил обычный и masked bitmap ordinals с явным unrendered scope/no evidence.

Подэтап source-pixel extraction закрыт для120 обнаруженных bitmap источников этогоDOCX; №13 остаётся❌,8✅/8🟡/3❌. Full EMF rendering/vector graphics/Word placement,растровые и mixed tables,OCR conflicts,visual formula correspondence,полныйV4 и qualified corpus открыты. НаПК пользователя не установлено; инженерно не принято. Далее — source-bound rendering и визуальное покрытие смешанной графики/таблиц. ЛИРА/RES отложены. Подробный receipt:docs/qa/2026-10-10-emf-bitfields.md.


### Итог §91 — включено в кандидат

PR107 MERGED squash с expected_head guard21114ab273a5927f34af985126afb0a804f6b422. Кандидат6d59ea16712fafd8306d9710d3726551b183d2b6; git fetch подтвердил полное дерево7898926d5b8121e655a0b16ccdaf904c7b136dee, идентичное проверенному локальному/опубликованному head. Все final-head CI SUCCESS: Core37991762946/job114027465213 —851 tests/93.583s OK,2 Windows-only skips,10Node,2HTTP/DOM,5Chromium; Windows37991762903/job114027465278 —49 tests/14.622s OK,cold/repeat/restart,real Ollama qwen3:0.6b и5 browser workflows,включая ordinary/masked raster ordinals; Security37991762941 SUCCESS. Это Windows runner, не пользовательский ПК.

120/120 bitmap sources реального DOCX доступны;29880590 RGB pixels совпали с независимым BMP decoder. Исходник не изменён. Производный isolated fixture с точным realimage465 asset прошёл Store/Worker/model/receipt/PNG при усечённом parent text;strict quote BLOCK,acceptance=false. Full original Store/model,полная EMF/Word отрисовка и visual coverage/таблицы/формулы/V4/qualified corpus не подтверждены. №13 остаётся❌,8✅/8🟡/3❌;№14/19 открыты. НаПК пользователя не установлено,инженерно не принято. Далее — source-bound rendering и сверка смешанной графики/таблиц;ЛИРА/RES отложены. Точные машиночитаемые receipts:docs/qa/2026-10-10-emf-bitfields-ci.json.


## 92. №13: полный реестр документа и устранение потери хвоста — 10.10.2026

Пользователь поручил закрыть весь№13 за один проход. Критерии не ослаблены: source-pixel decode/число обработанных страниц не означают полноту сложных таблиц/графики/формул/OCR или qualified corpus. Расчёты отложены. До шага кандидат6d59ea16712fafd8306d9710d3726551b183d2b6. PR108 https://github.com/maxim505885-jpg/engineer-os/pull/108, веткаfeat/document-visual-coverage-20261010,head70db597b178e419428588ab63aa6dec4b71af157,tree5dd2b66194be961a73dd68a2601b48ac6c778611; git fetch подтвердил совпадение полного дерева с проверенным локальным кодом. Пока PR OPEN,Security38002094570 SUCCESS,Core38002094577/Windows38002094533 выполняются;merge не заявляется.

Полный native DOCX учёт установил фактическую потерю:2320826 сериализованных символов,Store budget остановил бы проход13606/14684,1078 элементов не обработаны,8 усечены. Причина — повтор полной image/EMF record geometry в тексте, хотя exact descriptor уже есть в locator. В office reader compact textual image refs сохраняют part/SHA/status/reason,а каждый non-null nativeEMF Unicode text — с image/record byte label. Все полные record descriptors остаются в source locator. Прежние бюджеты и strict source binding не ослаблены;glyph indices не выданы за текст.

Независимая сверка reader с base6d59ea1 на исходном DOCX:14684 units,671 image refs,3394 native EMF text-record refs сохранены;все locators/limitations точно равны,весь non-image text/OMML/auxiliary text побайтно равен,body native prefixes и каждый native EMF record text сохранены. Новый текст1358951 chars;ни один unit не превышает20000. SHA оригиналаb253439bdd673a775eaf209ca7d398d766efae5f4a18ac33fa6679f7faae28a5 неизменён. Первый full original Store/Worker/controlled-model probe FAILED,сохранил14505/14684,0text_truncated;model batches ещё не выполнены. Причина исследуется,штатный resume_analysis запущен. Этот промежуточный результат не объявлен полным/успешным. LibreOffice fullDOCX derivative export начат,не завершён на момент записи.

V4 найден через Google Drive ID1Ycw-dcevqNSHgvb_y0pVa7B1lM4uhK6g;74522583 bytes/SHA b5d95b660b35bfb6b2441623635cba91c235efd754bc283dfe1405f075834916 подтверждены. Новый standalone source-bound all-page audit полностью отрисовал534/534 страницы,сохранил PNG SHA/native text SHA/page bbox.40 страниц492–531 не имеют native text;на странице493 визуально имеются планы,подписи и легенда,пустой text не означает пустую страницу. Existing Tesseract rus+eng adapter записал OCR candidates для всех40 страниц:62189 chars,1682 blocks с confidence<60;quality/content/table/formula/graphics verification остаютсяfalse. Это не1682 ошибки отчёта или конструкции. Локальные модели hash rus=e16e5e036cce1d9ec2b00063cf8b54472625b9e14d893a169e2b0dedeb4df225,eng=7d4322bd2a7749724879683fc3912cb542f19906c83bcc1a52132556427170b2;никакой платныйAPI не используется. Финальный повтор audit новым head после review исправления выполняется.

Audit проверяет byte/page/pixel limits,исходныйSHA до/после,сохраняет полный постраничный журнал и OCR scope UNVERIFIED. Initial bounded source read и streaming final hash. Review обнаружил пропуск финального журнала при исчезновении исходника:исправлен с RED/GREEN regression,SOURCE_IDENTITY_UNAVAILABLE и render_cycle_complete=false. Независимый повторный review:blocking findings нет. Локально857 tests/65.906s OK,17 environment skips;6 targeted,10Node,2HTTP/DOM,5Chromium PASS;architecture/compile/JS/diff PASS. Windows suite добавляет6 tests,ожидается55. Первый browser запуск не выполнен из-за отсутствующего Chromium binary;после установки финальные маршруты PASS,не production defect.

№13 остаётся❌ до фактического выполнения всех критериев. Полный original Store/model ещё не PASS;полная Word/EMF layout отрисовка,растровые/mixed tables/ячеечные связи,visual formula fidelity,OCR exactness/conflicts и qualified multi-document corpus не подтверждены. НаПК пользователя не установлено,инженерно не принято.8✅/8🟡/3❌;расчёты ЛИРА/RES отложены. Далее — завершить диагностируемые реальные прогоны и source-bound qualified визуальную сверку,не начинать ещё один счётчиковый подэтап. Receipt:docs/qa/2026-10-10-document-visual-coverage.md.

# ENGINEER OS — проверка пяти критериев

Дата: 09.10.2026. Последний код PR 97: 187b6d88448806f31781df7cf68f6bd6bf826b22; кандидат f83c4d5fbaac8e602757ca6fac1646b86589cdff принят после всех 9 CI SUCCESS. Дерево 2af4da649a69d4f60c7c51ffd7331af1ea6ccb80 равно проверенному локальному коду. Последний итог — §73.1; прежние проходы сохранены как история.

| Критерий | Подтверждено | Что остаётся для полного закрытия |
|---|---|---|
| 1. CodeQL и единый кандидат | 29 alerts разобраны индивидуально; false-positive решения привязаны к owner-controlled контракту; 0 open на проверенном PR 91. PR 91 принят в candidate 22ad4c1 с точным равенством проверенного дерева. | Критерий закрыт. Это не окончательный выпуск main. |
| 2. Полнота документов | Прежние PDF: 43 страницы; Office: 665 единиц. Новый полный DOCX 147 МБ: 14 678/14 678 единиц, 0 ошибок и обрезаний текста; исходник неизменён. Сохранены 41 уравнение и 6 300 объявлений объединённых ячеек. Проверены все три решения журнала источников на большом оригинале. | 7 022 единицы остаются BLOCK. Требуют проверки 655 элементов графики и 642 media-файла, отображение таблиц, смысл формул и полнота документа. Физические страницы неизвестны; V4 PDF и квалифицированный эталон остаются открыты. |
| 3. Нормы, расчёт, FINAL_AUDIT | LIR identity проверена; приложение сохраняет BLOCK при отсутствии семантического decoder/export и основания принятия. | Подтверждённые в intake GEOMETRY, MATERIALS_SECTIONS, LOADS_COMBINATIONS, SUPPORTS_RELEASES, UNITS, SOLVER_LOG, RESULTS, ACTUAL_STRUCTURE_REFERENCE; действующие нормативные основания и квалифицированная проверка. Положительный FINAL_AUDIT реального объекта отсутствует. |
| 4. Память, отчёт, CAD, providers | Программные acceptance/stale/revoke gates, отчётные черновики, CAD/memory browser route проверяются. Найдены5 DWG копий/1 уникальный AC1032; оригиналы неизменны. Отдельный DXF создан GNU LibreDWG 0.14 и прочитан. | 10 172 графических сущности доступны в приложении для чтения (15 906 всех entitydb records). Редактирование остаётся BLOCK при edit budget 10 000 и неподдерживаемой геометрии. 1 304 строки warnings и210 errors конвертера; геометрия/roundtrip не подтверждены, controlled edit NOT_RUN. Реальный ACCEPTED→memory и принятый отчёт нужны после критерия 3; fixture/replay их не заменяют. Внешние optional providers без фактического live receipt не считаются проверенными. |
| 5. Windows и финальный выпуск | Native Windows supervisor clean start/cache repair/restart,23 regression tests и фактический Ollama qwen3:0.6b inference проверены в CI. Исправлены byte-lock cleanup, shared SQLite metadata, DOM teardown и Windows test paths/cwd. | Windows и Linux PR/push CI полностью прошли. Остаётся проверенная установка, повторный запуск и перезагрузка на физическом Windows ПК. После закрытия остальных критериев — FINAL RELEASE AUDIT,main/tag. |

## Реальные исходники и ограничения

Два PDF:22+21 страница, у 40 из 43 нет native text. OCR выполнен настоящим Tesseract rus+eng через штатный Store/Worker, не тестовым replay. Failed pages 0, но все 43 остаются BLOCK; MuPDF дополнительно выдаёт object-out-of-range/xref warnings, поэтому полнота рендера не подтверждена. Первые листы обоих PDF визуально просмотрены: планы, карты измерений и мелкие инженерные обозначения. Низкоуверенный OCR всей страницы не подтверждает числа, пространственные связи и легенды.

DOCX содержит 487 logical units; XLSX 125+48 units. Все 660 units пройдены; прочитанный текст не означает проверенные physical pages/layout/formulas/merged table semantics. Native LIR файлы 42 047 193 и 21 209 600 байт имеют сохранённую identity; solver и корреляция с реальной конструкцией не запускались.

Пять DWG byte-identical, один оригинал 1 138 808 байт, SHA256 `544f0114ba3e5b16c737c189716ec64308f36855cf93b3fab2bfce489f72d632`. Отдельный DXF 16 034 803 байт, SHA256 `dddb5edf86015cf7603f9e95d485d18ee03c4916c30c46e8e88cca4fd9ed18d0`. Inventory: 4 189 modelspace, 10 172 block entities, 287 blocks, 32 layers, 3 layouts. Официальный LibreDWG 0.14 архив проверен по SHA256 до сборки. Exitcode 0 не отменяет ошибки/предупреждения преобразования. Произвольное повышение лимита 10000 ради PASS не выполнялось.

## Изменения и проверка

Повреждённый cache зависимостей теперь проверяется и восстанавливается перед запуском. Ошибка приобретения Windows byte lock закрывает stream и возвращает штатное занятие каталога. Когда обычный Windows stat теряет число links на открытом SQLite WAL, native metadata query использует совместный read/write/delete доступ, открывает reparse point без перехода и продолжает отклонять reparse/hardlink.

JSDOM тест останавливает таймеры каждой страницы, дожидается fetch и response bodies, затем уничтожает document. Это устраняет teardown race без подавления unhandled errors. Выбранный Windows каталог проверяется по bigint device/inode identity; восстановленные оригиналы дополнительно сравниваются побайтово. PDF fixture Python запускается из repository root, как остальные launcher/seed subprocesses. Независимое ревью не нашло оставшихся Critical/Important в этих изменениях; DOM дважды завершился PASS с exitcode 0.

## План оставшейся работы

1. Документы: проверить локальные области сложных листов, таблицы/merged cells, формулы, рисунки и легенды; сверить полноту V4 с проверяемым эталоном. Сохранить BLOCK там, где нет подтверждения.
2. Расчёт/нормы: получить и проверить восемь семантических ролей, vendor exports/run и корреляцию с фактической конструкцией; провести квалифицированный нормативный и расчётный аудит.
3. Реальный кейс: провести положительный FINAL_AUDIT; только затем проверить принятую память и выпуск отчёта.
4. CAD: устранить предупреждения/ошибки native conversion, доказать эквивалентность геометрии/units/resources и ограниченный контролируемый edit/roundtrip для большого реального источника.
5. Физический Windows ПК: чистая установка, повторный запуск/restore и перезагрузка с сохранением истории. Затем финальный release audit и согласованный main/tag.

В едином плане 19 пунктов:8 готовы в указанном программном объёме,8 частично готовы,3 открыты (13, 14, 19). Программный PASS не является инженерной приёмкой; BLOCK здесь фиксирует отсутствие проверенного основания и не устанавливает дефект конструкции.

## Результаты предыдущего прохода PR 92

Head: `ff586382874774838d584339bfbfa136c26dd351`, tree: `f5f78d4fa1504259b02a2d323dd2143dd690c6c4`.

- Windows PR [run 37893170912](https://github.com/maxim505885-jpg/engineer-os/actions/runs/37893170912): SUCCESS, 23 tests, real Ollama, все 4 Chromium routes. Windows push 37893164417 также SUCCESS.
- Linux push [run 37893164515](https://github.com/maxim505885-jpg/engineer-os/actions/runs/37893164515): SUCCESS, 728 tests (726 passed, 2 native-Windows-only skips), 4 Node, 2 HTTP/DOM и 4 Chromium routes.
- CodeQL aggregate и 3 analyzers, оба security guard: SUCCESS. Required Linux PR [run 37893170818](https://github.com/maxim505885-jpg/engineer-os/actions/runs/37893170818) также SUCCESS.


PR [92](https://github.com/maxim505885-jpg/engineer-os/pull/92) squash merged в `integration/release-candidate-v1`: `8beb55924a8e5a82029636b235c3cac64c565488`. Git API подтвердил точное равенство дерева `f5f78d4fa1504259b02a2d323dd2143dd690c6c4` проверенному source head. Рабочая ветка чистая. Критерий 1 полностью закрыт; критерии 2–5 частично готовы с указанными реальными основаниями и оставшимися gates. Финальный инженерный объект и релиз не приняты.


## Продолжение — большой CAD и OCR-проба

[PR 93](https://github.com/maxim505885-jpg/engineer-os/pull/93) принят в кандидат `9bf58d02659d9ff0f330b3c310046f406802f088`, tree `2cb8e47cd4d5f199edee708cb784e4db83a7c62d` точно равен проверенному `fd4e8da9b933dd2ab3c8065a6c1aafcb816122dc`. Все 9 CI checks SUCCESS. Linux:731 tests (729 passed, 2 native-Windows-only skips), 4 Node, 2 HTTP/DOM, 4 Chromium. Windows: 23 tests, actual Ollama qwen3:0.6b и 4 Chromium PASS. Независимый review — нет Critical/Important.

Read-only inventory/locator: до 50 000 графических сущностей в блоках; edit/export сохраняют 10 000 и все исходные запреты. На действительном 16MB derived DXF прочитаны 10 172 сущности за 4.324s, peak RSS 141108 KiB; source SHA неизменён. Списки ресурсов/локаторов ограничены 100. Ограничения сложной geometry, audit, conversion и инженерной приёмки не устранены.

Проба OCR первого листа: whole page median line confidence 56.67 → four regions 80.35; 40 → 22 blocks, 296 → 294 chars, 15 → 7 low-confidence. Разбиение отличается, эталонной транскрипции нет, границы crop могут резать текст. Confidence не равно accuracy/coverage. Это offline probe, не продуктовый OCR feature, acceptance=false. Следующий шаг — region/tiled OCR с явным покрытием, проверенными координатами, общим page/time/output budget и эталонной сверкой.

## Продолжение — OCR по областям и проверка плана

[PR 94](https://github.com/maxim505885-jpg/engineer-os/pull/94) принят в кандидат `cca057f6fdd2e1f3751485727543d15b33e1879a`, дерево `2ae639262b28d21707d3f8f628d49fd2370c9e91` точно равно проверенному `6db015bb9ad5c38a5143f747f2508eabc5fe97eb`. Все 9 checks SUCCESS. Linux: 741 тест (739 PASS, 2 Windows-only skips), 4 Node, 2 HTTP/DOM, 4 Chromium. Windows: 23 теста, реальный Ollama qwen3:0.6b, 4 Chromium. Локально 35 focused tests PASS; два Important ревью воспроизведены и исправлены RED→GREEN. Отложенный minor: нет отдельного descriptor прерванного прохода; planned/completed и INCOMPLETE раскрывают неполное выполнение.

Режим regions сохраняет whole-page OCR и четыре перекрывающиеся области с исходными координатами и общей границей 60 секунд / 2 MiB TSV / 20 000 слов / 45 млн пикселей. Альтернативы явно маркируются в модельном вводе; повторы не являются независимыми фактами. По умолчанию whole; смена режима меняет identity и не переиспользует старое извлечение.

Окончательный реальный прогон: 43/43 страницы, 215 проходов, 0 failed и 0 retained-text truncations; оригиналы неизменны, координаты в пределах исходных страниц. Время: 109.297 и 244.320 секунды для двух PDF. Максимум на страницу 32 080 286 пикселей / 326 472 TSV bytes / 2 432 слова. Программное выполнение подтверждено, все результаты остаются BLOCK/UNVERIFIED.

Выборочная визуальная сверка ассистентом трёх чисел первой страницы: 2 совпали; размер 82400 распознан региональным проходом как 82406 и отсутствовал в целостном проходе. Это конкретное ограничение распознавания, а не дефект инженерного объекта. Полный квалифицированный эталон, графика/таблицы/формулы и V4 не подтверждены; предупреждения MuPDF xref сохраняются.

План 19 пунктов: 8 готовы в указанном программном объёме, 8 частично, 3 открыты (13, 14, 19). Следующий №13 — целевые числовые подписи/таблицы/формулы со сверкой по эталону, затем графика и полнота всего V4. Далее №6/14 (нормы/семантические расчёты/реальный FINAL AUDIT), №15/16/17/18 (принятая память/отчёт/CAD/провайдеры), №9/19 (physical Windows и выпуск). Критерий 1 закрыт; критерии 2–5 остаются частичными. Оставшиеся gates не снимаются числом зелёных тестов.

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

Независимое ревью: Important100MBreviewcap и MinorUIwording воспроизведены/исправлены, остаточных Critical/Important/Minor0. Focused47Python и5Node PASS, architecture/compile/JS/diff PASS. Итоговый frozen full763теста/761PASS/2nativeWindows skips с реальным rus+eng OCR. Первичный запуск без OCR дал17skips и не использован как полный результат. RemoteCI будет добавлен после завершения. Parseridentity фактического full run точно совпал с frozenOfficeкодом.

План8✅/8🟡/3❌. №13 остаётся открыт: rendered tables/merged cells/formulas,655 drawing elements/642media нового полного DOCX, прежняя Office/OCRграфика и числовые конфликты, полный V4 и qualified ground truth. Далее нормы/8semanticroles/solver-run/actualcorrelation/FINAL AUDIT, реальный ACCEPTED→memory/report,CADroundtrip,liveproviderreceipts,physicalWindows/release. Детали docs/qa/2026-10-09-large-office-input.md.

Дополнительная проверка PR97: первый headfd6f08c получил763PythonPASS/761PASS/2skips, но LinuxPR DriveDOM упал на new-chat. PushLinux и Windows прошли. Детерминированно воспроизведены две stale bootstrap races: поздний список скрывал созданный чат и initial list мог переключить пользователя назад. Исправлены latest-request render guard и initial-consumer current/creating guard. Controlled-delay HTTP/DOM RED→GREEN, VMinitial-response RED→GREEN. Итог6Node/2localHTTP-DOM PASS, независимое ревью0остаточныхImportant. Новый head `2be525c674037aa87e498fd2abf25dd8ad0709f4`, tree `554b44515fe801ac20b92b31f373df21f0a29c9e` равно локальному `b1d724c8da4cfbd7a3f03fa386bd85b724a0bb86`; CI выполняется заново. Первое падение сохранено в receipts, не скрыто rerun.

Последний frozen head PR97 `187b6d88448806f31781df7cf68f6bd6bf826b22`, tree `2af4da649a69d4f60c7c51ffd7331af1ea6ccb80` равно локальному `9aa29f7724905137bb6c816a59101ef060a4cc57`. На предыдущем head Windows23/live Qwen/2Chromium прошли, но очистка intake fixture дала EBUSY app.lock. Windows журнал показывает EBUSY вскоре после PASS и не доказывает исполнение timeout-ветки. В исходном fixture ожидался exit, а не close; отдельно детерминированно воспроизведена timeout-ветка SIGKILL, которая разрешала удаление до закрытия процесса. Shared stop helper ждёт close, имеет bounded deadline и не удаляет каталог при неудачной остановке; rm имеет ограниченные retries для transient locks. Actual-cleanup RED→GREEN,7Node PASS, независимое ревью0Important. LocalChromium NOT_RUN: отсутствует browser binary; это не заменено заявлениемPASS. Финальная реальная проверка Windows/Linux выполняется на новомhead.

## 73.1. Итог полного Office-прохода: PR 97 принят

Все 9 CI checks на `187b6d88448806f31781df7cf68f6bd6bf826b22` SUCCESS. PR 97 принят в кандидат `f83c4d5fbaac8e602757ca6fac1646b86589cdff`. Дерево `2af4da649a69d4f60c7c51ffd7331af1ea6ccb80` равно проверенному опубликованному коду и локальному `9aa29f7724905137bb6c816a59101ef060a4cc57`. Linux PR/push: 763 Python-теста (761 PASS, 2 native Windows skips), 7 Node, 2 HTTP/DOM и 4 реальных Chromium-сценария PASS. Windows: 23 теста, clean start/cache repair/restart, настоящий Ollama qwen3:0.6b и все 4 Chromium-сценария PASS; очистка завершилась успешно. Физический Windows ПК по-прежнему NOT_VERIFIED. Receipts: docs/qa/2026-10-09-large-office-input-ci.json.

Полный доступный DOCX 147 МБ обработан: 14 678/14 678 логических единиц, 0 ошибок исполнения и обрезаний текста, исходник неизменён. Сохранены 41 OMML-уравнение с буквальными токенами и 6 300 объявлений объединённых ячеек; source XML сверка совпала. 7 022 единицы остаются BLOCK. 655 элементов графики и 642 media-файла, отображение таблиц, смысл и вычисление формул, полнота страниц/документа не приняты. Число физических страниц неизвестно; полный DOCX не объявлен проверенным V4 PDF. Три source-review решения на настоящем большом оригинале прошли без инженерной приёмки.

За проход закрыты конкретные программные дефекты: несовместимые входные лимиты большого Office, ограниченное чтение оригинала при source review, повторное полное хеширование на каждой единице, две гонки старых списков чатов и преждевременная очистка тестового процесса. Начальные падения CI сохранены, исправления проверены RED→GREEN и независимым ревью.

План остаётся **8 ✅ / 8 🟡 / 3 ❌**. Из пяти критериев закрыт CodeQL/единый программный кандидат; остальные частичны. Следующий шаг №13: квалифицированная сверка rendered tables/merged cells/formulas, всей графики и числовых конфликтов, V4 PDF и полного эталонного покрытия. Затем №6: восемь семантических расчётных ролей, актуальные нормативные основания, реальный solver-run и связь с фактической конструкцией. После этого №14: положительный FINAL AUDIT; на его основании принятая память и отчёт, CAD equivalence/roundtrip и live-provider receipts. Физический Windows и №19 release/main/tag — после закрытия продуктовых критериев. BLOCK не снят автоматически.

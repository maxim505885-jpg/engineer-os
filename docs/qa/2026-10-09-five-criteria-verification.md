# ENGINEER OS — проверка пяти критериев

Дата: 09.10.2026. Последний код PR95: 6b7674bc57ce62f8abac2cd702720e7c7c1d6488; кандидат c4e1181a5f7463a03ec2fce279aab6641e420e61 принят после9CI SUCCESS. Дерево e404c539dcd28394980b937b5eb1fb0a9a676f9a равно проверенному коду. Последний итог — §71.1 ниже; прежние проходы сохранены как история.

| Критерий | Подтверждено | Что остаётся для полного закрытия |
|---|---|---|
| 1. CodeQL и единый кандидат | 29 alerts разобраны индивидуально; false-positive решения привязаны к owner-controlled контракту; 0 open на проверенном PR 91. PR 91 принят в candidate 22ad4c1 с точным равенством проверенного дерева. | Критерий закрыт. Это не окончательный выпуск main. |
| 2. Полнота документов | 7 реальных оригиналов сохранены без изменения. Native проход43 PDF страниц и660 Office units без failed; реальный OCR43/43, 66 349 символов, 2 615 блоков. | Все 43 OCR страницы BLOCK по low confidence и непроверенной графике. DOCX: 31 рисунок, 2 формулы, 14 merged cells; XLSX: формулы/стили/графика и 48 merged cells не проверены. Нужна проверка таблиц, чисел, рисунков и локальных областей с эталонным покрытием; полный V4 и представительный corpus. |
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

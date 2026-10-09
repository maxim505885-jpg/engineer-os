# ENGINEER OS — проверка пяти критериев

Дата: 09.10.2026. Проверяемый код PR 92: `ff586382874774838d584339bfbfa136c26dd351`. Все 10 проверок CI SUCCESS. PR 92 принят в официальный кандидат `8beb55924a8e5a82029636b235c3cac64c565488`; дерево точно равно проверенному коду. Main и финальный release/tag не публиковались.

| Критерий | Подтверждено | Что остаётся для полного закрытия |
|---|---|---|
| 1. CodeQL и единый кандидат | 29 alerts разобраны индивидуально; false-positive решения привязаны к owner-controlled контракту; 0 open на проверенном PR 91. PR 91 принят в candidate 22ad4c1 с точным равенством проверенного дерева. | Критерий закрыт. Это не окончательный выпуск main. |
| 2. Полнота документов | 7 реальных оригиналов сохранены без изменения. Native проход43 PDF страниц и660 Office units без failed; реальный OCR43/43, 66 349 символов, 2 615 блоков. | Все 43 OCR страницы BLOCK по low confidence и непроверенной графике. DOCX: 31 рисунок, 2 формулы, 14 merged cells; XLSX: формулы/стили/графика и 48 merged cells не проверены. Нужна проверка таблиц, чисел, рисунков и локальных областей с эталонным покрытием; полный V4 и представительный corpus. |
| 3. Нормы, расчёт, FINAL_AUDIT | LIR identity проверена; приложение сохраняет BLOCK при отсутствии семантического decoder/export и основания принятия. | Подтверждённые в intake GEOMETRY, MATERIALS_SECTIONS, LOADS_COMBINATIONS, SUPPORTS_RELEASES, UNITS, SOLVER_LOG, RESULTS, ACTUAL_STRUCTURE_REFERENCE; действующие нормативные основания и квалифицированная проверка. Положительный FINAL_AUDIT реального объекта отсутствует. |
| 4. Память, отчёт, CAD, providers | Программные acceptance/stale/revoke gates, отчётные черновики, CAD/memory browser route проверяются. Найдены5 DWG копий/1 уникальный AC1032; оригиналы неизменны. Отдельный DXF создан GNU LibreDWG 0.14 и прочитан. | 15 906 объектов; приложение BLOCK CAD_ENTITY_LIMIT 10000. 1 304 строки warnings и210 errors конвертера; геометрия/roundtrip не подтверждены, controlled edit NOT_RUN. Реальный ACCEPTED→memory и принятый отчёт нужны после критерия 3; fixture/replay их не заменяют. Внешние optional providers без фактического live receipt не считаются проверенными. |
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

## Точные результаты последнего кода

Head: `ff586382874774838d584339bfbfa136c26dd351`, tree: `f5f78d4fa1504259b02a2d323dd2143dd690c6c4`.

- Windows PR [run 37893170912](https://github.com/maxim505885-jpg/engineer-os/actions/runs/37893170912): SUCCESS, 23 tests, real Ollama, все 4 Chromium routes. Windows push 37893164417 также SUCCESS.
- Linux push [run 37893164515](https://github.com/maxim505885-jpg/engineer-os/actions/runs/37893164515): SUCCESS, 728 tests (726 passed, 2 native-Windows-only skips), 4 Node, 2 HTTP/DOM и 4 Chromium routes.
- CodeQL aggregate и 3 analyzers, оба security guard: SUCCESS. Required Linux PR [run 37893170818](https://github.com/maxim505885-jpg/engineer-os/actions/runs/37893170818) также SUCCESS.


PR [92](https://github.com/maxim505885-jpg/engineer-os/pull/92) squash merged в `integration/release-candidate-v1`: `8beb55924a8e5a82029636b235c3cac64c565488`. Git API подтвердил точное равенство дерева `f5f78d4fa1504259b02a2d323dd2143dd690c6c4` проверенному source head. Рабочая ветка чистая. Критерий 1 полностью закрыт; критерии 2–5 частично готовы с указанными реальными основаниями и оставшимися gates. Финальный инженерный объект и релиз не приняты.

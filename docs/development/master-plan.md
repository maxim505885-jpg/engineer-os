## §171 — 2026-10-14: пункт 13 возобновлён на реальном кейсе

В ответ на последнюю просьбу пользователя пункт 13 проверяется сейчас, а не откладывается на конец независимых пунктов. Сводное состояние, результат теста полного комплекта и новый порядок указаны в разделе «Текущая позиция» ниже. Главный результат: штатные маршруты обработали DOCX 553/553 логических единиц и все три PDF-листа, но оставили существенные BLOCK/UNCERTAINTY; DWG-конвертер недоступен. Пункт 13 остаётся OPEN. Подробная локальная QA-запись не содержит общедоступной исходной документации и не загружалась в репозиторий.

## §170 — 2026-10-14: Windows launcher recovery, real .cmd path, and current gates

PR148 is ready for review and remains unmerged. It targets the unchanged candidate `integration/release-candidate-v1` at `091edd1c2881b1f7c416034b45c1d6f48899bcdd`. Exact PR head: `f53a6f45e6d46486e8d2103af610565591fef494`.

### Completed in this pass
- Reproduced and fixed Windows one-click failures: repair a pre-existing venv with missing pip; detect failed venv creation accurately; put Windows' native PowerShell module directory before inherited reduced modules; support a selected loopback port through both start and stop commands.
- Added Windows regression coverage for missing pip recovery and alternate-port start/stop; the workflow now executes the real `Start_ENGINEER_OS.cmd`. Added timeout diagnostics for the synthetic Drive DOM smoke. Fixed a Windows tempfile test by closing the source before reopening it.
- Actual local `Start_ENGINEER_OS.cmd -Port 18768` startup receipt and matching stop passed. The unrelated service on 8765 was not stopped.
- Exact PR-head CI: Windows Runtime #217, Core Tests #1016, Repository Security Guard #837, and CodeQL PR workflow #607 all SUCCESS. Core includes full Python regression and browser UI/HTTP tests. Windows includes cold/repeat/restart, pip repair, alternate-port CMD start/stop, backup/security, offline PDF viewer, qwen3:0.6b browser inference, and four browser workflows.
- Local browser route suite (7 routes), full HTTP/DOM E2E, and offline PDF viewer passed. Local qwen3:8b browser inference exceeded the bounded timeout; Open WebUI was not listening on port 8080. No local inference performance claim is made.
- A full local Windows Python run enumerated 1,058 tests, with 47 skips and 7 errors caused by six symlink-privilege cases and a Windows open-file fixture. The open-file fixture is fixed and its four-test module passes. The full Core regression passed on GitHub CI; local symlink tests remain limited by this account's Windows permissions.

### Current 19-point status
No point is promoted to DONE on this evidence alone. The project remains 8 DONE / 8 PARTIAL / 3 OPEN.
- №9 PARTIAL: launcher defects and CI lifecycle are covered; physical reboot and install continuity on the user's PC remain.
- №11 PARTIAL: browser workflows pass; full real-user acceptance remains.
- №12 PARTIAL: CI security and backup tests pass; CodeQL alert #45 status reconciliation and physical cross-machine transfer/restore remain.
- №17 PARTIAL: DWG source and conversion history exist; source-specific geometry, loss accounting and roundtrip remain.
- №18 PARTIAL: CI local inference passed with qwen3:0.6b; user-PC qwen3:8b timed out and live Open WebUI/optional provider receipt remains unqualified.
- №14, №15, №16 and №19 remain OPEN/PARTIAL pending a real accepted engineering case and its traced knowledge/report/release evidence.
- №13 remains OPEN and deferred last. LIRA/SCAD/RES calculations remain deferred under the user's instruction.

### Next execution order
1. Review PR148, then integrate it into the candidate only through the repository's normal review/merge gate.
2. Reconcile CodeQL alert #45 and complete physical backup transfer/restore and reboot evidence.
3. Verify DWG geometry, conversion losses, supported editing scope and roundtrip.
4. Qualify the local provider receipt, qwen3:8b performance on the user's PC, and Open WebUI only if it remains part of the selected local setup.
5. Use a real positive case to complete acceptance, memory recall/revoke and DOCX/PDF review; rerun release audit.
6. Resume №13 last; calculations stay deferred.

No ACCEPTED, 100%, or release-complete claim is made.

> **Актуально 14.10.2026 / §169:** порядок №13 не меняется; он остаётся OPEN и последним содержательным документным блоком. PR147 squash merged: candidate 091edd1c2881b1f7c416034b45c1d6f48899bcdd. PR head 92a2396d441e2005712f85cd20f3e40693b618a4 passed Core, Windows Runtime, Repository Guard and CodeQL. Candidate push Core1012/1013, Windows213/214, Security829/830 and push workflow599 passed. Windows Runtime included the end-to-end receipt/source-page test plus cold/restart, backup/security, offline PDF viewer, live Ollama and browser workflows. Local Ollama qwen3:8b returned PASS; Open WebUI port8080 was not listening. #18 remains PARTIAL and E3 open until live Open WebUI/optional-provider receipt is verified. #12 remains PARTIAL: CodeQL alert #45 and physical transfer/restore remain open; candidate CodeQL status associated with PR74 reported 4 HIGH/1 MEDIUM alerts needing separate reconciliation. #17 PARTIAL (source DWG/DXF absent). #13 OPEN and last. LIRA/SCAD/RES calculations deferred; no 100%, ACCEPTED or release-complete claim.
# ENGINEER OS — план доведения до стабильного выпуска
Обновлено: 14.10.2026, Europe/Moscow. Активный план заменяет противоречащие ему ранние сводки, но не уничтожает историю.
Исполнение: самостоятельно по шагам через superpowers:executing-plans; этот документ является дорожной картой, конкретный implementation plan составляется для изменяемого подсистемного блока перед кодом.

## Цель и критерий 100%
100% означает выполнение всех согласованных критериев выпуска в документированном поддерживаемом объёме, а не универсальное безошибочное чтение любых файлов. Неизвестные/неподдерживаемые данные явно получают UNCERTAINTY/UNAVAILABLE/BLOCK и не допускаются к неподтверждённому заключению.
Бесплатное локальное приложение Windows: ТЗ → документы → проверка извлечения → доказательства → профильные проверки → заключение → FINAL AUDIT. Чат, история, задачи, память, CAD и восстановление входят в выпуск. Обязательные платные API не вводятся; оригиналы неизменны.

## Текущая позиция
**На 14.10.2026 пункт 13 возобновлён по прямой просьбе пользователя и сейчас проверяется на предоставленном реальном комплекте.** Все 42 страницы Word-export и 49 медиаобъектов визуально проверены в локальном QA; это не подтвердило семантическую точность или геометрию. Комплект целиком прошёл штатный attachment-preparation route без модели: DOCX 553/553 логических единиц (112 BLOCK, 441 UNCERTAINTY); PDF 1–3 native route BLOCK на векторном содержимом; OCR выполнен на всех трёх листах, но каждый остался BLOCK с OCR_TEXT_UNVERIFIED / OCR_LOW_CONFIDENCE; DWG BLOCK — DWG_CONVERTER_UNAVAILABLE. Это не закрывает №13 и не подтверждает инженерные выводы.

### Свежая проверка всего плана
GitHub candidate: `integration/release-candidate-v1` на `091edd1c2881b1f7c416034b45c1d6f48899bcdd`. PR148 остаётся открытым и не объединённым на `f53a6f45e6d46486e8d2103af610565591fef494`; exact-head Windows Runtime #217, Core #1016, Security Guard #837 и CodeQL PR #607 успешны. Общий реестр остаётся 8 DONE / 8 PARTIAL / 3 OPEN; изменения статусов по новому кейсу не доказаны.

### Следующие действия
1. №13: сохранить приватные оригиналы; создать source-bound инвентарь листов и визуальных элементов; разобрать все DOCX drawing/field/merged-cell limitations и связь приложения PDF-листов с Word; квалифицировать OCR/vector fallback на каждой физической странице; определить ошибки против независимо размеченного эталона. До прохождения каждого полного критерия держать BLOCK/UNCERTAINTY.
2. №9 и №12: завершить пользовательские физические reboot и перенос/restore evidence; отдельно сверить CodeQL alert #45.
3. №17: применить проверяемый локальный DWG converter, сверить сущности/слои/геометрию и потери, затем roundtrip; не выводить геометрию из PDF вместо исходного CAD.
4. №18: завершить provider receipt/performance и проверить выбранный Open WebUI путь на пользовательском ПК.
5. №14–16: только после полного документального основания — инженерная проверка, положительный FINAL AUDIT/явная приёмка, трасса accepted knowledge recall/revoke и сверенный DOCX/PDF выпуск.
6. №19: выполнить полный release checklist на чистой установке и подтвердить воспроизводимые инструкции. PR148 требует обычного ревью и candidate integration.
7. №6 solver-расчёты LIRA/SCAD/RES остаются отложены по решению пользователя; не включать в автоматическое закрытие.


## Единый реестр 19 пунктов
| № | Направление | Статус на 14.10.2026 | Оставшийся критерий |
|---|---|---|---|
|1|Единая версия|DONE в объёме кандидата|Финальный release относится к19|
|2|OCR и локальная модель|DONE программный контур|Качество конкретного документа относится к13|
|3|Большие документы/resume|DONE программный контур|Сохранить совместимость при изменениях|
|4|Форматы и происхождение данных|DONE программный контур|Поддерживаемые ограничения явно документированы; сложные случаи в13|
|5|ТЗ→источник→вывод|DONE программный контур|Сквозной положительный кейс в14|
|6|Нормы/расчёты|PARTIAL; расчёты отложены|Редакции/применимость норм; реальные model/run/results и сверка|
|7|Реальный сценарий|DONE отрицательный сценарий|Положительный сценарий в14|
|8|FINAL AUDIT gates|DONE программный контур|Инженерная приёмка в14|
|9|Windows один запуск|PARTIAL|Чистая установка/перезапуск/перезагрузка на реальном ПК|
|10|Консолидация|DONE в объёме кандидата|Новые изменения только после проверки|
|11|Интерфейс|PARTIAL|§156: textarea keyboard focus fixed and tests pass; full real-user acceptance and physical release remain|
|12|Backup/recovery/security|PARTIAL|PR146 merged; exact PR-head Core/Windows/Security/CodeQL PASS, включая 183 Windows tests и hardlink checks. Открыты CodeQL #45 и физический Windows перенос/restore.|
|13|Полнота документов|OPEN — новый реальный комплект проверен штатными маршрутами, критерии полноты не пройдены|§171: DOCX 553 logical units (112 BLOCK / 441 UNCERTAINTY; physical pages unknown); three vector PDFs BLOCK on native route and remain BLOCK after full-page OCR; separate DWG intake BLOCK because converter unavailable. Still need full visual/semantic comparison, attachment linkage, table/field/image verification and independent labelled accuracy corpus.|
|14|Реальный ACCEPTED|OPEN|Полное ТЗ, проверенные основания, положительный FINAL AUDIT|
|15|Подтверждённая память|PARTIAL|ACCEPTED→knowledge→recall/revoke на реальном кейсе|
|16|Заключения/отчёты|PARTIAL|Проверенный инженерный выпуск DOCX/PDF|
|17|CAD/DWG|PARTIAL|Реальный DWG отдельно преобразован GNU LibreDWG0.14:15,906 объектов;1,304 предупреждения и210 ошибок конвертации; CAD_ENTITY_LIMIT=10,000. Геометрия, потери и roundtrip не подтверждены|
|18|Несколько ИИ|PARTIAL|§169: live Ollama и receipt/source-page provenance прошли; Open WebUI на ПК UNAVAILABLE; optional-provider receipt/gate не квалифицирован.|
|19|Стабильный выпуск|OPEN|Все обязательные release gates, clean install, main/tag и воспроизводимые инструкции|

Итого: 8 DONE в указанном объёме, 8 PARTIAL, 3 OPEN. Это счёт пунктов, не процент инженерной готовности.

## Исторические контрольные результаты прежних этапов (приоритет — текущая позиция §171)

### A. Стабилизировать новые инструменты — №13
Файлы: engineering/local_app/word_formula_preview.py, table_worker.py, table_readback.py; tests/test_word_formula_preview.py, tests/test_table_readback.py; scripts/probe_formula_runtime.py на docs-ветке.
- [x] A1. На безопасном фиксированном fixture воспроизвести distro LibreOffice exit1. Сравнить launcher/SVP/direct binary/профиль памяти и безопасный reference. Зафиксировать причину, минимальный fix и regression. Не открывать user original в unsandboxed контроле; javaldx warning не считать причиной без доказательства.
- [x] A2. Воспроизвести custom tessdata без configs/hocr. Явно включить tessedit_create_hocr=1 с exact PNG input. При пустом OCR сохранить найденную геометрию с TEXT_UNAVAILABLE. Проверить отсутствующий config, empty OCR, merged cells и настоящий V4 p55 bbox[55,68,582,462].
- [x] A3. Проверить source SHA/координаты/лимиты/authenticated HTTP/UI и неизменность оригиналов. Реальные QA JSON/PNG/logs сохранить долговременно, записать ID и хеши.
- [x] A4. На окончательном head выполнить focused/full suite, HTTP/DOM/Chromium и review; получить Core/Windows/Security SUCCESS на этом же head. Только затем объединить PR140 и сверить merged tree.
**Выход A:** работающие в квалифицированных средах инструменты в общем кандидате. №13 этим целиком не закрывается.

### B. Доказать качество чтения — №13
- [ ] B1. Создать эталонный реестр исходников/областей: SHA, формат, page/part/bbox, ожидаемый текст/числа/знаки/единицы/ячейки/связи, основание визуальной сверки. Включить реальные V4/DOCX и дополнительные представительные документы; synthetic fixtures отдельно.
- [ ] B2. Word: сверить все 41 OMML, графику/OLE/WDP/EMF, таблицы, поля, шрифты и порядок; документировать расхождения оригинального Word и производных изображений. По §157 exact bounds/scale/no-rotation для трёх оставшихся OLE подтверждены; §158 source font inventory completed, run→render font mapping remains open. Эффекты, инвентаризация и PNG не заменяют полноценную визуальную эквивалентность.
- [ ] B3. PDF: полный V4 реестр покрытия; raster/mixed/merged таблицы, мелкие подписи, минусы/десятичные знаки/единицы, связи значений и заголовков, графические обозначения. Проверять ошибки, а не только число обработанных страниц.
- [ ] B4. img2table/Paddle/Docling использовать по измеримому приросту. Paddle проверять только с лицензированными заранее доступными локальными моделями; отсутствие модели явно UNAVAILABLE. Исследованные резервы не устанавливать автоматически.
- [ ] B5. Закрепить поддерживаемый объём и эталонные проверки в regression corpus. Критические числа/единицы/знаки/связи на квалифицированных областях должны совпадать с эталоном; пропуски и ошибки явно блокируются, полнота не выдается без основания.
**Выход B:** №13 закрывается только при подтверждении всех заявленных критериев. Если исходная Word-эквивалентность не достигнута, ограничение остаётся открытым; изменение требований отдельно согласуется, а не скрывает пробел.

### C. CAD и сквозной интерфейс — №17/11
- [ ] C1. Реальный DWG→DXF: сопоставить сущности, геометрию, единицы, размеры, слои, текст, xref и предупреждения. Source hash и ведомость потерь обязательны.
- [ ] C2. Проверить контролируемую аннотацию производной копии, export/reimport и roundtrip в поддерживаемом объёме. Неподдерживаемые объекты не терять молча.
- [ ] C3. Полный UI: источник→область→варианты→ручная сверка→доказательство→черновик; сохранить чат/задачи/history/resume. Проверить большой файл, перезапуск, отмену, повтор и неверный источник.
**Выход C:** пользователь может воспроизвести квалифицированный маршрут без скрытых ручных обходов.

### D. Инженерная проверка — №6/14
Нормативная подготовка может идти независимо; solver/export на ПК остаются отложенными до возобновления пользователем.
- [ ] D1. Для требований ТЗ закрепить действующие применимые источники: документ→редакция→область→пункт→требование→факт→вывод; неизвестные нормы не выдумывать.
- [ ] D2. После возобновления расчётов: ЛИРА2024 input/results, KE57/жёсткости, материалы, нагрузки/сочетания, units/IDs, solver warnings, связь source→model→completed run→results. PR102 не объединять как qualified exporter без доказательств.
- [ ] D3. SCAD: сначала установленная версия/headers/ABI/право vendor execution; затем read-only adapter и контрольные схемы. Текущий SDK adapter NOT_IMPLEMENTED, наличие пакета не означает выполнение.
- [ ] D4. Реальный объект с полным ТЗ и проверенными основаниями пройти от ввода до положительного FINAL AUDIT. Реальные дефекты/нехватку данных исправлять или честно сохранять BLOCK; ACCEPTED не получать снятием защит.
**Выход D:** инженерно подтверждённый кейс и traceable выводы. Если SCAD входит в обязательный объём выпуска, он проверяется; отсутствие SDK остаётся открытым ограничением.

### E. Завершить рабочие сценарии — №15/16/18
- [ ] E1. Реальный ACCEPTED→knowledge→recall; отмена принятия/устаревание источника должны отзывать основание и запрещать некорректное повторное использование.
- [ ] E2. Из того же кейса выпустить DOCX/PDF: источники, таблицы, изображения, нормы и выводы; визуально сверить оба файла и историю изменений.
- [ ] E3. Ollama qwen3:8b live inference на локальном ПК и end-to-end receipt/source-page regression проверены; Windows PR CI прошёл. Open WebUI API mapping покрыт loopback tests, но live service на ПК UNAVAILABLE (8080 не слушает); optional-provider receipt/gate не квалифицирован. E3 остаётся OPEN до проверки выбранного полного локального набора.
**Выход E:** проверенные память, отчёт и локальный AI-сценарий.

### F. Надёжность и пользовательская установка — №9/12/11
- [ ] F1. Backup→новая папка/машина→restore: sources/SQLite/settings/history/keys/derived; hash/identity проверяются, чужие/повреждённые архивы отвергаются.
- [ ] F2. Подготовить воспроизводимый installer/launcher и понятную инструкцию. Проверить fresh Windows, cold/repeat/restart/reboot, большие документы, прерванные задачи, восстановление и локальный Ollama.
- [ ] F3. Проверить optional pywebview физически, если включается в выпуск; текущий web UI должен оставаться работоспособным. Проверить обновление и откат без потери данных.
**Выход F:** реальная установка на пользовательском ПК подтверждена отдельным протоколом, не подменяется CI.

### G. Финальный выпуск — №19
- [ ] G1. Повторить release checklist всех19 пунктов и подтвердить обязательные критерии выбранного поддерживаемого объёма; ни один обязательный OPEN не скрыт.
- [ ] G2. На финальном release head пройти необходимые CI/security/browser/real-file проверки, сверить состав зависимостей, лицензии и локальные модели.
- [ ] G3. FINAL RELEASE AUDIT: исходники не изменены, выводы доказаны, ограничения известны, backup/restore и clean install воспроизводимы.
- [ ] G4. После gates оформить main/release/tag, changelog, install/update/rollback инструкции и ссылки на QA.
**Выход G:** стабильный выпуск. Инженерное ACCEPTED конкретного объекта и качество продукта учитываются раздельно.

## Как обновлять план после каждого результата
1. Работать сначала над одним текущим шагом; независимые задачи допустимы при сохранении главного приоритета.
2. После существенного результата обновить этот master-plan, ENGINEER_OS_PROJECT_MAP.md и docs/development/project-map-handoff.md в docs/project-map-handoff-20261005.
3. Записать: дата; №/шаг; что реализовано; что проверено тестами; что проверено на оригинале; branch/PR/head/tree; команды/результаты/skips; QA IDs/hashes; merged/PC/engineering status; оставшиеся ограничения; следующий шаг.
4. Чекбокс отмечать только при выполнении критерия; IN_PROGRESS не является DONE. FAILED/UNAVAILABLE/NOT_RUN не заменять PASS.
5. PASS не переносить между heads. Малые проверенные code checkpoints своевременно публиковать; репозиторий не дублировать архивом в Library.
6. Список upstream вести с уровнями: RESEARCHED / DEPENDENCY_ONLY / ADAPTER_IMPLEMENTED / REAL_RUN_VERIFIED / MERGED / PC_VERIFIED. Их не объединять словом «добавлено».

## Журнал продвижения
| Дата | Шаг | Сделано | Осталось | Текущий/следующий |
|---|---|---|---|---|
|14.10.2026|E3 / №18 локальный receipt|PR147 merged 091edd1c2881b1f7c416034b45c1d6f48899bcdd; exact PR-head Core/Windows/Guard/CodeQL SUCCESS; candidate push Core1012/1013,Windows213/214,Security829/830,push599 SUCCESS; локально qwen3:8b inference PASS; добавлен end-to-end source receipt/hash/provenance test и Windows CI trigger.|OpenWebUI live unavailable на ПК (8080); optional-provider receipt/gate не квалифицирован; №18 PARTIAL; №13 OPEN.|№6 D1, затем оставшиеся независимые пункты перед возвратом к №13|
|12.10.2026|B2/B3 второй проход|PR141 merged; Word field context/PDF no-oprotation исправлены;12realHTTPregions,1044Core/145Windows/QA|OriginalWord reference/fonts;9/12OCRmismatches;fullgraphicsemantics/corpus|№13/B2+B3|
|12.10.2026|A1–A4, частично B|LibreOffice/hOCR и native conflicts исправлены; PR140 merged, freshCI SUCCESS, QAversion1|B2+B3, fullqualifiedcorpus; №13 OPEN|№13/B2+B3|
|12.10.2026|План выпуска|Сверены карта §§133–137, master-plan, отбор Word/PDF/CAD/ЛИРА/SCAD, PR102/139/140 и CI PR140; сформирован порядок A–G|Реализация A1–G4; старые PASS не повторялись в этом проходе|№13/A1 — начать воспроизведение LibreOffice|


---

## Исторические сводки до плана выпуска 12.10.2026
Следующий текст сохранён для истории. Его ранние «актуальные» заголовки и статусы не заменяют активный план выше; текущий пункт указан в активном плане выше.

# Актуальный результат — §133 итог — PR139 MERGED; кандидат1a765fa1766add7b5c5950a98893cd6e8099c6f8/tree f750e239a41e90099313b234170059b8c213e60e. Core964/Windows69/Security SUCCESS;6 Chromium и real Ollama PASS. Source-region native/PNG/OCR/history реализован; V4 −0,450/44/38 recovered,788cell serialization differences clarified. Word visual audit41OMML/11WDP/19EMF/493derived pages остаётся QA, не authoritative production render. №13 открыт: точность raster/mixed/OCR, source layout и qualified corpus. №14/19 открыты,ПК не обновлён,расчёты отложены;8✅/8🟡/3❌.

# MASTER PLAN — ENGINEER OS

Единая нумерация: **19 пунктов**. Эта сводка заменяет противоречащие текущие статусы планов17/19; история сохранена в `master-plan-17-history.md`, `master-plan-19-history.md` и живой карте. Результат нельзя переносить между планами по номеру без названия и критерия.

**Активный план (11.10.2026):** §132 итог — PR137 MERGED, кандидат 93dd656bd57c02e3997abb8870583d59bbb37c49, дерево 51365a6dedae556e683bdbd5e6d6f409ec122a22. Core 943 / Windows 55 / Security SUCCESS; 6 Chromium маршрутов и реальный Ollama PASS. Real DOCX: 14684 native элементов, 704 актива, 11 WDP-привязок, все 21 OLE bitmap/raw/PNG/checkpoint сверены. V4: 534 рендера, 43 OCR-кандидата. №13 остаётся открытым: visual Word/formula/graphics, raster/mixed cells, OCR conflicts и qualified corpus. №14/19 открыты; ПК не обновлён, расчёты отложены; 8✅/8🟡/3❌.

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
| 13 | Production completeness документов | ❌ полностью не закрыто | §133 итог: PR139 merged1a765fa,Core964/Windows69/Security PASS. Source-region native/PNG/OCR/history и V4−0,450/44/38 recovered;788cell serialization parity. Word41formula/11WDP/19EMF/493derived visual audit;productionWordlayout/rastermixed/accurateOCR/qualifiedcorpus incomplete. |
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
| 13 | Производственная полнота документов | ❌ Открыто | PR108 merged,e0754b2:real DOCX14684/14684 послеresume,749/749 controlled-model batches;V4 render534/534 и40OCR candidates. Qualified tables/graphics/formulas/OCR/Word-layout/corpus не подтверждены (§92 итог). |
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

### Итог §92 — PR108 объединён; №13 остаётся открытым

PR108 MERGED с expected-head guard. Кандидат **e0754b2a3dcfb24a55e68af9333ec9d35a67618f**, tree **5dd2b66194be961a73dd68a2601b48ac6c778611** точно совпадает с проверенным head70db597b178e419428588ab63aa6dec4b71af157. GitHub Core38002094577 SUCCESS:857 tests/2 Windows-only skips;Windows38002094533 SUCCESS:55 tests,live Ollama и5 Chromium маршрутов;Security38002094570 SUCCESS.

Полный исходный DOCX после штатного resume завершил Store/Worker/controlled-model:SUCCEEDED,14684/14684 journal units,0 truncated,749/749 batches,summary_input_clipped=false,text_omitted=false,budget_exhausted=false. Отдельное повторное чтение SQLite подтвердило сохранённый результат;1492 сохранённых receipts(1491 COMPLETED,1 RUNNING),1496 model calls. Это расхождение требует сверки;полнота real receipt журнала НЕ подтверждена,несмотря на SUCCEEDED и749/749 в job report. Модель controlled office-test-1,не live inference пользователя. Первый запуск FAILED14505/14684;его причина не установлена,повтор не выдаётся за исправление неизвестной ошибки.7031 логический элемент сохраняет ограничения/недостаток подтверждения;это не7031 дефект конструкции. SHA оригинала неизменён. Native сохранение проверено отдельно по base:14684 units,671 refs,3394 EMF text-record refs.

Финальный повтор V4 audit завершён:534/534 PNG,source SHA неизменён,40/40 страниц492–531 с OCR candidates,62189 chars,1682 low-confidence blocks. Пер-page bbox/native SHA/PNG SHA/OCR SHA сохранены. Это воспроизводимый визуальный реестр и непроверенные кандидаты;структура таблиц,точность подписей,формулы и смысл графики не сертифицированы. Полный Word-layout export LibreOffice не завершён в ограниченном локальном пробном запуске;эквивалентность Word/V4 и применение колонтитулов/сносок к страницам не подтверждены.

**№13 НЕ ЗАКРЫТ.** Реальный пробел:qualified соответствие mixed/raster ячеек и графических подписей источнику,визуальная сверка41 OMML формулы,OCR exactness/conflict adjudication,полная Word/EMF layout проверка и представительный multi-document corpus. Не ослаблять критерии до счётчиков. Следующий проход должен закрывать именно эти информационные потери и эталонные сверки. №14/19 остаются открыты;план8✅/8🟡/3❌. НаПК пользователя не установлено,инженерно не принято;ЛИРА/RES/расчёты отложены. JSON receipt:`docs/qa/2026-10-10-document-visual-coverage-ci.json`.

## 11.10.2026 — следующий информационный пробел №13

§130: native PDF table V2 сохраняет индивидуальные cell/header coordinates, unresolved slots и rotation/source identity. Реальная таблица V4 стр.15:24/24 native значения/rectangle сверены; raster/mixed content остаётся не подтверждён. Кандидат до интеграции c52cfb4. Полный app→Supabase replay не заменён capture transport; критерии №13/14/19 остаются открытыми. Далее — source-bound raster/mixed cell content и графические подписи через существующий application route. ЛИРА/RES отложены.

Публикация §130: PR135 head1a9e0c93d2e31376dfafbea33afc78b04eb12734, full910 OK/17 skips; Core/Security выполняются, MERGE не подтверждён. Другие open browser PR130–134 не включены; не повторять их реализацию.

### Итог §130 — PR135 объединён в кандидат

PR135 MERGED squash с exact expected head1a9e0c93d2e31376dfafbea33afc78b04eb12734. Новый кандидат **4641743a6da1086be75649a5e34c896283842888**, tree3892ae0af7a0cab3b51f5157b3c7c952e14ddea1 совпадает с проверенным локальным/PR деревом. Final-head Core38120688580 и Security38120688628 SUCCESS. Core910 tests/95.747s OK,2 Windows-only skips;HTTP/DOM иexisting Chromium routes PASS. Отдельный Windows workflow нового изменения NOT_RUN (DI-only path filters), physical PC NOT_RUN. Real V4 native sample24/24 сохранён и сверён;оригинал неизменён. Raster/mixed semantics,OCR/graphics/Word/EMF/OMML/corpus иlive app→Supabase остаются открыты;№13/14/19 НЕ закрыты,8✅/8🟡/3❌. Следующий проход — растровые/mixed значения с cell/source geometry через существующий application route. Расчёты отложены.


## Проход №13 — §131,11.10.2026

PR136 добавляет user HTTP/UI readback безпринятия;915local tests PASS/17skips. Полные реальные V4/DOCX сверены структурно;конкретные потери/неподтверждённые представления перечислены в§131 иQA. №13 остаётся OPEN,6document gates BLOCK. Не подменять qualified completeness source hashes/counts/CI. Расчёты отложены;ПК не обновлён.


### Итог §131 — PR136 объединён, №13 остаётся открытым по фактическим пробелам

PR136 MERGED expected head54d86a160e4a0161d1a886e380c5192b6b97940e → candidate9e253567a3eaa2fbc024a1a05fd960da5e4206ac,tree92c3ed2e6e849d96830ee40ca79b5467f86de136. Core38127002376 SUCCESS:915tests/97.717s,2Windows-only skips,HTTP/DOM и6Chromium routes включаяnewnative-table-user-readback. Windows38127002396 SUCCESS:55tests/14.979s,cold start/repeat/restart,real Ollama qwen3:0.6b inference и6browser routes. Security38127002368 SUCCESS. Полноеcandidate tree совпадает с опубликованным иlocaltested tree. Local915/17skips;independent finalreview Critical/Important нет. На пользовательскомПК не установлено. Document qualification6/6BLOCK;№13не закрыт,originals unchanged,engineering ACCEPTED не выдан. Следующая независимая работа — конкретные representational/visual/corpus gaps,неЛИРА.


## Актуальный проход§132

§132 — PR137 OPEN, heade2570bce0425cdb4420ef700b569f380ad538b94; реализованы source-bound WDP layer bindings, passive OLE bitmap preview HTTP/UI и sparse V4 OCR routing. Local943tests PASS/17skips, независимый review PASS. Реальные21PBrush bitmap pixels сверены;V4 all534renders/43OCR candidates,конфликтыП1→111 ив→6 остаются. Full original native Store/HTTP checkpoint proof иfinal-head CI выполняются. №13 OPEN поqualified Word/formula/graphics/table/corpus,№14/19 OPEN;ПК не обновлён,расчёты отложены;8✅/8🟡/3❌.




### Проверка полного исходного DOCX и исправление ранней загрузки

Реальный источник 147210288 байт / SHA256 b253439bdd673a775eaf209ca7d398d766efae5f4a18ac33fa6679f7faae28a5 прошёл authenticated HTTP upload/original download byte equality. Полный inventory: 704 кандидата = 683 прежних + 21 OLE. Все 21 raw OLE hash и derived PNG pixels совпали. Production office.execute в автоматическом EXTRACT_DOCX child сохранил 14684/14684 логических элементов, 1366524 символа; cycle_complete=true, errors=0, budget_exhausted=false. Все 21 checkpoint-bound object PNG сверены. Оригинал неизменён. Выполнение 538.94s. Это полный native Store/HTTP checkpoint route, не полный Worker/model inference большого отчёта; model_inference_performed=false. Сквозной Worker/model/receipt проверен на контролируемом документе. JSON QA: docs/qa/2026-10-11-docx-layer-ole-coverage.json.

Начальный head e2570bce0425cdb4420ef700b569f380ad538b94: Core38144958474 SUCCESS (943 tests/103.218s, 2 Windows-only skips, HTTP/DOM и 6 Chromium маршрутов, включая OLE inventory/checkpoint); Security38144958468 SUCCESS. Windows38144958476 attempt1 упал на существующем intake .file wait; attempt2 того же head SUCCESS. Дополнительное исследование воспроизвело реальную причину: HTML upload enabled до current session, ранний change молча игнорируется. Delayed-bootstrap DOM regression RED→GREEN; upload теперь disabled до появления диалога, дальнейший upload/worker/history PASS. Await ограничен по времени и gate освобождается при любом выходе. Новый итоговый head 8fd34f7fead37c389b77c24f781e24328d55fc82 / tree 51365a6dedae556e683bdbd5e6d6f409ec122a22 совпадает с локальным деревом; его свежий Core/Windows/Security требуется до merge. Новый итог не переносит ранние CI на изменённый head.


### Итог §132 — PR137 объединён, реальные потерянные представления добавлены

PR137 https://github.com/maxim505885-jpg/engineer-os/pull/137 MERGED с expected-head 8fd34f7fead37c389b77c24f781e24328d55fc82. Новый кандидат **93dd656bd57c02e3997abb8870583d59bbb37c49**, tree **51365a6dedae556e683bdbd5e6d6f409ec122a22** полностью совпадает с локальным и опубликованным проверенным деревом. Final-head Core38145680188 SUCCESS:943 tests/89.055s,2 Windows-only skips,HTTP/DOM и6 Chromium маршрутов, включая delayed-bootstrap regression и OLE inventory/checkpoint PNG. Windows38145680312 SUCCESS:55 tests/65.467s,cold/repeat/restart,real Ollama qwen3:0.6b и6 browser routes с обоими OLE просмотрами. Security38145680348 SUCCESS. Неподтверждённая ранняя ошибка Windows не скрыта: прежний head attempt1 timeout, attempt2 PASS; причина дополнительно воспроизведена DOM и исправлена в final head. Последний независимый review: Critical/Important нет; minor unbounded bootstrap wait исправлен, gate освобождается на всех выходах.

**Реализовано:** 11 HD Photo/WDP layer bindings с правильным hdphoto relationship; 21 internal OLE object source binding; bounded passive bitmap extraction и authenticated raw/PNG/checkpoint UI; sparse-native graphic OCR routing; expected-source-SHA preflight; раздельные image/object/global budgets; барьер загрузки до создания диалога. **Проверено на реальном файле:** оригинальный DOCX 147210288 байт/SHA b253439bdd673a775eaf209ca7d398d766efae5f4a18ac33fa6679f7faae28a5 — reader14684,images682/layers11,OLE21; все source hashes совпали. Fresh Store HTTP inventory704,all21 raw OLE hash и PNG pixel matches; original download equality; production native automatic EXTRACT_DOCX child14684/14684,1366524chars,0errors,no budget exhaustion;all21checkpoint previews match. Original unchanged,elapsed538.94s. Это native Store/HTTP route без model inference большого документа. Controlled Store/Worker/model/receipt route PASS; source_only/UNCERTAINTY, evidence0, acceptancefalse.

**V4:** правильный исходник 74522583 байта/SHA b5d95b660b35bfb6b2441623635cba91c235efd754bc283dfe1405f075834916 неизменён. All534renders и43pages492–534 rus+eng OCR candidates complete,errors0.12809words/2615blocks/66349chars,1841blocks confidence<60. Все534render и43OCR/source/hash bindings сверены. Ошибочный local4b источник исключён; источник восстановлен из доступногоDrive отдельно, originalcopies не перезаписывались. Crop493 title совпал; реальные П1→111,в→6 и joined legend columns остаются UNCERTAINTY. 534 страницы и43 OCR не подтверждают полноту содержания.

**№13 НЕ ЗАКРЫТ:** не подтверждены полный Word render/layout/fonts/fields и41 OMML visual equivalence;WDP composition и19 EMF comments;resolved real raster/mixed values и48page cell conflicts;точность всех V4 labels/units/geometry/associations;representative qualified multi-document corpus. Ошибки OCR — ошибки извлечения, не доказанные дефекты конструкции. Математическая/расчётная проверка не возобновлялась. №14/19 открыты;8✅/8🟡/3❌. На пользовательскомПК не установлено, инженерно ACCEPTED не выдан.

Доказательства: ENGINEER_OS_stage13_pass2_audit_20261011.zip, libfile_d624929a93b481918bbcf84d85648581, version0,1955742 bytes,SHA2564769a6de99bae051085dfeab8f39943b9b2166cb702d9b43ca31046161a4c4b0;117 payloads с отдельным SHA manifest. QA docs/qa/2026-10-11-docx-layer-ole-coverage.{md,json},ole-bitmap-decoder.md,v4-graphic-ocr-43.{md,json}. Следующая независимая работа — адресная source-bbox сверка raster/mixed ячеек и OCR conflicts с сохранением unverified статусов;не возвращаться к ЛИРА без нового указания.


## 133. 11.10.2026 — адресное чтение исходного PDF, реальные cell/OCR и Word visual gaps

§133 — PR139 опубликован: source-bound PDF fragment native/PNG/OCR + append-only history, PSM6/11 и сохранение controls при poll. Headd7d4dea14cd012a9cb50bb7cd80cc7eefdde6476/treef750e239a41e90099313b234170059b8c213e60e; локально964 Python/10 Node/HTTP-DOM PASS; новый CI выполняется, merge ещё не выполнен. Кандидат пока93dd656. №13 открыт по точности OCR, Word layout и qualified corpus; расчёты отложены, ПК не обновлён;8✅/8🟡/3❌.

**Программная реализация:** authenticated local selected-source readback сохраняет page/bbox/hash, PNG, native words и optional local rus+eng OCR. PSM6 — блоки текста, PSM11 — разрозненные подписи; candidates/conflicts не заменяют source. Append-only SQLite history reload/reopen, SHA целостности record/source, exact worker request/page/bbox/status/render/dossier validation. Лимиты source/result/history и2 slots, process timeout с остановкой потомков. GET также ограничен. DOM воспроизвёл потерю результата при delayed1800ms response/1500ms poll; per-file/session controls сохраняются, session switch очищает их. Независимый review воспроизвёл 3 дефекта: orphan OCR child, unbounded parent hashing, wrong selection/quality worker protocol; исправлены регрессиями. Native Windows descendant termination требует нового CI.

**Проверено на настоящем V4:** source74522583bytes/SHA b5d95b660b35bfb6b2441623635cba91c235efd754bc283dfe1405f075834916. HTTP p493 raster legend и p534 numeric/level, сохранение/read/reopen совпали, evidence0, source unchanged. PSM11 действительно извлёк −0,450/44/38, которые PSM6 не прочитал. П1 и пары17/8,19/11,20/13 полностью не recovered; соседние9 и geometry/units/association не подтверждены. Empty native vs OCR не выдаётся за verified agreement.

**Уточнение прежних788 cell differences:** свежая независимая сверка всех48pages обнаружила lost0/added0 detector-selected nonspace chars; same-flags native center membership matches788/788. Причины прежних rawclip differences: boundary/accurate glyph boxes и fill/stroke overprint dedup. Naive replacement привносит соседние строки/повторные цифры; detector values не изменены. Это serialization parity, не qualified semantic/table completeness.

**Реальный DOCX visual readback:** все11 JPEG XR originals декодированы и сопоставлены с11 готовыми source-cached effect blips/effect XML. В19 EMF прочитаны112 EMF+ comments/315records, drawing/text payloads0, все Dual; original vs comment-stripped passive renders pixel-identical19/19. 41 OMML full XML equaloriginal,41 formula pages/crops просмотрены, missing-glyph/clipping не обнаружены; substitutedLiberation/OpenSymbol fonts не подтверждают Word/Cambria Math equivalence, математические расчёты не выполнялись. 71 source fields inventoried, не evaluated. Полный неизменённый DOCX export timed out300s/low-DPI420s/cached-preview300s/PageRange1 60s. Производный cached-preview вариант с разделением4 tables>80rows успешно export120s:493pages/24993047bytes/SHA301e449965de13cac64de6ecdd219d7958f736a0fc82fc263ce2ecbe9c372d23; все493 rasterized. Source cells12826 и paragraphs15651 preserved order AFTER explicit passive-preview removals21OLE activation/11imgProps; exact-original12801cells/15623paragraphs,all41formulas exact. Layout changed; representative10pages выявили overlap/wrapping и font substitutions. Поэтому authoritative/full quality NOT_VERIFIED; derived render не original physical pages.

**Верификация до публикации:**964 Python PASS/85.375s,2 Windows-only skips;14 safety+HTTP PASS после request-binding fix;10 Node PASS,HTTP/DOM delayed readback PASS; architecture/compile/JS/diff PASS. Security38148354650 SUCCESS; Core38148354660/Windows38148354687 pending. Final head/tree сверены с локальным staged tree. Нет нового full Store/model inference большого отчёта, PC installation или engineering acceptance.

**Остаток№13:** точность raster/mixed table values и association/merged semantics, allV4 graphic labels/units/geometry/text links, originalWord render/fonts/field/page layout and visual formula equivalence, representative qualified corpus. №14/19 открыты;8✅/8🟡/3❌. НиBLOCK, ниOCR error не означают доказанный дефект конструкции; ЛИРА/RES отложены по указанию пользователя.

Доказательства: ENGINEER_OS_stage13_source_readback_20261011.zip,libfile_6a4e2c88f07881919d035e8afb966d66,version0,31694103bytes,SHA cf921ff9898487f8d8dcb67398c1f85bf290aeba73d9114d221ba060f5e0d436,71payloads inclderivedPDF/sourceproofs/reproscripts. QA docs/qa/2026-10-11-source-region-readback.{md,json},word-visual-manifest.json,word-visual-readback.md. Следующая работа: вручную источник-сверенные эталоны значений и reader profiles для raster/mixed/graphic corpora; производная верстка не засчитывается как оригинальная.


Уточнение §133 final head: выбранная ячейка теперь привязана к странице загруженного inventory даже после изменения page control; regression входит в Chromium маршрут. Head d7d4dea/tree f750e23 совпадает с локальным. Windows actual timeout descendants/request history включены в native CI; новый final-head CI выполняется, предшествующий head не переносит PASS на новый.


### Итог §133 — PR139 объединён; полнота №13 не объявлена

PR139 MERGED с expected-head d7d4dea14cd012a9cb50bb7cd80cc7eefdde6476. Кандидат **1a765fa1766add7b5c5950a98893cd6e8099c6f8**; tree **f750e239a41e90099313b234170059b8c213e60e** полностью совпал с finalhead и локальным деревом. Core38148354660 SUCCESS:964tests/107.117s,2 Windows-only skips,HTTP/DOM delayed-readback+6 Chromium routes, selection/history reload. Windows38148354687 SUCCESS:69tests/56.010s без skips, native worker/descendant timeout и request/source/history integrity, cold/repeat/restart, realOllamaqwen3:0.6b+6browserroutes. Security38148354650 SUCCESS. Все доказательства относятся к finalhead; промежуточный561fecd не использован для merge.

**Реализовано и merged:** выбранный source-bound PDF region native/PNG/OCR, explicit6/11profiles, preservedconflicts, append-only history/reopen, validatedscope/status/raster/dossier/hash, boundedprocess/source/history, actualchildcleanup onWindows/Linux, UIpoll retention, loaded-cell-page binding. **RealV4 проверено:** unchangedoriginal,threeHTTPregions/history/reopen,evidence0;psm11 recovers−0,450/44/38;П1/numericpairs/neighbour9 remaininaccurate. **Independentrealcell audit:**48pages/788differences,detectorselectedtextlost0/added0; это не qualifiedfulltablegeometry/semantics.

**Word visual evidence — только отдельный QA-прогон:**41sourceOMML visual crops,11decodedWDP/cachedeffectpairs,19EMF with112comments/315EMF+records and identicalpassivefallback. Derived493-pagePDF fullyrasterized;41formulaoriginalXMLexact,12826cells/15651paragraphs order preserved AFTER explicitpassivepreview21OLE/11imgProps removals. Original/layout/fonts/pageplacement/fields не подтверждены; observedoverlap/wrap defects и substitutedfonts. Это не новыйproductionWordrender/decoder, не установка наПК и не математическаяпроверка.

**№13 остаётся OPEN по реальным неподтверждённым критериям:** raster/mixedtable values and relationships, fullV4graphictext/labels/units/geometry/associations, productionWordvisual/layout/font/field/formulaequivalence, representativequalifiedmultidocumentcorpus. Дальше нужна работа над этими содержательными пробелами; увеличение числа тестов или processedpages их не закрывает. №14/19 такжеOPEN;8✅/8🟡/3❌. UserPC не обновлён, engineeringACCEPTED не выдан,ЛИРА/RES не возобновлялись.

Финальный архив: ENGINEER_OS_stage13_source_readback_20261011.zip, тот жеlibfile_6a4e2c88f07881919d035e8afb966d66, **version1**,31700092bytes,SHA256 **540cedde2fb8b606413e2dd006a6a376769e38287839b8559ae5f23ebecdcbb9**;77payloads,CRC PASS,originals excluded. Включает derivedPDF, source/canonical/sourcehash proof, actualOCR readbacks, independentcells, reproduciblescripts,finalCore/Windows proofs,local964log/DOMregression. Первоначальная version0 сохранена как история, финальнаяversion1 добавила CI/merge identity.


## §134. 11.10.2026 — отбор upstream-репозиториев для Word/PDF/DWG и desktop

По новому поручению пользователя выполнен поиск через GitHub plugin и сверка официальных README/документации с текущим кандидатом **1a765fa1766add7b5c5950a98893cd6e8099c6f8**. Отбор и ограничения: [docs/development/document-tooling-repositories-20261011.md](document-tooling-repositories-20261011.md).

Приоритет №13: производственное визуальное чтение Word через существующий LibreOffice-контур; затем ограниченный пилот PaddleOCR PP-StructureV3/img2table на проблемных областях V4 и сравнение с уже имеющимися native/Tesseract/Docling. GMFT — резерв native таблиц без собственного OCR; PDF.js — просмотр исходника. Для CAD сохраняется имеющийся ezdxf и отдельный LibreDWG-конвертер, с учётом неполноты и проверки потерь. pywebview — будущая оболочка; Playwright уже используется. ONLYOFFICE — резерв отдельного Word renderer; docxjs не подтверждает поля/динамическую пагинацию.

**Статус: исследовано, не внедрено этим шагом.** Не установлен новый компонент, не выполнена новая квалификация файлов/Windows, не изменён runtime-кандидат. Обязательные платные API не вводятся. №13/14/19 остаются OPEN, итог **8✅/8🟡/3❌** без изменения; инженерная приёмка/обновление на ПК не объявлены. ЛИРА/RES не возобновлялись. §133 сохраняет последний проверенный программный/реальный результат.


## §135. 11.10.2026 — поиск инструментов SCAD Office и ЛИРА, расчёты остаются отложенными

По отдельному запросу пользователя проверены GitHub-репозитории и первичная документация vendor. Подробности: [docs/development/lira-scad-tooling-repositories-20261011.md](lira-scad-tooling-repositories-20261011.md).

Основной путь: существующий собственный ЛИРА2024 COM exporter/reader (PR101 MERGED, PR102 OPEN/DRAFT headb623bc3abd58adbf46432fbc4e3adb96d647235c), дляSCAD — официальный SCAD++ C API (SCADAPI.pdf2025/83pages, модель и сохранённые результаты) и адаптер по заголовкам установленнойверсии. ИзGitHub: pywin32; scadlira ограничен геометрией/закреплениями, нагрузки/РСУ не реализованы; SpaceFramer и3DFACE2HATCH — узкие вспомогательные проекты; OgibArm закрытыйfreeEXE; StructOS закрытыйdownload-only иfree-during-beta, не обязательное бесплатное ядро. pywinauto — запаснойGUIexport, PyVista — будущаявизуализация. OpenSCAD/SCADA/SCADE не смешивать сSCADOffice; ЛИРА10/2025/2026 API не переносить на2024.

**Только исследование: ничего не установлено и не запущено, новый native/result reader не реализован, реальнаяRES не получена и не запрашивалась.** Runtimeкандидат1a765fa1766add7b5c5950a98893cd6e8099c6f8 без изменения. Решение09.10.2026 об отсрочке расчётов соблюдено; №13/14/19 остаютсяOPEN,8✅/8🟡/3❌. Следующая производственная работа остаётся по№13/Word/PDF, отбор§134 сохраняется.


## §136. 11.10.2026 — локальные инструменты Word/PDF и reader результатов ЛИРА внедрены в PR140

Новое поручение пользователя: внедрить отобранные инструменты и полностью проверить доступные маршруты. Исходный кандидат **1a765fa1766add7b5c5950a98893cd6e8099c6f8**. PR140: https://github.com/maxim505885-jpg/engineer-os/pull/140, branch **feat/local-tooling-resume-20261011**, опубликованный head **7b8092fc8a62c27fac272e0a910990b55a1b4835**, tree **4edb4bb9613890ab7709e6c6a77217cfaaff6557** совпадает с локальным index. Сейчас OPEN/DRAFT: Core38173794008 и Windows38173794012 выполняются, Security38173794002 SUCCESS. В кандидат ещё не объединён, ПК не обновлён.

**Реализовано в приложении:** выбранная OMML формула -> пассивный source-bound scaffold -> локальный LibreOffice PDF/PNG с SHA исходника/формулы/шрифтов, authenticated candidate/project/identity checks и UI; nearest-ancestor WDP/cache bitmap+ordered effects; strict EMF+ comment/record inventory; optional isolated img2table1.4.2/Tesseract и Paddle PPStructureV3 с заранее установленными local models для выбранного PDF bbox; vendored offline PDF.js5.4.624 pages/zoom; strict R4 result ZIP reader до input/generic archive dispatch. Optional pywebview wrapper использует прежние Store/Worker/server/DataLock. Optional PyVista requirements — только подготовка будущей визуализации. Уже имеющиеся Docling/ezdxf/LibreDWG/Playwright не переписаны. Обязательные платные API не добавлены. Closed/beta/узкие upstream инструменты не установлены автоматически как ядро.

**Свежая локальная проверка:**1019 Python tests OK/82.616s,21 environment skips; genuine img2table11/11;10dashboard tests; HTTP/DOM;6 прежних Chromium routes+новый actual-app tool route; отдельный offline PDF viewer DOM/Chromium; architecture/compile/JS/staged diff checks PASS. Установлен отсутствовавший pinned olefile0.47 из существующих requirements, что восстановило прежний OLE preview без изменения decoder. Independent review воспроизвёл и исправил tail-inclusive formula identity, blank PNG acceptance, nonstandard auxiliary part rejection, Windows resource imports, inverted clip geometry и model-config mismatch; финальные56focused tests/3skips+11genuine table+Chromium PASS.

**Проверено на оригиналах:** DOCX147210288bytes/SHA b253439bdd673a775eaf209ca7d398d766efae5f4a18ac33fa6679f7faae28a5,14684logical units;11WDP/cache associations,12effects,19unique EMF+/112comments/315records. Реальный authenticated HTTP по формулам0/20/40 совпал по candidate/source/formula hashes; все три производных PNG построены, evidence0, source unchanged. V4 PDF74522583bytes/SHA b5d95b660b35bfb6b2441623635cba91c235efd754bc283dfe1405f075834916: PDF.js действительно показал первую и последнюю534-ю страницы; HTTP img2table source region p5 bbox[80,60,550,720] вернул1candidate table/5cells. Synthetic ruled table12cells и merged header11cells/span2 проверены реальным Tesseract/img2table. Локальный OCR в этом доказательстве eng-only: кириллица и полнота/точность V4 НЕ квалифицированы.

**Результаты ЛИРА:** strict schema1 ENGINEER_OS_LIRA_RESULTS_EXPORT, exact10cols/part hashes/rows/safe ZIP/finite values, actual requests1–4/8 отдельно от availability probes5–7/9/10; ноль является значением, sparse IDs сохранены. Whole-run claims и per-part observations различаются; observed rows должны укладываться в per-request claims, включая EXPORTED из ранних chunks при позднем UNAVAILABLE. Reader не доказывает завершённый solver run или model-result association. PR102 exporter остаётся DRAFT/UNMERGED, реальная RES не получена/не запрашивалась, расчёт на ПК не запускался.

**Границы:** Word full layout/physical pages/fields/font and formula visual equivalence не подтверждены; эффекты/EMF+ graphics state не применены, математическая корректность не проверена. Paddle реальные веса/инференс, physical native desktop и SCAD SDK adapter остаются неподтверждёнными/не реализованными соответственно. Windows network-denial=false отражает отсутствие OS enforcement; taskkill после завершения основного worker не гарантирует очистку уже orphaned descendants. Проверка наличия SDK/пакета не выдаётся за выполнение. Документация: docs/development/local-document-tooling.md, docs/local-tooling/offline-raster-tables.md, scripts/LOCAL_DESKTOP_AND_PDF.md.

**№13 остаётся OPEN:** qualified fullV4 graphic/raster/mixed table semantics/links, originalWord visual/layout/fonts/fields и представительный корпус. №14/19 такжеOPEN; **8✅/8🟡/3❌**. Новый шаг программно расширяет извлечение/просмотр, но не закрывает инженерную полноту и не означает обновление ПК. Далее — final-head CI/merge при успехе и источник-сверенные эталоны с кириллическим OCR для проблемных областей.


### Уточнение §136 — Core выявил несовместимость distro LibreOffice; merge остановлен

На head7b8092f Core38173794008 FAILED:1020tests/179.680s,1failure/1error/4skips; конвертация формулы Ubuntu LibreOffice завершилась exit1. Windows38173794012 SUCCESS:125tests/30.758s,9skips; actual cold/repeat/restart, realOllamaqwen3:0.6b, offlinePDFviewer и7UIroutes, формулы наWindows честно UNAVAILABLE безLibreOffice. SecuritySUCCESS. Эти результаты не переносились на новый head.

Опубликован диагностический headd2ed01389a02a6a953c4f3c579d20183ee8e37d5/treec89a0368eea83ae28df4017092efac79e6064808: bounded stage/exit/log diagnostic, condition-based waiting for asynchronous SIGKILL in tests, fast actual formula CI. Core38174414604 сноваFAILED только actualLibreOffice: conversion.log exit1, warning javaldx; skipactualtest не введён. Причина исследуется, merge не выполнен. Windows38174414644 выполняется, Security38174414687SUCCESS.

Дополнительная локальная actualHTTP проверка предыдущего renderer adapter охватила **все41sourceOMML** с exact source/candidate/formula/PNG hashes, evidence0, unchangedoriginal. Это проверка41производныхPNG, не Word/font/math equivalence; adapter identity каждого прогона сохранён. Дляimg2table обнаружены реальные ограничения: eng-onlyp5 дал5сомнительныхcells, rus+engp5 и genuinep55table дали0tables; данные не объявлены прочитанными/подтверждёнными. Source原本неизменён; №13 OPEN.


## §137. 12.10.2026 — полная передача продолжения, сохранность кода и два незакрытых дефекта

По поручению пользователя сохранены подробный промпт нового чата и диагностический черновик. Читать [docs/development/continuation-prompt-20261012.md](https://github.com/maxim505885-jpg/engineer-os/blob/docs/project-map-handoff-20261005/docs/development/continuation-prompt-20261012.md). Это актуальная передача после §136; старые сводки не заменяют проверку GitHub.

**Заново подтверждено GitHub:** PR140 OPEN/DRAFT/NOT_MERGED, headd2ed01389a02a6a953c4f3c579d20183ee8e37d5, treec89a0368eea83ae28df4017092efac79e6064808; base/candidate1a765fa1766add7b5c5950a98893cd6e8099c6f8. Core38174414604 FAILURE, Windows38174414644 SUCCESS, Security38174414687 SUCCESS. Новый кандидат не объявлен, ПК не обновлён. Уточнение§136 «Windows выполняется» теперь устарело: проверка завершилась успешно, но actualWindowsLibreOffice/Paddle/vendor исполнение этим не подтверждено.

**Сохранено в промпте:** перечень опубликованных модулей/API/requirements и конкретных проверок; реальные DOCX/PDF/ЛИРА identifiers/SHA/limits; отличие upstream research от внедрения; критерии №13/14/19; отсутствие реальнойRES/model-result association/SCAD SDK adapter; порядок диагностики, CI, review, merge и обновления карты. Исходники не изменялись.

**LibreOffice blocker:** Ubuntu conversion.log exit1, толькоwarningjavaldx. Причина не установлена; Math package установлен. Нельзя выдавать warning за причину, отключать actual test или ослаблять sandbox наугад. scripts/probe_formula_runtime.py сохранён на docs-ветке как fixed-benign-fixture diagnostic prototype, толькоpy_compilePASS, НЕ выполненный production fix. Диагностическая матрица launcher/SVP/directbinary/memory/sandbox-reference предназначена для выяснения причины; контрольный unsandboxed опыт только на встроенном безопасном fixture, не на оригинале пользователя.

**hOCR blocker — последняя диагностическая находка, fix ещё не опубликован:** отдельный исполнитель установил, что detector p55 сOCR=None видит21x4/84cells, но custom TESSDATA_PREFIX безconfigs/hocr даёт plaintext вместоhOCR; parser видит0words и удаляет таблицу. В проверенном GitHubtable_worker.py head d2ed013 явного tessedit_create_hocr нет. Следующий шаг: воспроизвести, явно tessedit_create_hocr=1 сexactPNG, сохранить geometry-only candidates приOCRempty сTEXT_UNAVAILABLE, проверитьmissingconfig/genuinep55/merged cases. Не объявлять этот fix реализованным. p55sourcebbox[55,68,582,462], nativebbox[61.224,74.280,576.720,455.110]. rus.traineddata officialblob b146cb2263acbc6383f8e92ea0ce759537687bb8,3861738bytes,SHAe16e5e036cce1d9ec2b00063cf8b54472625b9e14d893a169e2b0dedeb4df225.

**Сохранность:** временныйcheckout вновь оказался72d323a; опубликованныйPR140 сохранился. Новые сырые41-formula QA PNG/JSON и последние незапубликованные агентские правки в текущей среде не подтверждены; локальныеpaths/agents/PASSне наследовать. Промпт сохраняет известные результаты как контекст сscope/ограничениями и точные задачи для восстановления, но не заменяет пропавшие сырые доказательства. Если их нет в долговременномхранилище — повторить на оригиналах, сохранитьQAmanifest/logs/PNG/JSON. Публикация малыхпроверенныхcheckpoints и идентичностьhead/tree обязательны для дальнейшей сохранности.

**Точный следующий шаг:** восстановитьfeat/local-tooling-resume-20261011 изactualremote, устранитьLibreOffice/hOCR, пройтиfreshfinalheadCore/Windows/Security+review, затемmerge/treecomparison и актуальная карта. №13/14/19 остаютсяOPEN;8✅/8🟡/3❌. Добавление библиотек не равно производственной полноте или инженерной приёмке.


## §139. 12.10.2026 — LibreOffice/hOCR исправлены; проверка конфликтов OCR/Native
По поручению закрыть №13 выполнен новый проход без снятия evidence gates. GitHub PR140 head **d2fa1d6dcf4bc7c62c25e49977028186b7631852** / tree **dce647bd734ff385d440cf9d5b4b388a338889bc**: Core38180844882, Windows38180844836, Security38180844952 **SUCCESS**. PR140 пока OPEN/DRAFT, кандидат пока1a765fa.
**Причина LibreOffice доказана CI strace:** strict seccomp запрещал AF_UNIX OSL pipes; SVP/directbinary/6GiB не исправляли, безопасный reference создавал PDF. Реализован отдельный passive-formula IPC profile: закрыты существующие sockets, разрешено только создание AF_UNIX; прямые AF_INET/IPv6 запрещены; legacy DOC/table profile сохранён строгим. Dossier явно отражает local IPC и предел direct-network guarantee; общего filesystem sandbox/защиты от Unix proxy не заявлено.
**hOCR fix опубликован:** exact source PNG на stdin Tesseract, явный tessedit_create_hocr=1 без configs/hocr/JPEG; detector geometry не пропадает при пустом OCR; текст сопоставляется по exact bbox. RED→GREEN missing-config/empty-OCR/merged cases, независимый stdin/argv regression.
**Проверено локально:**1027full tests/24skips,14genuine table tests;7Chromium routes,HTTP/DOM/PDFviewer/architecture. Review не нашёл Critical/Important; Minor о независимой проверке stdin исправлен. Новые сравнения ещё проходят собственный final suite/CI, их PASS не переносится с d2fa1d6.
**Реальные источники:** DOCX SHA b253439b… —41/41производных формул сexactXML hashes; V4 SHA b5d95b66… —534/534постраничных рендера/инвентаря,716native detections (не716qualifiedtables). ДополнительныеPDF:Графика21pages,Геодезия22pages,V3 534pages;577страниц технически читаются, семантика не квалифицирована.
**p55:**21×4/84gridpositions/74unique cells; визуальный эталон74ячеек совпал сnative extraction (0расхождений),OCR rus+eng имеет41расхождение, включаяd20→420/d16→416. Локально добавлено bounded independent native alternative comparison и видимые UIконфликты без подменыOCR/приёмки; rawQA сохраняется перед завершением этого прохода.
**Текущий шаг:** №13/A4 + B3: итоговый head,свежие тесты/CI/review,source-boundHTTP41формул иp55,QAwriteback. №13 остаётсяOPEN: fullWord layout/fonts/fields/formula visualequivalence, fullV4graphic/raster/mixed semantics иqualifiedcorpus не доказаны. ИнженерныйACCEPTED иустановкаПК не объявлены;расчёты не запускались;8DONE/8PARTIAL/3OPEN.

## §140. 12.10.2026 — PR140 объединён, стабилизация A завершена; №13 остаётся OPEN

**Опубликовано и объединено:** PR140, final head **6f33d039cf58f571e45dd39896286446f961a4e4**, кандидат **4bae5948072384f271376eb15c14c81fcbfdec1c** в integration/release-candidate-v1. Tested/merged tree **2592b7c2714db2c80d047fea9ccf7dca8ff887a5** идентичен по git rev-parse. Core **38204983979**, Windows **38204983966**, Security **38204983889** SUCCESS на final head. Core1035tests/160.313s/7skips; Windows136tests/43.757s/12skips. Local1035tests/86.166s/25environment skips. Пропуски не объявлены выполненными проверками.

**Исправлено:** LibreOffice passive-formula AF_UNIX IPC с закрытием прежних sockets и запретом direct INET; exact PNG/hOCR без зависимости от configs/hocr; сохранение grid при пустом OCR. Добавлены bounded independent native alternatives и UI OCR_NATIVE_CONFLICT без подмены исходного OCR. Два замечания CodeQL устранены: bounded ASCII formula part проверяется до source IO, PDF test server выбирает фиксированные paths из Map. Оба review threads resolved; независимый review без Critical/Important/Minor. Свежий Security Guard SUCCESS; отдельный новый CodeQL scan этим протоколом не заявляется.

**На оригиналах:** authenticated HTTP41/41OMML с exactXML/PNG/source/candidate hashes; evidence0 и originals unchanged. Native DOCX14684logical units, не physical layout. V4 534pages render/inventory и716native candidates, включая drawingframes; не716qualifiedtables. Дополнительные21+22+534pages технически inventoried, не semanticqualification. Реальный p55:21×4grid/74unique cells; визуальный эталон74cells/native0различий, OCR41различие; все41конфликта доступны, originalOCR сохранён. Linux actual formula renderer, HTTP/DOM,7Chromium routes/PDFviewer PASS; Windows cold/repeat/restart/backup/PDFviewer/realOllama/browser PASS. Windows формульный converter не установлен в этом CI, formula_rendered=false; пользовательскийПК не обновлён.

**QA сохранён:** ENGINEER_OS_STAGE13_QA_20261012.zip, тот же libfile_fa998953e1ac81919d5c9d8bd4acd15d, **version1**,217payloads/1060612bytes, SHA256 **eba2d747b012a068aa9b57c3e30edf8253e41b1f9d6c83e7c8a6f1406824dfa9**; CRC PASS. Оригинальные пакеты и модели исключены. Архив содержит final CI/review/merge proof, source-bound receipts, PNG, gold и reproducible scripts.

**В плане A1–A4 выполнены. Текущий пункт №13, следующий шаг B2+B3:** originalWord visual/layout/fonts/fields/formulaequivalence; полная qualifiedV4 graphic/raster/mixed/merged semantics, labels/units/value relationships; затем representativequalifiedcorpus B1/B5. B1–B5 остаются частично выполненными/OPEN, не закрываются этим merge. №13/14/19 OPEN,8DONE/8PARTIAL/3OPEN; engineeringACCEPTED=false, userPC NOT_VERIFIED. ЛИРА/RES не запускались; PR102 draft/unmerged. Для закрытия №13 нужны перечисленные содержательные доказательства, не новый счёт тестов.

## §141. 12.10.2026 — второй проход B2/B3: исправлены Word field ranges и лишние PDF rotation writes

**PR141 MERGED:** final head **9bf4232466dde19dd25943e0e507e9c0db1e63c7**, кандидат **52996bb62c8a96fa297c6924749d510415b0f6e2**, tested/merged tree **a29c8dc8d439f03de49a285c14b01ff8fb31a0de** совпал. Core **38214608519** SUCCESS:1044tests/103.263s/7skips; Windows **38214608540** SUCCESS:145tests/36.935s/12skips; Security **38214608466** SUCCESS. Local1044/92.333s/8skips. Все9новых regression выполнены также в Windows CI. Независимый whole-branch review без Critical/Important/Minor; workflow follow-up/tree/SHA проверены. PR141 без unresolved threads. Первые два локальных OLE failures вызваны отсутствием существующей pinnedolefile0.47; зависимость восстановлена, focused и fullGREEN. Тесты не отключались.

**Два конкретных исправления:** complex Word field context сохраняется между paragraphs/cells, вложенными fields и marker-only units; cached results остаются FIELD_NOT_EVALUATED, malformed ranges FIELD_STRUCTURE_UNVERIFIED. Native/region/table/OCR PDF чтение не делает set_rotation(0) для уже unrotated страницы; nonzero rotation/CropBox контракт сохранён. Обе ошибки воспроизведены RED→GREEN,6+3regressions.

**На исходниках:** DOCX SHA b253439bdd673a775eaf209ca7d398d766efae5f4a18ac33fa6679f7faae28a5: все14684прежних logicalunits/text сохранены, восстановлена1field-marker unit (14685total),21/21passiveOLEbitmaps и41OMMLunits доступны,71instruction fragments не вычислялись. Это не original Word physical layout. В fontTable27семейств безembeddedfonts; в document.xml явноArial/Calibri/CambriaMath/TimesNewRoman/TimesNewRomanПолужирный, локальные fontconfig families их заменяют. FontTable не означает27реальноиспользуемыхfonts. Source-bound эталон originalWord fullrender отсутствует.

**Растровая графика:** визуально сверены6exactsourcecrops изГрафикиp18 иГеодезииp13: +46,740/−0,450/−4,200, title с+42.650,Прогиб27мм/20мм. PSM6/11 дают3/12строгих whitespace-only совпадения; остальные9не объявлены correct.12authenticatedHTTP/isolatedworker/reopenedhistory проверок PASS,source/PNG hashes совпали,evidence0,originals unchanged. Для этих же12requests ошибкиobject-out-of-range **5976→0**, OCRtext unchanged. Числоошибок/регионов не переносится на весь534pageV4.

**QA:** тот же ENGINEER_OS_STAGE13_QA_20261012.zip / libfile_fa998953e1ac81919d5c9d8bd4acd15d; новый архив **275payloads/1337223bytes**, SHA256 **08d00c8ceaef8bd4812d23013411d5dbd45a94d8d7509e9b0b0a16035d8bfb82**,CRC PASS; сохранены предыдущие receipts и новыеpass2data/CI/review/source-crops. Originalpackages/models/repositorycode/browser screenshots excluded.

**№13 остаётся OPEN, B1/B5 baseline расширен, B2/B3 частично выполнены. Текущие конкретные условия:** source-bound полный Word reference render с исходнымиfonts и проверкой layout/fields/formulas; устранение/сверка literalOCRerrors и проверка signs/units/value-to-geometry relationships на всём graphic/raster/mixed corpus. Никакое число тестов не заменяет эти результаты. №14/19 OPEN,8DONE/8PARTIAL/3OPEN; engineeringACCEPTED=false,PC NOT_VERIFIED,ЛИРА/RES отложены.

## §142. 12.10.2026 — третий проход B3: явный single-line OCR, PR142 MERGED

**Готовое исправление:** профиль PSM7 «Одна строка · отметка или подпись» проходит через UI/API/изолированный worker/history/CLI. Default6 и sparse11 сохранены. CLI записывает фактический render_scale. Никаких автоматических замен текста, изменения источника или инженерного принятия.

**PR142 MERGED:** final head8d469f3fc29225c7c0bbe4248674105528294a64; кандидат cdd0cddadc44a9362f4d718d54dd9492f9581c31; tested/merged tree35a3dfb29944566bdf17b8d09b7364cbc3160360 совпал. Core38218813753 SUCCESS:1048tests/118.590s/7skips; Windows38218813740 SUCCESS:149tests/34.726s/14skips; Security38218813892 SUCCESS. Local1048tests/94.666s/8skips PASS,7Chromium routes PASS. Независимый whole-branch review:0Critical/Important/Minor. Исправлен устаревший отрицательный тест PSM7; invalid99 и positive7/11 worker/history проверены. Windows два genuineOCR regressions SKIP из-за отсутствия rus+eng models; controlled profile/CLI проверки выполнены. Пропуски не объявлены PASS.

**На тех же оригинальных пикселях:** six source-bound crops, PSM6=1/6, PSM11=2/6, PSM7=3/6 strict whitespace-only совпадений. +46,740 больше не дублируется; −4,200 и title распознаны. −0,450 с рамкой и Прогиб27мм/20мм остаются ошибочными. Все6 authenticatedHTTP/isolatedworker/reopenedhistory запросов выполнены, PNG/source hashes совпали, evidence0. Это не квалификация всех страниц.

**Диагностика альтернатив:** tessdata_best не дал общего улучшения; p55conflicts41→40 лишь диагностический результат. Отдельный RapidOCR3.4.1 Cyrillic PP-OCRv3 / ONNXRuntime1.23.2, localmodelSHA1efb65bdc460af1c0e8733d005b20952b17ca5aac10ddb56c968333791c5eaa3, на exact6PNGs:0/6 и приheight48, и приheight32. Network во время inference запрещён; неявный fontdownload заблокирован, затем указан localfont. Ни один альтернативный engine/model не стал production default; автокоррекция «д→б» не добавлена. QA содержит диагностические receipts, но не модели или зависимости.

**Что делаем дальше / критерии закрытия:** B3 — устойчиво распознавать оставшиеся literal labels/signs/units и проверить value-to-geometry associations на полном graphic/raster/mixed corpus; B2 — source-bound originalWord reference с исходнымиfonts, layout/fields/formulas equivalence; B1/B5 — representative qualified corpus. Эти критерии остаются OPEN/частично выполненными. A1–A4 выполнены в ранее указанном объёме. №13/14/19 OPEN;8DONE/8PARTIAL/3OPEN, engineeringACCEPTED=false, userPC NOT_VERIFIED, ЛИРА/RES отложены. Новый счёт тестов не закрывает содержательные критерии.

**QA:** ENGINEER_OS_STAGE13_QA_20261012.zip сохраняет предыдущие receipts и добавляет pass3 RED/GREEN/full/browser/HTTP/CI/review/probe данные; тот же файл libfile_fa998953e1ac81919d5c9d8bd4acd15d. Originals/models/venv/repositorycode/browser screenshots исключены; полный payload SHA manifest и CRC проверяются перед сохранением.

## §143. 12.10.2026 — оставшиеся три selected-line OCR ошибки устранены в уточнённых selections, PR143 MERGED

**Причина и решение:** прежние широкие selections включали frames/arrows/часть соседней подписи; наклонный Cyrillic glyph б путался с д. Добавлены explicit `ocr_preprocess=padded|italic`, только selectedOCR+PSM7; defaultnone/6/7/11 сохранены. padded=20whitepixels; italic=fixed0.1horizontal shear, neutraldarkink mask,20whitepixels. Nolexicalautocorrection/whitelist/autoselection/sourcechanges/acceptance; никаких новых runtime dependencies/downloads. UI показывает sourcePNG и derivedPNG. Цветные детали derivedcopy могут быть потеряны, sourceequivalence NOT_ASSERTED.

**Подтверждённые строки в оригинальных PDF:** authenticatedHTTP/isolatedworker/reopenedhistory6/6 strict whitespace-only совпадений. +46,740/−4,200/title сохранены; −0,450 и Прогиб27мм/20мм recovered с тремя более узкими selections. Графикаp18 negative bbox[335.5,1376,368,1385],padded; Геодезияp13 deflection27 bbox[327,295,374,304],italic; deflection20 bbox[316,357,360,366],italic. SourceSHA fc2e720d13039b5fa9628b05125e8ce3bc6ba2c8756bfcb882243a67ec69d44c /6092ab2298bf328a545379a850b0a740cc40f3c5592703fbf876c32f459913ce. Ранее широкие snapshots сохранены; новый6/6результат не относится к прежним bounding boxes или всему corpus. Evidence0, originals unchanged.

**Контракт provenance:** originalPNGhash/dimensions сохранены; derivedPNG/hash/sourcebinding/fixedtransform записаны и deterministically regenerated приsave/reload; bbox inverse shear/padding + originalpixelorigin возвращаетunrotated crop-relativecoords. Exactfractionalorigin regression дляbothprofiles; malformed/unsupportedprofiles rejected before render. Pixel/output/deadline/historylimits retained; только bounded candidate, не engineeringevidence.

**Проверки:** Local1053tests/99.461s/9skips PASS;7Chromiumroutes и DOM/architecture PASS. GenuineChromium OCR Прогиб27мм, обеPNG, selector disabled/reset, historyreload PASS. Независимый whole-branchreview0Critical/Important/Minor; initialMinor exactinversecoverage закрыт5thregression. **PR143 MERGED:** finalheadcefc0094c52015fab1c512664a3f9fe320e67309, кандидат9b4cd8f3ec8bf5c4718c3906bf1750b83d58e569; tested/merged treef8d9c41513fdc8e57454ea6bc086708db9dd6cdf совпал. Core38222370207 SUCCESS:1053tests/150.216s/7skips, actualLinuxformulaRenderer/HTTP/DOM/7Chromium/PDFviewer,genuineprintedOCR PASS. Windows38222370336 SUCCESS:154tests/35.742s/16skips; cold/repeat/restart/backup/PDFviewer/realOllama/browser PASS.2newgenuineOCRtests и браузерныйgenuineOCR skipped/unavailable без локальныхrus+eng,3newcontrolledtests PASS. Security38222370258 SUCCESS. Skips не объявлены выполненными проверками. Дополнительный exactinverse test mutation wrongshearsign RED→restoredGREEN; productionbytesunchanged.

**Что закрыто:** три названные literal ошибки в уточнённых source selections. **Что остаётся №13:** originalWord source-bound reference/fonts/fullphysical layout/fields/formulas equivalence; полная semanticqualification graphic/raster/mixed/merged corpus, signs/units/value-to-geometry associations и unresolvedtable OCR conflicts; representativequalifiedcorpus B1/B5. Текущий шаг B3 corpus qualification, параллельное условие B2 Wordreference. A1–A4 в прежнем объёме выполнены; B1–B5 partial/OPEN. №13/14/19 OPEN,8DONE/8PARTIAL/3OPEN. engineeringACCEPTED=false,userPC NOT_VERIFIED,ЛИРА/RES отложены. Шесть строк не являются100%готовностью documentintelligence.

**QA:** прежний ENGINEER_OS_STAGE13_QA_20261012.zip /libfile_fa998953e1ac81919d5c9d8bd4acd15d, pass4 дополняет сохранённую историю; rawsourcecrops/derivedPNGs/fixtures/probe/HTTP/REDGREEN/full/browser/CI/review/merge proof, payloadSHAmanifest/CRC. Originalpackages/models/venv/repositorycode/browser screenshots исключены.

## §144. 12.10.2026 — латинские обозначения армирования и квалификация четырёх таблиц V4

**PR144 MERGED:** final head **2db5e5d8c29dede95abb9dbeca9725236507b229**, кандидат **b2c29604d3a8a2a8079a670a7affca4f55b2b9c6**, tested/merged tree **c1f44ad1839ecf763faedb98deaf87fd219e5e75** совпал. Core **38227712649** SUCCESS:1057tests/128.463s/7skips; Windows **38227712661** SUCCESS:158tests/33.737s/18skips; Security **38227712680** SUCCESS. Local1057/98.573s/9skips PASS,7Chromiumroutes/DOM/architecture PASS. Core genuine Latin/printed OCR, actual formula renderer и PDFviewer выполнены. Windows2newgenuineOCRtests skipped без локальныхrus+eng; проверки invalidlanguage/wholepagecontract выполнены, browsergenuineOCR=false. Skips не объявлены PASS.

**Исправление:** явный выбор `eng` или default `rus+eng` для выбранного PDF фрагмента в UI/API/worker/history/CLI. Русский профиль принимал латинскую d в `4 d20 + 4 d16` за4. Выбор языка не автоматический, никаких подстановок символов или изменения источника. Сохраняются оба прежних локальныхmodel prerequisites; новые зависимости/downloads отсутствуют. Defaultwholepage/history остались прежними. Независимыйreview выявилImportant:defaultrecord мог содержатьengine.language=eng. Исправлена симметричная проверка request/dossier/engine; отсутствующийlegacylanguage означаетrus+eng. Hash-valid SQL mutations default→eng и eng→rus/missing отклоняются приreopen, RED→GREEN. Finalreview0Critical/Important/Minor,60tests/0skips и genuineChromium PASS. После сброса среды2initialOLEtests FAILED из-за отсутствующего существующегоolefile0.47; восстановлен pinned dependency, полныйGREEN, тесты не отключались.

**V4 p55:**40numericcells exact приexpliciteng+PSM7+padded и inset2/3PDFpoint внутри parentcell; на полных границах36/40, а focusedrus+eng23/74, поэтому общийdefault не изменён. Отдельно восстановлен пропущенный1в подписи «1 этаж, верхняя часть». Все41 authenticatedHTTP/isolatedworker/reopenedhistory запросов PASS сsource/PNG hashes. Квалифицированныйledger объединяет33ранее exactOCRcells и41source reread: **74уникальные literalcells,84gridpositions,21×4**,0literal mismatches. Row/column/mergedspans иparentcell→selection association проверены. Старыйwhole-tableOCR с41conflicts сохранён; app не выполняет автоматическую замену или adjudication.

**Независимый holdout p56:**3таблицы в осях16/Д,14/Е,16/Е. Визуальныйgold составлен доOCR, сверены **96nativecells**;48numericsourceHTTP/worker/reopenedhistory запросов дали **48/48exact**, тот жеeng+padded+PSM7 и2/3pointinset без измененияпараметров. Независимыйvisualreview подтвердил headers/marks/mergedrows,все48значений,включая red12/8/16d20. SourcePDF SHA **b5d95b660b35bfb6b2441623635cba91c235efd754bc283dfe1405f075834916** сохранён.

**Итог квалифицированной выборки:**4таблицы/pages55–56, **170uniquecells/192gridpositions**, **89sourceHTTPrequests exact89/89**,44same-row«проект—факт» literalpairs. В11pairs строки различаются; это проверка содержимого и связи, не инженерный вывод о дефекте. Diameterunits NOT_ASSERTED — единицы не выдумывались. Evidence0, originalsunchanged, quality/acceptance вruntime=false. Полный534pageV4/всяrastergraphics этими числами не квалифицированы.

**Что дальше и почему №13 открыт:** B3 — остальные graphic/raster/mixed/merged таблицы и схемы, знаки/единицы иvalue-to-geometry связи на representative corpus; B2 — source-bound эталонный экспорт исходногоDOCX изMicrosoftWord с исходнымиfonts дляphysical layout/fields/formula equivalence. Доступный substitution-font render не заменяет этот эталон. B1/B5 qualifiedbaseline расширен четырьмя таблицами, веськорпус не закрыт. A1–A4 в прежнем объёме выполнены;B1–B5partial/OPEN. №13/14/19OPEN,8DONE/8PARTIAL/3OPEN, engineeringACCEPTED=false,userPC NOT_VERIFIED. ЛИРА/RES отложены.

**QA:** ENGINEER_OS_STAGE13_QA_20261012.zip, тот же libfile_fa998953e1ac81919d5c9d8bd4acd15d, сохраняетpass1–4 и добавляетpass5: diagnostic/REDGREEN/full/CI/browser/review,sourcecrops/fixtures/89HTTPreceipts,170cellqualifiedledgers/44associationpairs иmerge/treeproof. Originalpackages/models/venv/repositorycode/browser screenshots исключены; CRC иполныйpayloadSHAmanifest проверяются.


## 145. Проверка графики и кандидата Word-эталона — 12.10.2026
Код не менялся: PR144 MERGED, кандидат b2c29604d3a8a2a8079a670a7affca4f55b2b9c6, tree c1f44ad1839ecf763faedb98deaf87fd219e5e75. Core1057/Windows158/Security — результаты CI PR144 из §144, не новый полный прогон pass6.

### Проверено
- Все 21 лист графики соответствуют V4 p492–512; все 22 листа геодезии — V4 p513–534. На 43/43 совпали точные разобранные геометрические сигнатуры и пиксели контрольного рендера. Проверка размеров/CropBox/rotation всех 534 страниц исключила другие совместимые страницы. Сигнатуры и рендер выполнены одним PyMuPDF1.26.6: это взаимодополняющие проверки, не независимые движки и не доказательство всей семантики.
- Исправлено прежнее предположение о слоях: эти 43 листа содержат векторные пути и не содержат изображений; 40 не имеют native words. Отсутствие извлекаемого текста не означает растровый оригинал. Происхождение шрифта SHX не доказано.
- Шесть выбранных надписей заново прочитаны непосредственно из V4 p509/p525 через authenticated HTTP → worker → history → reopened Store: 6/6 точных совпадений после нормализации только пробелов. PNG/source SHA/page/bbox привязаны к текущему чтению; более ранние широкие визуальные контексты сохранены отдельно. Original unchanged; evidence_count=0; инженерная приёмка не выполнялась.
- Предыдущая квалификация четырёх таблиц V4p55–56 сохраняется:170 уникальных ячеек/192 позиции/89 точных HTTP чтений (§144). Соответствие 43 листов не делает автоматически квалифицированными все их подписи и инженерные связи.

### Word: доступный кандидат, ещё не квалифицированный эталон
DOCX имеет cached Pages491; V4 содержит491 основную страницу+43 сопоставленных листа графики. PDF создан примерно через2минуты после изменения DOCX. Это признаки возможного связанного экспорта, не доказательство одинаковой версии или экспорта Word.
Из3086 абзацев длиной≥12 нормализованных символов2247 найдены первоначальным substring поиском, ещё595 — эвристиками порядка текста/переносов/точек оглавления.244 остались несопоставленными; у176 найдены32-символьные фрагменты, у68 не найдены. Повторы, поля, формулы и порядок чтения ограничивают эти числа: это диагностика, не literal coverage и не244 доказанные ошибки. Проверка вложенных DOCX абзацев не выявила нового подтверждённого parser bug.
Ранее «Wordreference отсутствует» уточняется: V4 доступен как кандидат, но его correspondence/layout/fields/formulas/font equivalence ещё не доказаны. Новый экспорт нельзя требовать до проверки имеющегося кандидата.

### Дальше работаем и критерий закрытия
1. B2: сопоставить244 оставшихся абзаца по странице/контексту; отделить порядок чтения и поля от реальных пропусков/различий версии. Для подтверждённых дефектов — воспроизводимый тест, исправление, проверка.
2. B2: проверить source-bound physical layout, поля,41OMML и доступность/замены исходных шрифтов; metadata и cached page count не заменяют визуальную квалификацию.
3. B3: расширить заранее размеченный corpus на остальные векторные/растровые/смешанные данные и связи значений с осями/этажами/единицами; совпадение страниц не заменяет эту работу.
№13 OPEN;8DONE/8PARTIAL/3OPEN. №14/19 открыты, физический ПК не проверен, расчёты отложены. QA pass6, независимый review: оставшихся замечаний по43-page map и6-label provenance нет.


## 146. Разбор Word/PDF расхождений и оглавление — 12.10.2026
Продолжение §145 без изменения production-кода PR144. Первоначальные244 несопоставленных абзаца не являются244 ошибками документа.
-229 найдены диагностически после сохранения значимых дефисов, удаления строчных переносов и исключения рамки. Это normalized substring alignment, не буквальная/визуальная квалификация.
-15 остаточных случаев разобраны:3 noBreakHyphen пропускал исходный probe, существующий office.word_text их сохраняет;6 абзацев содержат по3OMML, которых probe w:t не включал;2 абзаца проходят черезV4p84–85 иp244–245, с таблицей/рамкой между частями;4 относятся к оглавлению. Две вручную ограниченные последовательности текста между страницами совпали после документированной нормализации. Отдельно сохранены исходные строки/страницы.
-V4p3 отображает2.3.1/2.3.2/2.3.3, которые отсутствуют в native get_text. Три заранее визуально прочитанных bbox прошли genuine eng/padded/PSM7 через authenticated HTTP/worker/GET/reopened Store:3/3 exact, source/PNG SHA/bbox связаны, evidence0, originals unchanged. Извлечённый native text сам по себе не является полным эталоном.
-2247 первоначальных+595 предыдущих+229 новых совпадений=3071/3086 диагностических substring совпадений;15 имеют объяснение. НЕ заявлены3086/3086 literal matches, отсутствие всех расхождений версий, квалификация всех формул или physical layout.
Отдельный подтверждённый runtime parser bug на этих residuals не найден; диагностические скрипты исправлены, производственные файлы не менялись. Результаты Core1057/Windows158/Security из§144 остаются прежними CI, не новым прогоном.
**Работаем дальше B2:** source-bound визуальная сверка41OMML/полей/OLE/WDP/EMF/шрифтов и physical layout. V4 имеет сильное подтверждение текстового соответствия и остаётся кандидатом связанного экспорта, но происхождение из конкретного Word renderer не доказано. B3: расширение квалифицированных областей и связей. №13 OPEN; критерия B2 нельзя заменить объяснением substring расхождений.


## 147. Два DOCX и проверка41 формулы — 13.10.2026
Production-код не менялся: PR144 MERGED; кандидат b2c29604d3a8a2a8079a670a7affca4f55b2b9c6/tree c1f44ad1839ecf763faedb98deaf87fd219e5e75.

### Исходники и границы версий
Восстановлены и проверены оригиналы: прежний DOCX147210288байт/SHA b253439bdd673a775eaf209ca7d398d766efae5f4a18ac33fa6679f7faae28a5; Drive V4 DOCX147560922байт/SHA c0ca593f4dec5c101d01282523032e05b147e9169fb043a144af5fbd479a5685; PDF74522583байт/SHA b5d95b660b35bfb6b2441623635cba91c235efd754bc283dfe1405f075834916. Неполные рабочие DOCX-копии после перерыва заменены повторными загрузками; перед проверкой SHA и ZIP CRC PASS.
Обе DOCX версии имеют одинаковые последовательности w:t абзацев и XML всех41OMML. Все642 прежних media payloads сохранены по multiset SHA, добавлены12;21embedding payloads byte-identical. Drawings655→668, media642→654. Это разные версии файлов, не byte-identical документы; графическую композицию нельзя объявить равной по этим числам.
Styles/numbering/theme byte-identical; settings изменились в rsids; fontTable byte-different, но названия шрифтов и explicit body families совпадают. Embedded font programs отсутствуют в обоих; это не подтверждает наличие исходных шрифтов или эквивалентность замен.

### Проверки текущим приложением
Полный production read_docx обоих оригиналов:14685→14689units,12826table_cells в каждом,682→696image references,21embedded_object references,41equation units. Source unchanged; physical pages/layout/auxiliary placement/embedded interpretation остаются unverified.
Все12826 логических table locator/source_grid записей между версиями совпали. Это проверка сетки и связи, не квалификация содержания каждой ячейки или физических страниц.
Focused Word regression:61tests/2.401s/0fail PASS. Восстановлена существующая pinned olefile0.47; новых production зависимостей или кода нет. Core1057/Windows158/Security — прежние CI PR144, не новый полный прогон.

### Формулы: конкретное продвижение B2
41/41 source formula XML и preview PNG hashes совпали с сохранённым provenance; XML41формулы одинаков в обоих DOCX. Все41 derivative previews и12crops исходных PDF страниц просмотрены, видимые обозначения/числа/дроби/индексы сопоставлены с контекстом V4. Формулы27–29 находятся наp337; p338 лишь соседний контекст.
41-formula-correspondence.json закрепляет source/formula/PNG SHA,ordinal иcandidate page. В этой ограниченной визуальной проверке различий содержимого обозначений не наблюдалось. Это не pixel/physical/font/layout equivalence и не расчётная верификация; math/engineering acceptance не выдано. V4 остаётся candidate reference без доказанного происхождения конкретного Word-экспорта.

### Осталось и сохранность
№13 OPEN. Следующий B2: поля, размещение графических/встроенных слоёв и полная physical/font/layout equivalence исходногоWord. B3: оставшиеся representative PDF semantic области/единицы/связи. Текстовое correspondence и41bounded formula review не заменяют эти критерии. Расчёты ЛИРА/SCAD отложены и не являются причиной OPEN13.
QA архив сохраняет восстановленныеpass1–5 и добавляет воспроизводимыйpass8. Rawpass6/7 не успели сохраниться до очистки workspace; их результаты остаются историческими§145–146 наGitHub, наличие их исходных receipts в архиве не заявляется. 8DONE/8PARTIAL/3OPEN; ПК и engineeringACCEPTED не подтверждены.


**Уточнение независимого review pass8:** все41визуальных обозначения/числа и source/preview/crop hashes подтверждены. Сравнение12826ячеек относится только к part/table/row/column/source_grid. **148полных locator dictionaries различаются** в image bindings/declared drawing labels; complete locator equivalence не заявляется. Квалификация physical/fonts/layout и расчётов остаётся false.


## 148. Передача Codex и cached Word fields — 13.10.2026
Полный промт сохранён: [codex-handoff-20261013.md](https://github.com/maxim505885-jpg/engineer-os/blob/docs/project-map-handoff-20261005/docs/development/codex-handoff-20261013.md). Production-код/кандидат PR144 не изменены. Сначала читать этотhandoff,AGENTS иактуальныйmaster-plan, проверять фактическийHEAD.
Pass9 диагностически проверил71поле каждогоDOCX:57PAGEREF/1TOC/11SEQ/2PAGE; balanced, orphan/unclosed не выявлены.71cached results equal.57bookmark names отличаются, но все57range targets существуют, target text иcached page одинаковы;57/57target texts найдены native вV4 наcached pages. Поля Word не перевычислялись, physical pagination/render/font equivalence не заявляется. Скрипты и19XML/rels частей каждого оригинала/source manifests сохранены отдельно; перед snapshot проверены полныйsourceSHA иZIPCRC.
12новыхmedia payloads имеют14runtime image bindings, в основномtable1rows2–9/paragraph63,507,530,703,705; дополнительныйHD_PHOTO_LAYER. Визуальнаякомпозиция остаётся открытой. проверено12добавленныхpayloadbindings, не весьgraphiccorpus.
Архив QA обновляется тем жеID сpass9, сохраняяpass1–5/8; rawpass6/7 отсутствуют, историческиерезультаты§145–146 сохранены.
№13 OPEN. Следующийработник—Codex; B2 поля/graphiclayers/fonts/physicalWord иB3 semantic corpus. ЛИРА/SCAD отложены;ПК/engineeringACCEPTED/стабильныйrelease не подтверждены.


## 149. Word Windows reference и ASCII CLI — 13.10.2026

Кандидат `integration/release-candidate-v1` не менялся: base `b2c29604d3a8a2a8079a670a7affca4f55b2b9c6`, tree `c1f44ad1839ecf763faedb98deaf87fd219e5e75`, PR144 MERGED. Открыт draft [PR145](https://github.com/maxim505885-jpg/engineer-os/pull/145), head `c97c8c9d39246261c5891b192af8c083a75893a9), base PR остаётся b2c2960. Он содержит commit `047838418cf5a6fadfbf0759ae189cdf8cd2909f` с исправлением CLI и отдельный commit только с уточнённой QA статистикой. Ни один PR не объединён.

### Word и PDF, source-bound проход

V4 DOCX `147560922` байта, SHA `c0ca593f4dec5c101d01282523032e05b147e9169fb043a144af5fbd479a5685`; 694 ZIP entries/CRC PASS. V4 PDF `74522583` байта, SHA `b5d95b660b35bfb6b2441623635cba91c235efd754bc283dfe1405f075834916`. Word 2021 build `16.0.14228.20204`, Windows10 build19045. Read-only открыть удалось на byte-identical DOCX copy; source иcopy hashes после закрытия совпали с оригиналом.

Word вывел491 страницу; PDF содержит534. Безопасно обновлены57 PAGEREF,11 SEQ,1 TOC и общий header PAGE через два section placements. HYPERLINK и EMBED не активировались. До/после обновления поля native text и raster hashes Word PDF совпали на всех491 страницах. Первая491 страница PDF:483 exact text,489 equal после whitespace removal. На 491 страницах размеры отличаются на0.12pt по каждой оси; pixel hashes0/491 equal, поэтому physical/visual equivalence не подтверждена.

Страницы492–534 PDF — 43 графических листа за индексом чертежей; Word export заканчивается на491. Полный native visual audit PyMuPDF1.26.6:125 trimmed text chars,40 листов без native text, vector paths на43/43 листах (2513–67955 на лист). Приложение вернуло `VECTOR_CONTENT_UNVERIFIED`/BLOCK для43/43; Tesseract и локальные русские/английские модели недоступны. В DOCX 21 embedded OLE `PBrush` (44,983,296 байт),696 image references,463 DrawingML paragraphs; соответствие этих объектов 43 листам не установлено. 11 `unsupported_body` units отдельно подтверждены пустыми bookmarkEnd markers без текста/графики. 41 equation unit и вспомогательное размещение не квалифицированы этим pass.

### Регрессии, воспроизведение и состояние CI

Новая subprocess regression сначала воспроизвела `UnicodeEncodeError` при Cyrillic JSON и ASCII stdout. CLI теперь выводит ASCII-escaped JSON; сохранённый отчёт остаётся UTF-8, входные байты и acceptance gates не меняются. Test проверяет ASCII pipe и восстановление исходной Cyrillic при JSON decode. ZIP test fixtures этапа7 получили фиксированные timestamps после нестабильного полного прогона; три теста этапа7 прошли.

Полный локальный Windows suite:1058 tests/297.549s,0 assertion failures,13 errors,49 skips. Ошибки: SQLite locks в шести backup/recovery тестах, один открытный NamedTemporaryFile fixture, шесть тестов не смогли создать symlinks без Windows privilege. Skips включают отсутствующие OCR модели, optional table OCR, Linux-only seccomp/process checks и link capabilities; ничего не отключалось. Подробности и private log SHA находятся в `docs/qa/2026-10-13-stage13-word-reference-windows.md`.

Для code commit `0478384` Windows workflow run170 SUCCESS, включая запуск нового CLI regression, а Repository Security Guard run693 SUCCESS. Core Tests run968 оставался in progress при записи; текущий draft head `c97c8c9` проверяется отдельно. Полные тесты PR144 не считать свежим evidence для PR145.

### Следующий шаг и открытые критерии

Продолжить source-bound сопоставление43 PDF листов с DOCX package/placement, затем квалифицировать графику/OLE/WDP/EMF, fonts и physical pagination и расширить B3 corpus. Нужен полный local OCR с координатами, visual cross-check и матрица coverage по листам/меткам. Не выводить значения из индекса чертежей и не считать VECTOR_CONTENT_UNVERIFIED как прочитанное содержимое.

CLI regression issue закрыт только в proposed PR; source-level Word/PDF completeness остаётся OPEN. Не объявлять100%, ACCEPTED или закрытие №13. ЛИРА/SCAD остаются отложены; paid/API/production dependencies не добавлялись.

## 150. Полный OCR-кандидат на графических листах и карта OLE preview — 13.10.2026

По исходному V4 PDF SHA-256 b5d95b660b35bfb6b2441623635cba91c235efd754bc283dfe1405f075834916 выполнен отдельный локальный OCR всех страниц 492–534 (43/43): Tesseract 5.5.3.20260724, rus+eng, OEM 1, PSM 11, 300 dpi. Сохранено 19,644 OCR-кандидата с TSV координатами; среднее confidence, взвешенное по словам, 71.35; 29.12% ниже 60; среднее по листу 57.61–85.31. Это не доказывает полноту/точность: значения, символы, поворот, reading order и пропуски не выверены целиком по исходным изображениям, а все 43 native vector pages по-прежнему дают VECTOR_CONTENT_UNVERIFIED/BLOCK.

OOXML-карта 21 PBrush OLE relationship найдена: 20 уникальных fallback PNG, привязанных к body paragraph indices; два OLE-пары делят одинаковые previews. OCR этих 20 PNG дал 616 кандидатов при среднем confidence 61.82 по изображениям. Native OLE payload и точная печатная страница DOCX не декодированы; соответствие этих деталей 43 страницам PDF не установлено. Исходные DOCX/PDF остались неизменны. Официальный Windows OCR runtime использован только как локальный диагностический инструмент и не добавлен в приложение или его зависимости.

Обновлён draft PR145: https://github.com/maxim505885-jpg/engineer-os/pull/145 (head после записи QA отчёта и плана: d1a41484a3b27c55301fbb832423a23483054553; новые exact-head checks ожидаются). Полный источник, параметры, хеши моделей и границы проверки записаны в docs/qa/2026-10-13-stage13-word-reference-windows.md; приватные TSV, manifest и OOXML relationship audit остаются в локальном stage13-qa.

Далее: проверить OCR-кандидаты каждого листа, в том числе размеры/обозначения/ориентацию, сопоставить все native OLE и previews с печатными страницами, затем завершить B2 visual/font/layout и B3 corpus coverage. №13 OPEN; не заявлять 100%, ACCEPTED или полноту. LIRA/SCAD по-прежнему отложены.

## 151. Проверка фактического OCR-контура приложения — 13.10.2026

На неизменном V4 PDF SHA-256 b5d95b660b35bfb6b2441623635cba91c235efd754bc283dfe1405f075834916 запущен текущий TesseractOCR приложения на всех43 листах, с теми же rus+eng моделями. Default whole завершил 1/1 проход на каждой странице: 11,993 слова, 2,530 блоков; средняя confidence строки43.38, 58.22% ниже50. Каждая страница получила низкоуверенные строки, поэтому критерий OCR LOW CONFIDENCE блокирует все43 листа. Layout regions завершил 5/5 проходов: 30,607 слов, 7,235 блоков; средняя confidence строки47.79, 52.07% ниже50. Перекрывающиеся регионы остаются явно UNMERGED; они не считаются подтверждёнными и могут дублировать кандидаты. Таймаутов и исчерпания pixel/word budgets не было. Это подтверждает fail-closed поведение и одновременно показывает, что текущая точность OCR не годится для чтения этих чертежей.

Независимый единый полноформатный PSM11 проход при300dpi дал19,644 word candidates; weighted confidence71.35 и29.12% слов ниже60. Значения различаются, поскольку это другой профиль, и ни один профиль ещё не прошёл полную source-bound human review. Контактные листы всех43 страниц просмотрены на обзорном уровне; они содержат разнотипные планы, разрезы, цветные карты результатов и узлы армирования. Это не проверка каждого числа, обозначения или легенды. Все21 OLE relationships сопоставлены с20 уникальными previews/paragraph indices; сами native payloads и точная печатная пагинация остаются открытыми.

Draft PR145 обновлён QA отчётом и планом; текущий head a7bd87ac8fa20d475b30817e02479e2d76d4756a, exact-head Windows/Core workflows ожидаются. См. docs/qa/2026-10-13-stage13-word-reference-windows.md. OCR-файлы/досье, fonts/source raw data остаются частными локальными доказательствами.

Следующий шаг: улучшить/обосновать OCR профили для чертежей и проверить каждую страницу по полной векторной графике; затем закончить OLE payload/page mapping, font/layout physical checks и B3 full corpus. Item13 OPEN. Не заявлять полноту, 100% или ACCEPTED. ЛИРА/SCAD остаются отложенными; платные runtime/API зависимости не добавлены.

## 152. Исходное происхождение графических листов V4 подтверждено — 13.10.2026

Из Drive read-only получены исходные пакеты: Графика 03.09.2026.pdf — 10,793,106 bytes, SHA-256 fc2e720d13039b5fa9628b05125e8ce3bc6ba2c8756bfcb882243a67ec69d44c; Геодезические измерения 03.09 пакетная печать.pdf — 7,563,047 bytes, SHA-256 6092ab2298bf328a545379a850b0a740cc40f3c5592703fbf876c32f459913ce. Pages1–21 graphics map one-to-one to V4 pages492–512; geodesy pages1–22 map to513–534. All43 corresponding page rectangles, native-text hashes and full rendered pixel hashes matched at72dpi in PyMuPDF. This proves page provenance and render identity only under that same renderer and resolution; no labels or engineering values were decoded by this comparison. Forty pages have no native text and remain VECTOR_CONTENT_UNVERIFIED/BLOCK.

§151 quality finding is unchanged: application whole and regions profiles complete their raster passes on all43 pages but block every page for OCR_LOW_CONFIDENCE; the independent300dpi PSM11 output is only an unverified candidate set. The package comparison does not qualify OCR completeness, raster table/label semantics, source Word object placement, physical pagination, fonts or B3 corpus.

Draft PR145 QA/report now has source packet hashes and page-by-page comparison. Current PR head bded12a438bdffaf4d551eabb05cf8b20505738f; Repository Security Guard run710 SUCCESS; Windows run177/Core run975 pending. Exact-base candidate remains b2c29604d3a8a2a8079a670a7affca4f55b2b9c6. №13 OPEN; no 100% or ACCEPTED. LIRA/SCAD deferred.

## §153 — exact OLE ShapeID binding and corrected placement counts (13.10.2026)

PR145 draft now includes the corrected QA report and plan at head 42ac6b0bd29a158912c14da9950e7e7d82ae9786; exact-head CI for this newest documentation commit is pending. The preceding documentation-only head 3e1e94ac8c62f1fc385164d98f159a3d439a957f has Core run977, Windows local runtime run179, Security Guard run716, and PR check run486 all SUCCESS. Code head 6b132093c8d4adb164ce7071275d3b6ed77b0413 passed Core run976 (1,059 tests, 7 skips, including HTTP/DOM and Chromium), Windows run178, and Security run715. The candidate branch remains at b2c29604d3a8a2a8079a670a7affca4f55b2b9c6; PR145 is open and draft.

A corrected OOXML resolver binds each OLEObject ShapeID to the VML shape with the same ID and its imagedata relationship. This avoids the ambiguous paragraph-level pairing used in an earlier diagnostic. The 21 OLE objects map to 20 distinct preview PNGs; OLEObject12 and OLEObject17 share image67.png. The application's read-only DOCX parse returns 14,689 logical units and classifies all 21 as BOUND_PACKAGE_OBJECT, with available BMP bitmaps and no activation. All 21 native Ole10Native BMP render outputs are pixel-identical to the exact ShapeID-bound OOXML preview.

Exact pixel matching against Word's 491-page PDF establishes XObject page associations for 18 object instances / 17 distinct previews. image166.png (OLEObject15), image180.png (OLEObject16), and image200.png (OLEObject20) have no exact standalone XObject match; their printed page positions remain unproven. Paragraph/page context does not count as proof. The comparison establishes bitmap/fallback equivalence only, not PBrush print-stream engineering semantics or linkage to the 43-sheet PDF appendix.

No source file changed: V4 DOCX SHA-256 remains c0ca593f4dec5c101d01282523032e05b147e9169fb043a144af5fbd479a5685; V4 PDF SHA-256 remains b5d95b660b35bfb6b2441623635cba91c235efd754bc283dfe1405f075834916. Both production OCR layouts still BLOCK all 43 vector pages on confidence; candidate OCR has not been exhaustively checked against every label, dimension, symbol, rotation, and omission. Physical Word pagination, fonts/layout, and full B3 semantic corpus remain unresolved. Item13 remains OPEN; no 100%, ACCEPTED, or closure claim.


## §154 — визуальная привязка оставшихся OLE-превью к страницам Word (13.10.2026)

At PR145 head 7d7347293714c50e87fdb4106b4279e02430adbc, Security Guard run722 has succeeded; Core run979 and Windows local runtime run181 were in progress at the latest check. The preceding code head 6b132093c8d4adb164ce7071275d3b6ed77b0413 passed Core run976 (1,059 tests, 7 skips, including HTTP/DOM and Chromium), Windows run178, and Security run715. The latest merged candidate remains b2c29604d3a8a2a8079a670a7affca4f55b2b9c6; PR145 is open and draft.

Side-by-side inspection of the 596×843 rendered Word pages and the three previews lacking an exact standalone PDF image XObject establishes their page-level visual association: image166.png / OLEObject15 appears as the right-hand reinforcement detail on page74; image180.png / OLEObject16 matches the left grid/deflection diagram on page84; image200.png / OLEObject20 matches the paired braced-column diagrams with arrows and numeric annotations on page99. Combined with the 18 exact-XObject object instances, page-level association is now identified for all21 OLE objects. The three visual matches do not establish exact PDF object decomposition, image bounds or scale. They also do not establish whether any objects correspond to the 43-sheet V4 appendix.

The §153 findings remain: exact OOXML ShapeID→VML→imagedata binding for all21 objects; 20 unique fallback PNGs (OLEObject12 and OLEObject17 share image67.png); application parse classifies 21/21 as bound package objects with available BMP bitmaps and no activation; native Ole10Native BMP renders pixel-match the exact ShapeID-bound fallback preview 21/21. All43 vector appendix pages still BLOCK under both app OCR layouts. Full label/dimension/symbol/rotation/omission review, PBrush print semantics, exact visual bounds/scale, relationship to the appendix, physical pagination/fonts and B3 corpus remain open. Item13 stays OPEN; no 100%, ACCEPTED or closure claim.


## §155 — exact-head CI completion (13.10.2026)

At exact PR145 head 7d7347293714c50e87fdb4106b4279e02430adbc, all four checks completed successfully: ENGINEER OS Core Tests run979, Windows local runtime run181, Repository Security Guard run722, and PR check run492. The draft remains open and the base remains the merged candidate b2c29604d3a8a2a8079a670a7affca4f55b2b9c6. No merge or release acceptance is implied.


## §156 — клавиатурный фокус и exact-head release checks (13.10.2026)

На текущем UI audit найдено правило `textarea:focus{outline:0}`, которое отменяло общий `:focus-visible` и делало клавиатурный фокус в поле сообщения невидимым. Правило удалено; добавлена регрессия в `tests/test_stage11_design_system.py`. Весь design-system module: 5/5 PASS; полный Chromium suite: 7/7 PASS локально на pinned Python; browser test подтверждает mobile/desktop no-overflow и все основные flows. Local screenshot review относится к синтетической модели и не является оценкой инженерной точности.

PR145 draft exact head `884c19a7a5a0e62b21d5f52525fc001e6d7cbdb2`, base candidate `b2c29604d3a8a2a8079a670a7affca4f55b2b9c6`: Core run980 SUCCESS (1,060 tests, 7 skips), Windows run182 SUCCESS after a retried transient timeout in the first memory-panel browser run, Security Guard run731 SUCCESS. Browser and UI verification do not close document completeness or physical release gates. Item11 remains PARTIAL; item13 remains OPEN. All43 graphics pages still BLOCK in the document OCR assessment; exact Word object bounds/scale, appendix linkage, full fonts/layout and the complete source-bound B3 semantic corpus remain unresolved. No ACCEPTED/100% claim is made. LIRA/SCAD remain deferred; local/free product constraints are unchanged.


## §157–158 — Word OLE bounds and source font inventory (13.10.2026)

PR145 draft head `1bb9b37240dc93eccb3682e704228838909c2517`; exact-head Core/Windows/Security checks are Core run992 SUCCESS (1,060 tests, 7 skips; HTTP/DOM, Chromium and vendored PDF.js PASS); Windows run194 SUCCESS; Security Guard run746 SUCCESS. Bounds/scale for the three previously decomposed OLE rasters are measured within 0.151 pt, axis-aligned with no rotation; the source font inventory is recorded (27 names, 6,302 references, no embedded DOCX fonts, 17 exact registry-name matches, 18/27 PDF font XRefs embedded). All43 appendix pages remain OCR BLOCK. Stage13 remains OPEN; no ACCEPTED/100% claim. Merged candidate base is `b2c29604d3a8a2a8079a670a7affca4f55b2b9c6`.

§157: read-only script `scripts/qa/audit_stage13_ole_pdf_bounds.py` and JSON `docs/qa/2026-10-13-stage13-ole-word-xobject-bounds.json`; three PDF XObjects (pages74/84/99) are axis-aligned and match source VML bounds within0.151pt. JPEG/re-rasterized pixel differences are recorded; no pixel equality or semantics are claimed.

§158: Windows font inventory script `scripts/qa/audit_stage13_font_inventory.py` and JSON `docs/qa/2026-10-13-stage13-word-font-inventory.json`; 27 source names/6,302 refs/no embedded DOCX fonts; 17 exact local registry matches; 27 PDF font XRefs,18 with embedded data. This is an inventory and does not infer substitution for an unused style.

B2/B3 remain incomplete, all43 appendix sheets remain BLOCK, and item13 remains OPEN. User-deferred LIRA/SCAD calculations remain out of scope.


## §159 — source-bound OCR false read, page 513 (13.10.2026)

The 300-dpi Tesseract PSM11 candidate at V4 PDF page 513 reads `54.185` (confidence 46.66; bbox px `[5538,491,76,34]`). Visual review of the hash-verified source crop reads `−4.185`; this is a confirmed lost-minus/spurious-leading-digit error in the candidate. It is high-risk elevation data. The application's recorded OCR state remains BLOCK for all43 vector appendix pages, so this sample is not accepted by the product and confirms the need for that gate. Reproduction data: `docs/qa/2026-10-13-stage13-ocr-source-bound-sample.json` on PR145.

The source combined PDF SHA remains `b5d95b660b35bfb6b2441623635cba91c235efd754bc283dfe1405f075834916`. Current PyMuPDF 1.26.6 / MuPDF 1.26.11 renders the standalone geodesy packet page1 and combined V4 page513 to identical raw RGB at 72/150/300 dpi. The 300-dpi raw pixel hash does not match the earlier manifest (`f1dbe...` vs current `62caa...`); that manifest omitted renderer version/options, so this discrepancy is documented, not explained away.

This is one confirmed error sample, not an exhaustive corpus result. All43 pages remain BLOCK; full semantic OCR, OLE/appendix linkage, physical Word layout/font equivalence, and B3 corpus coverage remain OPEN. PR145 exact head `098506e6271d3070c0aa109306f5bc5400f5efe2`; Core run994 and Windows run196 are pending, Security run755 passed. No 100%, ACCEPTED, or item13 closure is claimed.


## §160 — page 513 numeric OCR screening (13.10.2026)

A source-bound visual contact-sheet screen covered 162 numeric OCR candidate boxes on V4 page513. Three candidate errors were confirmed: `54.185` (46.66 confidence; bbox `[5538,491,76,34]`) for printed `−4.185`; `202` (93.87; `[5909,503,44,23]`) as a fragment of `−4.202`; and `4.19` (91.0; `[5986,510,46,22]`) for printed `−4.197`. The two high-confidence fragments lose the sign/prefix; one is also truncated. Reproduction evidence: PR145 `docs/qa/2026-10-13-stage13-ocr-source-bound-sample.json`; local 162-candidate contact sheets are in private `stage13-qa/ocr-full-v4-p492-p534/page-513-numeric-review/`.

This is a numeric screen on one sheet, not full page transcription or qualification; all42 other appendix sheets and nonnumeric page content remain unreviewed. The product continues to BLOCK all43 vector appendix pages. Current PyMuPDF 1.26.6/MuPDF1.26.11 source/combined-page renders match each other, while the old 300-dpi manifest hash still differs because its renderer options/version were not recorded. Item13 remains OPEN. At PR145 exact head `101f8cbcca413689bb8de9808a9ce5eb5eb4eafe`, Security run770 passed; Core run997 and Windows run199 are pending.

## §161 — exact-head PR145 validation and current blockers (13.10.2026)

PR145 remains a draft on exact head `101f8cbcca413689bb8de9808a9ce5eb5eb4eafe`, based on merged candidate `b2c29604d3a8a2a8079a670a7affca4f55b2b9c6`. Fresh GitHub Actions results for that exact SHA: Core run997 SUCCESS, 1,060 tests with 7 skips; HTTP/DOM workflow, real Chromium workflow, and vendored PDF.js checks succeeded. Windows local runtime run199 SUCCESS, including restart/persistence, backup/lock, document CLI, offline PDF viewer, local Ollama inference, and four browser workflows. Repository Security Guard run770 SUCCESS. These are CI results and do not establish a clean physical-PC install or engineering acceptance.

The PR has a separate CodeQL inline alert #45 (`py/path-injection`) at `engineering/local_app/lock.py:52`. A read-only caller trace identifies the line as the second `Path.lstat()` used to recheck a SQLite WAL/SHM unlink race. Its callers include explicit local data-root selection, and uploaded source paths are generated UUID paths; the recovery API is loopback/token/origin guarded. This suggests a likely static-analysis false positive for the supported local folder selection, but the GitHub connector did not expose the alert's SARIF source nodes. Leave the alert unresolved until those nodes are reviewed; a passing Security Guard workflow is not evidence that the CodeQL alert is closed. No production change or dismissal was made for this alert.

The V4 page513 source-bound screen reviewed 162 numeric OCR candidate boxes and confirmed three incorrect/truncated outputs (`54.185` for `−4.185`, fragment `202` for `−4.202`, and `4.19` for `−4.197`). This remains a one-page numeric screen, not full semantic qualification. All43 vector appendix pages remain BLOCK in the app. The 300-dpi renderer hash discrepancy remains unresolved. Item13 stays OPEN; no ACCEPTED/100% claim.

Next action: finish page-by-page source-bound review for pages492–534, record missed labels and uncertain associations, and rerun the app's full acceptance corpus only after its source-ground truth is complete. Then continue physical Word/layout and B3 requirements. Keep original DOCX/PDF immutable.
## §162 — corrected 43-page OCR diagnostic and current work order (13.10.2026)

The full-page visual diagnostic now covers all V4 vector appendix pages 492–534, in three local source-review reports. This means each page canvas/title area was viewed; it does not mean every dimension, sign, decimal, unit, symbol, label, or spatial association was exhaustively reconciled. The reports remain DIAGNOSTIC_INCOMPLETE and grant no acceptance. Original PDF SHA-256 is unchanged: `b5d95b660b35bfb6b2441623635cba91c235efd754bc283dfe1405f075834916`.

A defect was found in the private diagnostic TXT builder, not the application's OCR parser. The helper read Tesseract TSV with Python's default CSV quoting. Literal quote characters in OCR text caused subsequent physical TSV rows to be consumed as one quoted text field, creating tabbed/corrupted TXT artifacts and undercounting candidate words. The production parser already uses `csv.QUOTE_NONE`; its existing literal-quote regression verifies that subsequent TSV rows remain separate. No production OCR code change is justified by this artifact defect.

All43 stored Tesseract TSV files were reparsed without rerunning OCR, using the application's no-quote parsing mode. The original TSV hashes and page coverage were checked; the original PDF was re-hashed. I also passed all43 stored TSVs through the application's `engineering.local_app.ocr.TesseractOCR._blocks`: per-page output counts matched the corrected corpus exactly (22,821 total; no mismatches). The old TXT had raw tabs on pages 492, 495, 498, 503, 504, 512, 513, 526, 532, 533 and 534. The corrected TXT has no raw tabs on all43 pages. Candidate count changes from 19,644 to 22,821 (+3,177); corrected weighted mean word confidence is 71.51 and 6,594/22,821 (28.89%) are below 60. The corrected manifest SHA-256 is `f4716b946e21833f893161aa0c13eff4971b0414616bbade7539c0c0d1d46550`; the reproducible verification report is private at `stage13-qa/ocr-full-v4-p492-p534-quote-none-v2/verification-report.json`. The earlier count/mean/low-confidence figures from the quote-sensitive parser are superseded. These are diagnostic OCR candidates, not accepted text and not an accuracy score.

Reconciliation against corrected TXT already changes several page492–505 observations. The corrected caption screen compares all14 visible figure labels: 12 remain OCR/source mismatches (pages492–500, 502, 504 and505), none are missing; pages501 and503 match. Captions previously reported missing on pages495 and498 now appear as `X.4` and `X.7` (source `Ж.4`/`Ж.7`), and page503 reads `Ж.12`. Page504 still has OCR `+36.600` against source `+38.600`, while the source itself has a separate `+38.800` vs `+38.600` caption conflict. Page505 still contains `+4.2.650` against `+42.650`. The corrected caption audit is private at `stage13-qa/ocr-full-v4-p492-p534-quote-none-v2/corrected-caption-review-p492-p505.json`, SHA-256 `98d42d4e29118125a6f5d02e7e1b997951c160a78134c450717c9090d2d9b9dc5`. Earlier missing-caption/contamination statements are superseded; fine-detail coverage remains partial. The other two range reports remain diagnostic, and any TXT-derived observations on the eleven affected pages require the corrected transcript.

PR145 remains draft at exact head `101f8cbcca413689bb8de9808a9ce5eb5eb4eafe`, based on `b2c29604d3a8a2a8079a670a7affca4f55b2b9c6`. Core run997 (1,060 tests, 7 skips, including HTTP/DOM, Chromium and vendored PDF.js), Windows local runtime run199, and Security Guard run770 passed on that exact head. CodeQL alert #45 (`py/path-injection`, `engineering/local_app/lock.py:52`) remains open. All43 pages still BLOCK in the application; item13 remains OPEN. Overall plan remains 8 DONE in bounded scope, 8 PARTIAL, and 3 OPEN.

Next actions, in order:
1. Reconcile every earlier TXT-based source-review observation with the corrected 43-page text; keep TSV coordinates and source images linked by page and region.
2. Complete the B2 source-ground-truth ledger for every drawing label, dimension, sign, decimal, unit, orientation, symbol, and callout-to-element association across pages492–534. Reproduce missed/incorrect outputs and keep unresolved items BLOCK.
3. Finish Word physical qualification: full table/cell geometry, equations, fields, images, OLE/vector/print streams, fonts, page layout and appendix linkage. The 21 bitmap preview/placement findings do not establish vector-stream meaning or layout equivalence.
4. Build and run the complete B3 semantic regression corpus on qualified source regions, then rerun exact-head Core/Windows/Security CI.
5. Inspect exact SARIF data for CodeQL #45 and resolve it through a verified code correction or evidence-based dismissal.
6. Continue the remaining plan items in their existing order: №14 positive ACCEPTED case; №6 only within the user's deferred calculation boundary; physical Windows release gates №9/12; №15–19 integration and release work. Do not mark anything complete without its stated evidence.

No `ACCEPTED`, 100%, release-complete, or item13 closure is claimed. Free/local operation is preserved; LIRA/SCAD/RES calculations remain deferred.


## §163 — exact-head validation and current work order (13.10.2026)

PR145 remains open/draft at exact head `143dd4a21ee6c101ce52359e1f34caa3aefedbec`, based on merged candidate `b2c29604d3a8a2a8079a670a7affca4f55b2b9c6`. Exact-head GitHub Actions all passed: Core run998 (1,060 tests, 7 skips; HTTP/DOM, Chromium, vendored PDF.js and artifact upload), Windows local runtime run200 (cold/repeat startup, restart, persistence, backup/locks, legacy-stdout CLI, offline PDF viewer, local Ollama inference and four Windows browser workflows), and Security Guard run790. These results qualify the checked software/CI paths only; they do not establish OCR completeness, physical-PC clean install, or engineering acceptance.

The README on PR145 was corrected to match the user's scope: LIRA/SCAD/RES calculations are deferred, while physical-PC clean install/restart and final release remain unverified. It also states that OCR needs local Tesseract plus Russian/English models and that all43 V4 graphics pages remain BLOCK. The app remains free and local.

The §162 corrected diagnostic facts remain current: original V4 PDF SHA-256 `b5d95b660b35bfb6b2441623635cba91c235efd754bc283dfe1405f075834916`; corrected TSV-derived candidates 22,821, mean confidence71.51, 6,594/22,821 (28.89%) below60; application parser produced identical per-page counts from all43 stored TSVs. The page492–505 caption screen found 12/14 OCR/source mismatches and no missing captions. This does not complete source-ground-truth reconciliation: all43 application pages remain BLOCK, and labels, dimensions, signs, units, symbols, orientations, and spatial associations still need exhaustive review.

CodeQL alert #45 (`py/path-injection`, `engineering/local_app/lock.py:52`) remains open. Security Guard is not a substitute for exact SARIF review. Word print/vector semantics, appendix correspondence, full physical layout/font equivalence, renderer-hash discrepancy, complete B3 semantic corpus, and physical-PC release evidence remain open. Overall count remains 8 DONE in bounded scope, 8 PARTIAL, 3 OPEN; this is not a percentage.

Next work: (1) reconcile every earlier TXT-derived source observation against corrected TSV/text and page crops; (2) complete the source-ground-truth ledger for pages492–534; (3) finish Word layout, fonts, OLE/print-stream and appendix-link qualification; (4) build and run the B3 source-bound corpus; (5) inspect and resolve CodeQL #45 from exact SARIF data; (6) continue items14–19 within the user's deferred-calculation boundary and record physical-PC/release evidence. Keep unresolved content BLOCK and preserve originals.

No item13 closure, ACCEPTED, 100%, or release-complete claim is made. LIRA/SCAD/RES calculations remain user-deferred.


## §165 — opaque-image text conflict and Windows test cleanup (14.10.2026)

PR145 remains draft on base `b2c29604d3a8a2a8079a670a7affca4f55b2b9c6`; new head `fe76ee07273179e4ab694668654b39cd1cf76031` adds `NATIVE_TEXT_OCCLUDED_BY_LATER_IMAGE` with character count, coordinates, and SHA-256 per covered native span, while retaining the native candidate and keeping the page BLOCK. A synthetic regression passed. Source-specific observations and document identities remain outside this public plan.

The pinned Windows `.venv-stage13` full local run at the candidate had 1,060 tests, 0 assertion failures, 13 errors, and 49 skips. Isolation showed five errors came from `tests/test_data_backup.py` using sqlite connection context managers that commit/rollback but do not close handles. The test fixtures now close those handles; that module passes 13/13. The other Windows errors/skips remain platform limitations and are not reported as passing. The new PDF occlusion regression passes; `compileall` and `git diff --check` pass. Exact-head Core run1002 and Windows runtime run204 were pending; Security Guard run800 was queued at the last check. Recheck all workflows on the final head before updating status.

Item13 remains OPEN. V4's 43 graphic appendix pages still require source-bound review of labels, dimensions, signs, units, symbols and associations; Word physical layout/font qualification and the full B3 semantic corpus remain open. No ACCEPTED, 100%, or release-complete claim. Free/local operation remains; LIRA/SCAD/RES calculations remain deferred.

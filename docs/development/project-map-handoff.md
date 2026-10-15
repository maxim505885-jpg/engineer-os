# Текущий результат — 15.10.2026: PR150 merged, полный V4 rerun BLOCK

# Передача состояния ENGINEER OS

Официальный candidate `integration/release-candidate-v1` — `db29e4c946e4db5e088e8fdd727c6165365dcc4d`. PR150 слит; Core Tests, Windows local runtime и Repository Security Guard PASS на merged commit. Последнее состояние и полный критерий пунктов — `ENGINEER_OS_PROJECT_MAP.md` §67 и `docs/development/master-plan.md`.

V4 Docling v12 rerun охватил 534/534 страниц и 31 268 source-located blocks, но завершился 52 BLOCK / 55 UNCERTAINTY; 31 table-loss warning, а независимое сравнение нативного текста дало 74,8% weighted unique-token recall. DOCX intake совпал с приватным манифестом; Stage7 обработал 553/553 logical units, 112 BLOCK, auxiliary layout не верифицирован. Полнота PDF/Word остаётся BLOCK; private source identities/hashes не публиковать.

Свежий Stage7/8 одного реального объекта — BLOCK/BLOCK, `ACCEPTED=false`. №6 нормативные gates открыты, LIRA/SCAD расчёты отложены. №15/16 ждут квалифицированного ACCEPTED case; №17 roundtrip не подтверждён; №18 provider receipt/live specialist run не подтверждён; №9 физический Windows cold-start/reboot и №19 release audit остаются незавершёнными. Ни одна программная проверка не заменяет engineering acceptance.

Исторические записи ниже описывают состояния на дату соответствующего PR и не должны использоваться как текущий статус.

## Историческое состояние — §92: PR108 merged; мастер-план синхронизирован с незакрытой аномалией receipts

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

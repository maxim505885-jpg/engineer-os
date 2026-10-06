# ENGINEER OS — план работы 06.10.2026

> Для следующих агентов: выполнять по этапам самостоятельно; для детальных изменений применять superpowers:executing-plans. Реализацию каждого нового компонента планировать перед изменением кода. Не начинать проект заново.

**Цель:** один воспроизводимый локальный инженерный сценарий: ТЗ и документы → анализ → проверяемые источники → профильные проверки → заключение → FINAL AUDIT.
**Архитектура:** использовать существующие local_app, ENGINEER CORE и Document Intelligence. Сохранять границы исходников, черновиков, доказательств и инженерного принятия.
**Стек:** Python 3.12+, SQLite, локальный HTTP/UI, Ollama/Open WebUI, optional PyMuPDF/Docling.
**Основание:** ENGINEER_OS_PROJECT_MAP.md, разделы 29–30; план пользователя утверждён 06.10.2026.

## Обязательные правила

- Бесплатный локальный путь; платные API не обязательны.
- Windows проверять последней. Проверки живых компонентов сначала выполнять в доступной локальной среде.
- Не снимать BLOCK без проверки основания; не считать SUCCEEDED инженерным принятием.
- Не объединять автоматически старые неопубликованные PDF-изменения с опубликованным кодом.
- Не объявлять synthetic модель/OCR проверкой живой модели/OCR.
- После каждого существенного результата обновлять эту карту и план.
- Каждый итог: ✅ выполнено, ❌ не выполнено; затем «Дальше: пункт N — название».
- Номер пункта сохранять между чатами. Подэтап не означает завершение всего пункта.
- Пользователь поручил самостоятельное выполнение; повторное согласование обычных шагов не требуется. Слияние/развёртывание учитывать отдельно.

## Что проверять на всех этапах

1. Перезапуск/остановка: сохранённые результаты, BLOCK и исходники остаются.
2. Неполный документ: пропуски явно показаны; нет ложной полноты.
3. Чужая сессия/изменённый источник: доступ отклоняется, результаты не принимаются.
4. Ошибка модели/parser/solver: явно отделена от инженерного дефекта объекта.
5. Корректный отчёт: система не создаёт замечания ради замечаний.

## 1. Собрать единую проверенную версию — ВЫПОЛНЕНО (КАНДИДАТ, БЕЗ MERGE)

- [x] Сверить активный local HEAD, опубликованный PR49 и соответствие деревьев.
- [x] Проверить цепочку зависимостей кабинета PR38–49 и состояние PR49: draft/open/unmerged.
- [x] Просмотреть launcher, зависимости, пользовательскую инструкцию и CI.
- [x] Исправить устаревшие инструкции, различить preview и automatic analysis.
- [x] Описать минимальное окружение кабинета и отдельное окружение OCR, закрепить воспроизводимый запуск.
- [x] Проверить интеграционный кандидат и CI на точном commit; подготовить порядок интеграции веток.
- [x] Учесть PDF recovery e649885 отдельно, с повторной проверкой до включения.
- [x] Подготовить reviewable общую версию; не объявлять main обновлённым до фактической интеграции.

Результат: одна воспроизводимая версия, известные зависимости и инструкция; test/CI подтверждены для точного дерева.
Файлы: scripts/run_local_app.py, Start_ENGINEER_OS.cmd, requirements-pdf-review.txt, requirements-integrations.txt, .github/workflows/core-tests.yml, docs/development/local-app.md.

## 2. Проверить настоящий анализ документов — ВЫПОЛНЕНО (ОЦЕНКА КАЧЕСТВА, НЕ ACCEPTED V4)

- [x] Проверить живую локальную модель и OCR на native PDF, скане, таблице и графическом листе:6реальныхслучаев, включая V4pages15/500.
- [x] Сопоставить исходник, извлечение и ответы; записать пропуски, время и память: label «Этажи»→«ижее», wordloss «Число»,9/24codes графическойлегенды, OCRRSS3108,7MiB, cgroupOOM0; modelRSSsampler признанненадёжным.
- [x] Зафиксировать качество на небольшом эталонном наборе, затем проверить реальные документы: boundedQA matrix и source/model artifactSHA.
- [x] Проверить успешный actualscan CORE_RUN:250,25с,119,36/130,84с, обеCOMPLETED,UNCERTAINTY,acceptance=false.
- [x] Получить ответы на actualscan table105,86с и V4 Docling table79,12с; неопределённое имя не выдумано как этажность.
- [x] Локализовать graphicalPARSE_FAILED:14×3legend/22cells/merged; sanitizedTABLE_STRUCTURE_UNVERIFIED, BLOCKсохранён.
- [x] Исправить конфликтpreview/currentOCRmetadata вCHAT/CORE_RUN;343Python/4Node/compileall/diffPASS.
- [x] Повторить6OCRcases подLinuxseccompnetworkdeny сtelemetryoptoutдоimports.

Результат: известно, что прочитано/пропущено и какие утверждения модели совпали с источником. Завершение пункта2 не означает идеальныйOCR, полнотуV4 или инженерное принятие. Известные потери подписей и блокировкаграфики сохраняются доsource review/coverage/evidence в3/5/7; preferredRussianOCR не подтверждает bilingual switching; Windows9последней.
Файлы: engineering/local_app/{extraction,automatic_analysis,coverage,worker,core_run}.py; docs/development/stage2-document-quality-2026-10-06.md; docs/qa/2026-10-06-stage2-quality.json. DraftPR54 наPR53.

## 3. Довести обработку больших документов — ВЫПОЛНЕНО (RESUME/BUDGETS, НЕ ACCEPTED V4)

- [x] Сохранять идентичность задания, parser/model/config и обработанных частей для продолжения.
- [x] Добавить явное возобновление модели и повтор только неудачных частей с hash guards.
- [x] Проверить budgets, стоимость по времени и потерю деталей summary на эталонном наборе.

Результат: same-job resume, identity/response/source/config guards, failed/incomplete calls/pages повторяются, completed parts сохраняются. Изменившийся upstream CORE outcome инвалидирует зависимые drafts. 362Python/4Node/actualHTTP+DOMPASS; clipping/time/call budgets раскрыты. OpenWebUI/unknownidentity resume отключён, semantic completeness NOT_CHECKED. DraftPR55 наPR54; main/deployне менялись.
Файлы: automatic_analysis.py, Store/Worker/API/UI, tests/test_automatic_document_analysis.py.

## 4. Подключить остальные форматы — ВЫПОЛНЕНО (ПОДДЕРЖАННЫЕ ЧАСТИ, НЕ ACCEPTED)

- [x] DOCX: абзацы и таблицы с привязкой к источнику.
- [x] XLSX: листы, адреса ячеек, формулы и доступные сохранённые значения.
- [x] DOC: отдельная контролируемая конвертация с сохранением оригинала.
- [x] Объединить upload/Drive/parser/analysis через текущий пользовательский сценарий.

Результат: поддержанные форматы анализируются с проверяемой привязкой и явными ограничениями.
Файлы: local_app/files.py, drive_import.py, automatic_analysis.py, UI; новые format adapters/tests.

## 5. Связать анализ с доказательствами и ТЗ — ВЫПОЛНЕНО (SOURCE TRACEABILITY, НЕ ENGINEERING ACCEPTANCE)

- [x] Построить проверяемый перечень требований ТЗ.
- [x] Привязать существенные выводы к цитате/месту/типу данных и source review.
- [x] Подключить предметные evidence gates; раскрывать непроверенные требования и противоречия.

Результат: для каждого вывода видны основание и уровень проверки.
Файлы: local_app/evidence.py, provenance.py, review.py; document_intelligence/evidence_bridge.py и evidence_validation.py; core adapters.

## 6. Довести профильные проверки — В РАБОТЕ, ПОДЭТАПЫ 6А/6Б ВЫПОЛНЕНЫ

- [ ] Нормы: подтверждать редакцию, применимость, пункт и сопоставление с фактом.
- [ ] Расчёты: единицы, нагрузки, комбинации, опоры, материалы, результаты и solver logs.
- [ ] ЛИРА/SCAD: реализовать семантический маршрут поверх существующего intake; учитывать доступ к решателю.
- [ ] Проверять результаты роли и передавать ошибки контролю качества.

Результат: реальные предметные проверки, а не только модельные черновики.
Файлы: normative/verification.py, calculation/model_intake.py, профильные skills, core runner/contracts и новые adapters.

## 7. Пройти один реальный инженерный кейс — НЕ СДЕЛАНО

- [ ] Выбрать ограниченную задачу по объекту и проверить комплект/ТЗ.
- [ ] Выполнить цепочку источники → факты → проверки → выводы → контроль качества.
- [ ] Провести FINAL AUDIT с доказательной трассировкой; ACCEPTED только при выполнении gate.

Результат: воспроизводимый инженерный кейс, корректные выводы и отсутствие выдуманных данных.
Файлы: core runner/acceptance gate, evidence persistence, профильные skills и case verification report.

## 8. Подготовить удобный выпуск — НЕ СДЕЛАНО

- [ ] Экспорт заключения DOCX с источниками и статусом проверки.
- [ ] Резервное копирование/восстановление и подтверждённая память.
- [ ] Проверить живой Drive/OAuth, диагностику запуска и восстановления.

Результат: результат можно использовать, восстановить и продолжить в следующей сессии.
Файлы: local_app/store.py и UI/API, memory adapters, storage/google_drive.py; новые export/backup adapters/tests.

## 9. Проверить Windows — НЕ СДЕЛАНО, ПОСЛЕДНИЙ ЭТАП

- [ ] Один запуск, Python/dependencies/Ollama/OCR.
- [ ] Native/scanned files, Drive, большой документ, остановка/восстановление.
- [ ] Проверить пакет/инструкцию на компьютере пользователя.

Результат: полный сценарий подтверждён на Windows.

## Параллельное направление: V4 и CAD

11 BLOCK V4 проверять адресно (продолжения таблиц, неоднозначные ячейки, графика). Не блокировать независимые этапы приложения. CAD/DWG развивать после первого подтверждённого инженерного кейса; не считать генерацию текста реализацией графического маршрута.

## Запись выполнения 06.10.2026

✅ План зафиксирован; начат пункт1. Последний code tree 92b593a6c9245725fba621e33431551e46be9c94; local478dfe5, remote22641c3, PR49.
✅ Ранее проверено 329 Python +4 Node и два HTTP/jsdom scenarios; это baseline, не живой OCR/model.
❌ Пункт1 целиком не закрыт: инструкции устарели (local-app.md говорит «первые20/noOCR»), минимальный dependency набор не оформлен как отдельное окружение кабинета. GitHub Actions runs для head PR49 не обнаружены; локальные тесты не заменяют CI.
❌ Пункты2–9 не выполнены. Main не обновлён.
Дальше: пункт1 — Собрать единую проверенную версию; исправить инструкции и воспроизводимое окружение, затем проверить интеграционный кандидат.



## Выполнение пункта 1 — 06.10.2026, кандидат PR51

✅ [Draft PR50](https://github.com/maxim505885-jpg/engineer-os/pull/50): окружение, инструкции и CI. Local e6e1255ae3a42589717c7b482c5a53e8722c8aa6, remote6de0af404dfe0b691a32fefc3a25ee74f46d1e06, дерево2116797f6c2debec1b47888b748d4ee0bd53fe9c совпадает.
✅ Clean Python3.12 venv: PyMuPDF1.26.6 для кабинета; Pillow12.3.0 только разработки. 329Python+4Node, npmci, actual HTTP/jsdom app/Drive, pipcheck, compileall/JS/YAML/diff PASS. Initial RED3 missingPIL исправлен dependency manifest.
✅ CI push и PR50 success. [Единый draft PR51 относительно main](https://github.com/maxim505885-jpg/engineer-os/pull/51) использует тот же commit; main88f1b9c, ahead211/behind0,207files. Stacked PRs не нужно накладывать сверху этого кандидата повторно. Main/deployment не изменены.
✅ Неопубликованные e649885/13200ab не включены; OCR lock и live модель/сканы — пункт2. V4 не перепроверялся.
✅ CI PR51 success: https://github.com/maxim505885-jpg/engineer-os/actions/runs/37467412452 . Его test merge tree совпадает с candidate tree2116797f6c2debec1b47888b748d4ee0bd53fe9c. Пункт1 завершён как reviewable проверенный кандидат. ❌ Main не слит; Windows/liveOCR/model/OAuth не проверены.
Дальше: пункт2 — Проверить настоящий анализ документов. Подготовить отдельное локальное OCR/model окружение и representative набор; установка/качество ещё не проверены.

Перед пунктом2 проверена доступность: docling/onnxruntime не установлены; команды Ollama нет, loopback11434 закрыт. Это состояние текущей среды, не компьютера пользователя. Windows не требуется для начала следующего этапа.


## Выполнение пункта 2 — 06.10.2026, реальные Linux CPU/OCR проверки

✅ [Draft PR52](https://github.com/maxim505885-jpg/engineer-os/pull/52) относительно PR50: privacy fix, Linux OCR snapshot и QA report. Local ffcdf40916e3fdaff4939b51010e7320cd8cb5cc; remote901582da1c9617a1a91063767ba324a1b6f5be14; одинаковое дерево2f526825c66fd955022f8af65a2ea90e8047179c. 7files/590add/4del. PR51 остаётся прежним интеграционным кандидатом, новый fix в него не включён; main/deployment не изменены.
✅ Отдельная Python3.12.14 venv: Docling2.134.0, RapidOCR3.9.2, ORT1.30.0, torch2.14.1+cpu; 108packages pipcheck PASS. requirements-ocr-linux-cpu.lock — испытанный Linux snapshot, не Windows lock. Ollama0.35.1 CPU, Qwen3-8B-Q4_K_M official Qwen HF revision7c41481f57cb95916b40956ab2f0b139b296d974, SHA d98cdcbd03e17ce47681435b5150e34c1417f50b5c0019dd560e4882c5745785. Alias engineer-qwen3-8b-q4km:stage2; registry qwen3:8b не установлен из-за сетевого ограничения. num_ctx8192/num_predict1024/threads4, /no_think в задаче.
✅ 8 реальных OCR extraction jobs: 7 UNCERTAINTY и графический лист500 BLOCK/PARSE_FAILED, всего231.75s. Контрольные native/scan PDF и таблицы, V4p1 native/raster,p15,p500. Job SUCCEEDED не является успешным чтением каждой страницы. Контрольный scan потерял «Число»; scan table исказил «Этажи»→«ижете», числа4/2/0,50 сохранились. V4p15 пять климатических значений совпали с просмотренной таблицей; применимость СП не проверена. English language игнорируется RapidOCR — подтверждён только русский profile.
✅ 6 реальных model jobs через LocalModel/Store/Worker: простой native CHAT132.18s, native-table CHAT119.82s и scan CHAT152.44s прочли контрольные значения правильно. CORE_RUN360.34s сохранил ERROR: две роли FAILED после model calls180.11/180.12s; FINAL AUDIT NOT_RUN, acceptance=false. Scan-table CHAT190.58s и V4p15 CHAT198.45s FAILED с model wait limit180s; ответы не получены. OOM/oom_kill0 при лимите8GiB, это измерение конкретной среды, не обещание работы на другом hardware.
✅ Первый OCR запуск отклонён auto-review из-за Microsoft telemetry, payload не установлен. Незащищённый повтор не выполнялся. По официальной Privacy.md найден полный non-Windows opt-out ORT_DISABLE_TELEMETRY=1 ДО initialization; adapter задаёт его до imports, вызывает platform API и блокирует preloaded ORT без opt-out. Новый защищённый runtime import и OCR benchmark выполнены. strace/ptrace запрещён: полный сетевой аудит не выполнен, Windows startup event не подтверждён. Regression RED→GREEN, итог332Python/4Node/compileall/diff PASS; независимое read-only privacy review без actionable issues.
❌ Пункт2 целиком не завершён: получить успешные CORE роли и ответы на две таблицы, проверить повреждённые OCR подписи и локализовать исключение графического листа. Весь534-page V4 не прогонялся: старые523UNCERTAINTY/11BLOCK и0подтверждённых страниц не заменяются этими derived-page испытаниями. Ни один новый результат не принят. Windows остаётся пунктом9.

[Подробный QA report](https://github.com/maxim505885-jpg/engineer-os/blob/fix/live-document-runtime-20261006/docs/development/live-document-runtime-2026-10-06.md), [метаданные без полных исходных страниц/prompts](https://github.com/maxim505885-jpg/engineer-os/blob/fix/live-document-runtime-20261006/docs/qa/2026-10-06-live-document-runtime.json).
Дальше: пункт2 — Проверить настоящий анализ документов: сначала проверить CPU-профиль/явный thinking control и успешный ограниченный CORE_RUN, затем табличные таймауты и PARSE_FAILED графического листа. reasoning_effort=none в Ollama — гипотеза для следующего bounded test, не испытанное исправление; не увеличивать timeout и не снимать BLOCK без проверки.

✅ CI PR52 success: https://github.com/maxim505885-jpg/engineer-os/actions/runs/37473429471 (remote901582d, дерево2f526825c66fd955022f8af65a2ea90e8047179c). CI проверяет unit/DOM с synthetic transports, не подменяет вышеописанные live CPU/OCR результаты.



## Продолжение 06.10.2026: PR53 / успешный CORE_RUN

Явный `ENGINEER_OS_LOCAL_THINK=false` через native Ollama; timeout180с и acceptance gates сохранены. Production CORE220,19с, роли104,79/115,36с; таблица V4 native91,64с; damaged label text fixture48,97с. Нельзя объявлять OCR исправленным: текущие проверки без Docling, парный OpenAI baseline не повторён. 339Python/4Node/compileall/diff PASS. Draft PR53 на PR52; remote1fe8ce0/tree da3e402a, locald788cbd. Main/deploy не меняли.

Дальше: пункт2 — Проверить настоящий анализ документов: graphical PARSE_FAILED page500, защищённый OCR repeat сканированной таблицы и сверка подписей/пропусков. Пункт2 открыт; Windows — пункт9, последняя. Карта, раздел32.

CI PR53 push37484724688 и PR37484965521 SUCCESS, включая actual HTTP/DOM. Graphical page500 прежний raw checkpoint имеет59texts/1table/2pictures; сравнить старое/новое окружение, не снимать текущий BLOCK по старому результату.


## Актуальный итог 06.10.2026: пункт2 завершён, PR54

✅2 — representative realOCR/modelqualityassessment;343Python/4NodePASS; actualscanCORE250,25с,UNCERTAINTY,acceptance=false. ❌FullV4ACCEPTED/идеальныйOCR/Windows — не выполнены и не заявляются. GitHub CI PR54 PASS: push37489666141 и PR37489670188, включая actual HTTP/DOM. Main/deploy не меняли. Картараздел33.

Дальше:3 — Довести обработку больших документов. Parser/model/config/hash guards, restart/resume onlyfailed parts, budgets/summary loss на эталонном наборе.


## Актуальный итог 06.10.2026: пункт3 завершён, PR55

✅ Safe model/parser resume, durableRUNNING receipts, identity/response/session guards, cumulativebudgets, summarylossdisclosure и persistedBLOCK. 362Python/4Node/actualHTTP+DOMPASS. Одинreview, дваImportant исправленыRED→GREEN. GitHub CI PR55 PASS: push37497252188 и PR37497256126, включая actualHTTP/DOM; test-merge tree совпадает с опубликованным.. ❌FullV4ACCEPTED/semanticcompleteness/liveQwenresumerepeat/OpenWebUIresume/Windows не заявляются выполненными. Main/deployне менялись. Картараздел34.

Дальше: пункт4 — Подключить остальные форматы: DOCXparagraphs/tablesrefs,XLSXaddresses/formulas/cache,DOCcontrolledconversion,общийupload/Drive/analysis.


## Актуальный итог 06.10.2026: пункт4 завершён, PR56

✅ DOCXparagraphs/tables/locators, XLSXsheets/addresses/formulas/storedvalues, controlledLinuxDOCconversion с original/derivedSHA и cachedresume. Общие upload/Drive/automaticCHAT/CORE. Реальные DOC/DOCX/XLSX492/487/125units;53/48/0BLOCK раскрыты; модельcontrolled, actualparser/converter. 376Python/4Node/оба actualHTTP+DOMPASS. Один review, дваImportant RED→GREEN. DraftPR56 наPR55; tree4c6e8f96e0e4d694773a6283506ae64e46506991. Картараздел35.
❌ Officecomplexlayout/semanticcompleteness/evidenceacceptance/liveQwenOffice/liveOAuth/Windows не заявляются выполненными. Converter identity пока launcher-only: не обновлять LibreOffice runtime во время задания. Main/deploy не менялись.
Дальше: пункт5 — Связать анализ с доказательствами и ТЗ.

GitHub CI PR56 PASS: push37501193754 и PR37501199607, включая actualHTTP/DOM; test-merge83f0a6c tree совпадает с published4c6e8f96. 


## Актуальный итог 06.10.2026: пункт5 завершён, PR57

✅ Версионированный user-authored перечень требований, append-only выводы/relations/candidates/review snapshots. Office sourcebinding revalidated; DOC derivedunverified не originalconfirmation. CHAT/CORE context/identity/resume guards; source gates каждого требования и наблюдения; UI source→candidate→review→assessment/reload; pollingfocus/selection/history сохранены. 400Python/4Node/оба actualHTTP+DOMPASS. Actual DOCX/XLSX SOURCE_LINKED/UNCERTAINTY; DOC BLOCK; protocolQA с controlledmodel/testТЗ, не engineeringcase. Одинreview и одинImportantfixpass; hiddenfindinggates regradedImportant и исправлены RED→GREEN. DraftPR57наPR56; дерево70b36f9f977736a7fd5e0811478519ba43b5016b, картараздел36.
❌ Полнота/семантикаТЗ, типданных, нормативная/расчётная проверка и инженерное принятие не подтверждены. SUPPORTS/CONTRADICTS декларациипользователя; DOCoriginalconfirmation/Windows не выполнены. Наследованный converterruntimefingerprintlauncher-only открыт. Main/deployне менялись.
Дальше: пункт6 — Довести профильные проверки.

Initial CI PR37504947830 PASS, push37504942036 FAIL из-за ZIPfixture timestamps в inheritedtest; controlledclock RED→GREEN, preservation expected сравнивается с originaluploadbytes. Local400suite повторён послеfix; productionlogic не менялась.

GitHub CI final PR57 PASS: push37505430193 и PR37505435661, включая actualHTTP/DOM; head386cde2e, testmerge69a6d07c tree70b36f9f совпадает с опубликованным/локальным. Начальный ZIPfixture failure устранён, не скрыт повтором.
Дальше: пункт6 — Довести профильные проверки.


## Продолжение пункта6 — подэтап6А, 06.10.2026

✅ Строгие normative/calculation contracts, bounded Decimal/SI arithmetic primitive и deterministic domain prerequisite BLOCK в CORE_PLAN/CORE_RUN/QC/UI/Store. DraftPR58 наPR57, remote f006d1efea7072eaa1ffc60a716edd4c49378869/local e1475715c7fb7066a2a3ddaec715b946c03a96ef, tree b80f78cfa8db9a00132444d8363f158bdc57521e. 410Python/4Node/actualHTTP+DOM PASS; one review, copied-plan status fixed RED→GREEN.
❌ Пункт6 полностью не выполнен: real norm verification, source-bound quantities/domain packet, calculation semantic route и solver execution остаются открыты; арифметика пока standalone, не UI/API/source facts. acceptance=false, FINAL AUDITNOT_RUN, main/deployне менялись. Windows9последней. Четыре верхнихcheckbox6 остаются пустыми.
Дальше: пункт6 — Довести профильные проверки.

GitHub CI PR58 PASS: push37508689975 и PR37508694510, включая actual HTTP/DOM. Head f006d1efea7072eaa1ffc60a716edd4c49378869; test-merge 87ac8fdea85e6470328303e1e42ac82b8a8f767e, tree b80f78cfa8db9a00132444d8363f158bdc57521e совпадает с опубликованным и локальным.


## Пункт6 — подэтап6Б, 06.10.2026

✅ Неизменяемые source-bound normative/calculation packets, точная привязка numeric fields к цитатам/actual_condition/requirement, формы/API, per-form revision guard и CORE/QC/live+resume identities. DraftPR59 наPR58, remote19a31cfb7d1a032b1bf922cfa1b4c1245281c950/local16b28a4d729a393e58f5f1c8bdee6fb97732dc24/tree35b4579f5b77728b944cb21926088e7b313bd1f3. 424Python/4Node/actualHTTP+DOM PASS; один review/3Important fixed RED→GREEN. ActualDOCX paragraph25→UNITS SOURCE_LINKED/BLOCK/restart/originalpreserved; controlledmodel, не acceptedengineeringcase. Два actualLIR inspected metadataonly, binarypayload NOT_DECODED.
❌ Четыре checkbox6 остаются пустыми: authority edition/applicability/clause, actual data semantics/class, calculation semantic route/solver ещё открыты. Все9 declaredroles не означают performedcalculation. Main/deployне менялись, FINAL AUDITNOT_RUN/acceptance=false; Windows9последней.
Дальше: пункт6 — Довести профильные проверки: semantic calculation package и verifiednormativechain.

**Проверка публикации 6Б:** GitHub CI push [37511687457](https://github.com/maxim505885-jpg/engineer-os/actions/runs/37511687457) и pull_request [37511692882](https://github.com/maxim505885-jpg/engineer-os/actions/runs/37511692882) — SUCCESS для HEAD `19a31cfb7d1a032b1bf922cfa1b4c1245281c950`. Тестовый merge `cbfdf85d3935480d9aaaac8d32a0973f4587b14a` имеет то же дерево `35b4579f5b77728b944cb21926088e7b313bd1f3`, что проверенная локальная версия. PR59 открыт как draft, не слит. Пункт 6 остаётся в работе.

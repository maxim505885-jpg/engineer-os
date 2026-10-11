Ты продолжаешь существующий проект ENGINEER OS. Не начинай разработку заново. Это передача состояния на 12.10.2026 (Europe/Moscow), а не утверждение о завершении проекта. Сначала проверь GitHub: данные могли измениться после этой передачи.

## Цель и рабочий договор
Бесплатное локальное инженерное приложение для обследования зданий: ТЗ → документы → извлечение информации → доказательства → профильные проверки → заключение → FINAL AUDIT. Windows, Python, Ollama, Open WebUI; у пользователя ЛИРА САПР 2024. Никаких обязательных платных API. Оригиналы не изменять. Не выдумывать данные, нормы, расчёты, дефекты или результаты проверок. BLOCK из-за недостатка данных не является доказанным дефектом конструкции.
Пользователь поручил выполнять доступную работу самостоятельно: анализ → реализация → проверка → исправления → итог, без повторного «продолжать ли». После существенного результата обновлять карту и master-plan на GitHub. Различать: реализовано; проверено тестами; проверено на реальном файле; объединено в кандидат; установлено на ПК; инженерно подтверждено.

## Источник истины
GitHub: https://github.com/maxim505885-jpg/engineer-os
Общая ветка: integration/release-candidate-v1
Последний подтверждённый объединённый кандидат: 1a765fa1766add7b5c5950a98893cd6e8099c6f8
Его tree: f750e239a41e90099313b234170059b8c213e60e (PR139 MERGED).
Карта/план: docs/project-map-handoff-20261005.
Прочитай AGENTS.md, ENGINEER_OS_PROJECT_MAP.md, docs/development/master-plan.md, docs/development/project-map-handoff.md именно из актуальных GitHub-веток. Последний раздел теперь §137, предшествующий §136 содержит ход реализации и неудачные CI. Старые §87 и ранние ограничения являются историей; их нельзя считать текущим состоянием.
Полная передача: docs/development/continuation-prompt-20261012.md.
Диагностический черновик: scripts/probe_formula_runtime.py на docs-ветке; это compile-only prototype, не выполненный production fix.

## Текущая задача
Закончить интеграцию отобранных локальных Word/PDF/DWG/ЛИРА/SCAD инструментов и проверить реальную работу, прежде всего пункт №13. Пользователь просил добавление инструментов ЛИРА, но не поручал запуск расчёта на своём ПК. Не требовать реальные RES или запуск R4 для продолжения независимой работы. Не переписывать существующие память, заключения, CAD, backup и Windows-маршруты.

## PR140 — опубликовано, НЕ объединено
https://github.com/maxim505885-jpg/engineer-os/pull/140
Ветка: feat/local-tooling-resume-20261011
Текущий проверенный через GitHub head: d2ed01389a02a6a953c4f3c579d20183ee8e37d5
Tree: c89a0368eea83ae28df4017092efac79e6064808
OPEN / DRAFT / NOT MERGED. Этот код не установлен на ПК пользователя.
Предшествующий head7b8092fc8a62c27fac272e0a910990b55a1b4835/tree4edb4bb9613890ab7709e6c6a77217cfaaff6557. Не переносить PASS между heads.

В код PR140 добавлено:
1. engineering/local_app/word_formula_preview.py: render_formula(data,part,zero_based_ordinal) → PNG+dossier через пассивный scaffold и локальный LibreOffice. Source formula hash совпадает с source_assets ET.tostring, включая sibling tail; isolated fragment hash отдельно. Сохраняются пассивные свойства абзаца/OMML/styles/settings/theme/font declarations; оригинальный package, OLE, макросы, внешние связи и встроенные шрифты не открываются конвертером. Уничтожение потомков, время/пиксели/XML/PNG/PDF/log limits; пустой PNG отвергается. Windows network_denied=false отражает отсутствие OS enforcement. Source layout/fonts/math остаются непроверенными.
2. word_images.py: nearest-ancestor cached_processed_bitmap для WDP, статус/причина связи, ordered declared_effects. Эффекты не применены.
3. emfplus.py + emf_text.py: строгая инвентаризация EMF+ comments/records/metadata с ограничениями и явными coverage gaps. Это не полный EMF renderer.
4. table_readback.py/table_worker.py: optional isolated img2table1.4.2/Tesseract и PaddleOCR PPStructureV3; только выбранный исходный PDF bbox, точный PNG input, source/raster hashes, coordinate mapping, кандидатные spans. ENGINEER_OS_TABLE_PYTHON — отдельный Python; ENGINEER_OS_TABLE_LANG; ENGINEER_OS_PADDLE_MODELS_MANIFEST — восемь заранее установленных локальных model directories. Отсутствующие зависимости/модели — UNAVAILABLE. Paddle реально не запускался.
5. ui/pdf-viewer.js + vendor/pdfjs: официальный pdfjs-dist5.4.624/Apache2, локальный readonly modal viewer, страницы/масштаб/100MiB source limit/bounded canvas/races; embedded JS/XFA/eval/annotation actions/external fonts не выполняются. Original bytes клиент сверяет по размеру/SHA.
6. engineering/calculation/native_results.py + upload_analysis.py: строгий R4 result ZIP reader, dispatch раньше input/generic ZIP.
7. document_visuals.py/server.py/tooling.py/UI/analysis_identity.py: authenticated source-bound routes и новые действия сайта.
8. optional pywebview wrapper scripts/local_desktop.py использует прежние Store/Worker/server/DataLock; native окно физически не проверялось. PyVista requirements — лишь подготовка будущей визуализации, не новый native viewer.

API:
- GET /api/tooling: наличие/конфигурация ≠ исполнение.
- POST /api/sessions/{sid}/files/{fid}/formula-preview: part,ordinal,candidate_id,expected_sha256.
- POST /api/sessions/{sid}/files/{fid}/tables: page (1-based),bbox (unrotated CropBox-relative PDF points),backend (img2table/paddleocr),expected_sha256.
Общие preview slots=2, проверка токена/Host/Origin/project/source identity. Результаты не создают принятых evidence и не дают ACCEPTED.

Документы runtime-ветки:
docs/development/local-document-tooling.md
docs/local-tooling/offline-raster-tables.md
scripts/LOCAL_DESKTOP_AND_PDF.md
requirements-table-img2table.txt / requirements-table-paddleocr.txt / requirements-desktop.txt / requirements-visualization.txt.

## Проверки — с границами доказательства
До диагностического head локально:1019 tests OK/82.616s/21 environment skips; genuine table backend11/11;10 Node dashboard tests; HTTP/DOM;6 прежних Chromium routes+новый actual-app route; PDF viewer DOM/Chromium; architecture/compile/JS/diff checks. Independent review:56focused tests/3skips+11genuine table+Chromium PASS.
Исправлены найденные review дефекты: formula tail identity, пустой raster, нестандартные Word part paths, Windows resource import/cleanup calls, inverted bbox after clipping, Paddle config variable mismatch. OLE preview восстановлен установкой уже требовавшегося olefile0.47; decoder ради этого не переписывался.

На head7b8092f:
Core38173794008 FAILED:1020tests/179.680s,1failure/1error/4skips.
Windows38173794012 SUCCESS:125tests/30.758s,9skips, cold/repeat/restart, realOllamaqwen3:0.6b, viewer+7UIroutes. Windows без LibreOffice честно вернул UNAVAILABLE для формулы.
Security38173794002 SUCCESS.

На текущем headd2ed013:
Core38174414604 FAILED на раннем actual formula step.
Windows38174414644 SUCCESS (заново проверено GitHub12.10.2026).
Security38174414687 SUCCESS.
Не объединять PR140 и не закрывать №13 при failed Core.

## Блокер A — distro LibreOffice
В Ubuntu CI версия запускается, но conversion.log завершается exit1, единственный сохранённый текст:
Warning: failed to launch javaldx - java may not function correctly
Это симптом, НЕ доказанная причина; libreoffice-math в CI установлен. Не ставить JRE и не ослаблять sandbox наугад. _run теперь сохраняет bounded1200-byte diagnostic с именем стадии и exitcode; actual CI не отключён.
Локальный runtime LibreOfficeDev26.8.0.0.alpha0 строил формулы, Ubuntu distro LibreOffice не прошёл.
Следующий шаг: на фиксированном безобидном synthetic scaffold сравнить sandbox launcher, SAL_USE_VCLPLUGIN=svp, direct soffice.bin, controlled memory profile, отдельный unsandboxed benign reference. Черновик probe сохранён на docs-ветке; не использовать user original для unsandboxed контрольного опыта. Получить причину, исправить минимально и повторить реальные тесты/CI.
Тест завершения потомков исправлен condition-based wait после SIGKILL. Дополнительно выявлено: в некоторых временных средах PID namespace не совпадает с procfs; нельзя проверять чужой /proc/PID. Черновая идея — ребёнок записывает собственный /proc/self/stat PID, родитель ждёт handshake. Этот дополнительный тестовый fix НЕ подтверждён в опубликованном d2ed013; восстановить, если всё ещё нужен.

## Блокер B — Tesseract hOCR / потеря реальной таблицы
Ранее img2table на eng-onlyV4p5 дал5 сомнительных cells; rus+engp5 и настоящая21x4таблицаp55 дали0tables. Не считать их полноту/текст подтверждёнными.
Последняя диагностика отдельного исполнителя: detector с OCR=None распознаёт p55 при scale2/3/4 как21x4/84cells. В custom TESSDATA_PREFIX были только traineddata, без configs/hocr. img2table1.4.2 вызывает именованную конфигурацию hocr; Tesseract выдаёт plaintext, parser видит0hOCR words и таблица исчезает даже при confidence0.
Это найденная локальная диагностическая причина, но исправление НЕ опубликовано в d2ed013 и в новой среде нуждается в воспроизведении.
Следующий fix: явно вызывать Tesseract с -c tessedit_create_hocr=1, сохраняя EXACT исходный PNG input (без незадокументированного JPEG reencode); при OCR empty не терять найденную геометрию — оставить кандидат с явным TEXT_UNAVAILABLE. Проверить missing configs/hocr, реальные p55 и merged/raster cases; не объявлять символы/объединения верными автоматически.
Реальная p55 область: [55,68,582,462]; native table bbox[61.22400093078613,74.27996826171875,576.7200012207031,455.1099853515625].
Предыдущая p5 область[80,60,550,720] НЕ положительный qualified OCR-кейс.
Официальный rus.traineddata из tesseract-ocr/tessdata_fast: Git blob b146cb2263acbc6383f8e92ea0ce759537687bb8,3861738bytes,SHA e16e5e036cce1d9ec2b00063cf8b54472625b9e14d893a169e2b0dedeb4df225,Apache2. Сохранение custom tessdata должно включать нужные configs либо исключить зависимость от них явными параметрами. Не предполагать наличие языков или локальных путей прошлого чата.

## Реальные исходники — находить в подключённом хранилище, не просить загрузить снова
DOCX «15.09.2026 ТЗК БЦ ул. Набережная 28А на диск(1).docx»
Library ID libfile_10792d9386208191b103ee233d892250
147210288bytes
SHA b253439bdd673a775eaf209ca7d398d766efae5f4a18ac33fa6679f7faae28a5.
Читает14684logical units. Новый native reader ранее добавил6 элементов header/footer/служебных разделителей, сохранив14678 прежних. Native страницы/Word page placement не подтверждены.
В PR140-проверке:11WDP/cache pairs,12effects,19uniqueEMF+assets,112comments,315records. Локально reported authenticated HTTP preview всех41OMML с exact hashes, evidence0, unchangedoriginal; это derivative rendering, не визуальная Word/font/math equivalence. Доступность всех новых сырых QA PNG/JSON после отката scratch не подтверждена: при отсутствии повторить и сохранить доказательства долговременно.

PDF «15.09.2026 ТЗК БЦ ул. Набережная 28А V4 сшито с графикой.pdf»
74522583bytes
SHA b5d95b660b35bfb6b2441623635cba91c235efd754bc283dfe1405f075834916.
534pages. PDF.js реально отрисовал первую/последнюю страницу; это НЕ проверка всей графики/таблиц. Сначала искать по имени в подключённом хранилище и сверить SHA.
Если требуется альтернативный Drive reference: file ID1Ycw-dcevqNSHgvb_y0pVa7B1lM4uhK6g, проверять доступ и SHA.

LIRA input ZIP:
ENGINEER_OS_LIRA_EXPORT_c099d41396484fd9a9227714961bd1ae.zip
Library libfile_0d643d8cd40c8191bc8170ff5b059cbe.
PR101 MERGED, inputreader прочитал31tables/37083nodes/44086elements/16loads. Для3315KE57 auxiliary rigidity не извлечены default API — ограничение извлечения, не доказанный дефект.
R4 exporter ZIP ENGINEER_OS_LIRA_RESULTS_R4.zip
Library libfile_f4a5b33913408191861b6596fd131458.
PR102 OPEN/DRAFT, branch feat/lira-results-export-20261009, headb623bc3abd58adbf46432fbc4e3adb96d647235c. Не объединён; это exporter, не реальный completed solver result.

## R4 reader contract
Manifest schema1, kind ENGINEER_OS_LIRA_RESULTS_EXPORT.
values_00001.tsv etc., exact10columns:
request_type,subject_id,load_case,shape,history,section,component,value,status,hresult.
Requests1–4 и8 — действительные числовые queries;5–7/9/10 — availability diagnostics.
Finite EXPORTED values отдельно от UNAVAILABLE; ноль является значением, sparseIDs допустимы. WHOLE_RUN_NOT_PART claims не равны наблюдениям части; per-request counters должны покрывать observed rows. Поздний UNAVAILABLE может сохранять EXPORTED ранних chunks при согласованных counters.
200krows/40files/4096charsline/1MiBmanifest/100samples limits. Acceptance/full extraction/model-result association/solver completion не подтверждены. Новая реализация reader не даёт права утверждать получение реального RES.

## Отбор upstream — не устанавливать всё подряд
Источники: docs/development/document-tooling-repositories-20261011.md и lira-scad-tooling-repositories-20261011.md на docs-ветке.
LibreOffice, img2table, PaddleOCR, PDF.js, pywebview используются в описанном объёме; Docling/PyMuPDF/ezdxf/LibreDWG/Playwright уже были интегрированы.
GMFT — резерв native tables безOCR; ONLYOFFICE иdocxjs — резерв с ограничениями Word layout/fields.
SCAD Office — официальный SCAD++ C API/ScadAPIX.hxx установленной версии; adapter ещё НЕ реализован, SDK/license/vendor execution не подтверждены. Это не OpenSCAD и не industrial SCADA.
pywin32 — COM infrastructure; pywinauto — GUI fallback; PyVista — будущая визуализация.
scadlira GPL3 ограничен геометрией/закреплениями, нагрузки/РСУ не реализованы. SpaceFramer/3DFACE2HATCH — узкие инструменты с неустановленной лицензией. OgibArm source-closed; StructOS download-only/free-during-beta. Их поиск не является внедрением и не делает их обязательным бесплатным ядром.

## Сохранность и порядок продолжения
1. GitHub — основной источник опубликованного кода. Временная среда уже неоднократно откатывалась к старому checkout72d323a; не верить cwd/HEAD, агентским именам или старым локальным PASS. Проверить branch/head/tree и восстановить рабочую ветку из remote, сохранив реальные пользовательские изменения.
2. Незавершённые hOCR fix, procfs test refinement и distro reproduction нельзя считать сохранившимися. Их точные contracts/диагнозы переданы выше. Probe черновик сохранён в docs-ветке отдельно от tested production.
3. Сначала исправить LibreOffice и hOCR. Meaningful regression → realfile → full suite/HTTP/DOM/Chromium → independent review → finalhead Core/Windows/Security. Merge PR140 только после устранения важного дефекта и успешного CI на том же head; сверить merged tree. Не отключать failing actual test ради зелёного статуса.
4. После каждого существенного результата обновлять карту/master-plan/handoff. Небольшие проверенные code checkpoints публиковать своевременно, чтобы откат scratch не уничтожал часы работы.
5. Репозиторий не дублировать как архив в хранилище; отдельные QA PNG/JSON/logs/source SHA manifests сохранять долговременно, с указанием library IDs/versions. Сырые новые QA прошлого запуска сейчас не гарантированно доступны; существующие архивы предыдущих этапов указаны в §132/§133.
6. Не просить пользователя запускать solver, экспортировать RES или переустанавливать приложение для продолжения независимого исправления reader/UI.
7. Итог19пунктов:8выполнены в программном объёме,8частичны,3открыты — №13/14/19. №13 требует qualified fullV4 graphic/raster/mixed table semantics/associations, оригинальный Word layout/fonts/fields/formula equivalence и представительный корпус. №14 нет реального положительного ACCEPTED; №19 стабильный финальный выпуск не объявлен. Установка на ПК не подтверждена.

> **ТЕКУЩЕЕ СОСТОЯНИЕ 13.10.2026 / §161:** PR145 draft exact head `101f8cbcca413689bb8de9808a9ce5eb5eb4eafe` (base `b2c29604d3a8a2a8079a670a7affca4f55b2b9c6`). Core run997 SUCCESS (1,060 tests, 7 skips; HTTP/DOM, Chromium and vendored PDF.js passed); Windows run199 and Security run770 SUCCESS. CodeQL #45 (`py/path-injection`, `engineering/local_app/lock.py:52`) remains unresolved pending exact SARIF-source verification; Security Guard success does not close the alert. Page513 numeric screen found three OCR errors; all43 vector pages remain BLOCK and №13 OPEN. See §161 and PR145 QA JSON.

Ты продолжаешь существующий ENGINEER OS. Не начинай заново. Пользователь передаёт тебе дальнейшую разработку: доведи пункт13 до подтверждённого завершения, затем двигайся по действующему плану. Работай самостоятельно, исправляй подтверждённые дефекты, проверяй результат и сразу обновляй карту GitHub. Не ограничивайся предложением плана.

## Что создаём
Бесплатное локальное инженерное приложение Windows: ТЗ → документы → извлечение → доказательства → профильные проверки → заключение → FINAL AUDIT. Нужны чат, история, память, очередь, CAD и восстановление. Обязательные платные API не вводить. ЛИРА/SCAD/RES и реальные расчёты пользователь отложил; они не являются причиной незакрытого пункта13.

## Где код и источник состояния
Репозиторий: https://github.com/maxim505885-jpg/engineer-os
Рабочий кандидат: integration/release-candidate-v1.
Последний merged base: b2c29604d3a8a2a8079a670a7affca4f55b2b9c6, tree c1f44ad1839ecf763faedb98deaf87fd219e5e75, PR144 MERGED. PR145 draft current head: 1bb9b37240dc93eccb3682e704228838909c2517. Exact-head Core run992 (1,060 tests/7 skips; HTTP/DOM, Chromium, vendored PDF.js PASS), Windows run194 and Security run746 all SUCCESS. See §157–158 in the maintained map/master plan. Item13 remains OPEN.
Живая документация находится в ОТДЕЛЬНОЙ ветке docs/project-map-handoff-20261005:
- ENGINEER_OS_PROJECT_MAP.md — читать верхнюю актуальную сводку и последние разделы, особенно144–148.
- docs/development/master-plan.md — критерии и порядок работы.
- docs/development/project-map-handoff.md — передача состояния.
- docs/development/codex-handoff-20261013.md — этот промт.
В начале проверь реальные HEAD/ветки/PR/CI; более свежие подтверждённые результаты имеют приоритет. Сначала прочитай AGENTS.md. Не принимай старые исторические SHA в карте за текущий кандидат. Не работай сразу в main, не перезаписывай чужие незакоммиченные изменения и не делай reset --hard.
На ПК ранее использовался C:\Users\maxim\engineer-os; проверь фактическую папку. Workspace предыдущего ChatGPT /workspace/scratch/6b58cd5bc92e — временный и может быть недоступен в твоём окружении. Не рассчитывай на него.
Дополнительные ранее исследованные репозитории/адаптеры перечислены в карте. Не копируй их повторно и не объявляй установленными без проверки.

## Подтверждённый результат
PR144 добавил явный выбор OCR-языка eng/rus+eng для выбранного фрагмента, связал запрос/движок/досье/history, сохранил исходные и обработанные PNG и координаты. Автоматической подмены оригинала/принятия не делает.
Предыдущий полный прогон: local1057tests/9skips; Core1057/7skips, Windows158/18skips, Security SUCCESS. Genuine LatinOCR в Windows не подтверждён: модели там отсутствовали. Эти CI относятся к PR144, не к последним QA-only проходам. Физический ПК пользователя этим не проверен.
Квалифицированы4таблицы V4p55–56:170 уникальных ячеек/192 позиции,89 точных чтений HTTP/worker/reopened history. Это не весь документ.
43 листа графики сопоставлены с V4: graphics1–21→p492–512,geodesy1–22→p513–534. Геометрические сигнатуры и контрольные рендеры совпали43/43 одним PyMuPDF; это не независимые движки/не полная семантика. Источники векторные, не растровые:40 листов без native words, изображения отсутствуют.6 выбранных надписей V4p509/p525 прочитаны точно через приложение.
Word/PDF:244 несопоставленных абзаца диагностически разобраны:229 найдены после проверки переносов/порядка/рамок,15 объяснены OMML/noBreakHyphen/разрывами страниц/оглавлением. Не считать это3086/3086 literal qualification.3 номера оглавления p3 точно восстановлены OCR.
Найден второй DOCX V4 на Drive. Все15651 raw w:t paragraph strings и XML41OMML совпали с прежним DOCX;642media payloads сохранены+12добавлены,21embedding byte-identical. Размещение и оформление не доказаны.
Текущий parser разобрал обаDOCX:14685/14689units,12826table_cells каждый,682/696image references,21embedded objects и41equation units. Все12826 логических part/table/row/column/source_grid совпали;148полных locator dictionaries различаются images/drawing labels. Не заявлять complete locator equivalence.
Все41OMML/preview PNG hashes проверены; обозначения и числа сопоставлены с кандидатными страницами V4. Ordinals27–29 наp337; p338 только соседний контекст. Это ограниченная визуальная сверка, не полная физическая/шрифтовая эквивалентность, не проверка правильности расчётов. Independent review подтвердил этот объём. Focused61Wordtests PASS.
Последний pass9:71поле в каждомDOCX —57PAGEREF,1TOC,11SEQ,2PAGE. Структура balanced, orphan/unfinished fields не выявлены. Все71cached results одинаковы.57bookmark names отличаются, но все57targets существуют, их текст/сохранённая страница одинаковы; все57target texts найдены native вV4 наcached pages. Это проверка cached результатов и ссылок; поля заново Word не вычислялись.
12новыхmedia payloads связаны с14ссылками приложения: в основномtable1rows2–9 иparagraph63/507/530/703/705; присутствует дополнительныйHD_PHOTO_LAYER. Визуальная композиция ещё не квалифицирована.

## Исходники — не смешивать версии
1. PDF «15.09.2026 ТЗК БЦ ул. Набережная28А V4 сшито с графикой.pdf»,534страницы,74522583байт,
SHA256 b5d95b660b35bfb6b2441623635cba91c235efd754bc283dfe1405f075834916.
Drive ID1Ycw-dcevqNSHgvb_y0pVa7B1lM4uhK6g.
2. Старый «15.09.2026 ТЗК БЦ ул. Набережная28А на диск(1).docx»,147210288байт,
SHA256 b253439bdd673a775eaf209ca7d398d766efae5f4a18ac33fa6679f7faae28a5.
3. «15.09.2026 ТЗК БЦ ул. Набережная28А V4.docx»,147560922байт,
SHA256 c0ca593f4dec5c101d01282523032e05b147e9169fb043a144af5fbd479a5685.
Drive ID1JXWTnNH27To91_S5Fv5KFVy5hw6WczRU.
ОбеDOCX имеютcached491pages; PDF491основных+43графики. Время создания иcached count не доказывают Word-export provenance. Embedded font programs отсутствуют. Не называйV4 эталоном конкретного Word-рендера без проверки.
Доступ/файлы проверяй реально. Большие временныеDOCX-копии ранее становились неполными: перед каждым использованием проверьSHA/ZIP. Pass9сохранил19XML/rels частей каждогоDOCX сsource-manifest иper-part SHA.

## QA и сохранность
Архив ENGINEER_OS_STAGE13_QA_20261012.zip, постоянный IDlibfile_fa998953e1ac81919d5c9d8bd4acd15d. Забери последнюю версию через доступные инструменты либо файл, переданный пользователем. Он содержитpass1–5,pass8 и добавленныйpass9. Rawpass6/7 были утрачены при очисткеworkspace; их результаты сохранены вGitHub§145–146. Не объявлять утраченные receipts восстановленными.
Карта имеет постоянныйIDlibfile_947c39aad11c81918c7887832c1411bb; при доступе обновляй ту же карту с фактической version guard. GitHubдокументы обновляй обязательно даже без Library.
Последние проверки production-код не меняли; отдельных незакоммиченных исправлений приложения нет. QApass9скрипты диагностические, не productionфункции.

## Что делать дальше
1. Проверь действующий план и реализованный поддерживаемый объём, воспроизведи необходимые проверки.
2. Продолжи B2: фактическое отображение/обновление полей вWord, позиционирование/композиция графики, OLE/WDP/EMF, исходные шрифты и полная физическая эквивалентность. Проверь добавленные12media и148locator differences по происхождению/контексту. НаличиеPNG иBOUND_PACKAGE_IMAGE не означает content qualification. Не устанавливай коммерческие шрифты/Word или новый конвертер без основания; используй имеющиеся законные локальные средства.
3. Если Codex имеет доступ к Windows/Word, подготовь source-bound контрольный экспорт, зафиксируй версии/шрифты/хеши, не меняя оригиналы. Если доступа нет, явно обозначь конкретное невыполнимое действие и продолжай независимые задачи. Не подменяй исходныйWord другим рендером.
4. Продолжи B3: представительный corpus остальных raster/mixed/merged таблиц и графических областей, мелкие подписи, минусы/десятичные знаки/единицы и связи значений сэтажами/осями/заголовками. Проверяй ошибки и пропуски, а не только количество страниц.
5. Подтверждённый баг → воспроизводимый failing test → минимальное исправление → реальные проверки → review → CI проверенногоSHA → интеграция по правиламрепозитория.
6. Обновляй карту/план/handoff после каждого существенного результата: точныйHEAD/tree/PR,тесты/skips,проверенный объём,ограничения и следующий шаг.
Пункт13 сейчас OPEN. Всего8DONE/8PARTIAL/3OPEN. №14ACCEPTED и№19release тожеOPEN. Не закрывай13 по одной выборке, совпадениюхешей, успешнымтестам или снятиюfail-closed ограничений. Не обещай работу в фоне после завершения ответа.
Работай до конкретного проверенного результата, без повторных вопросов «продолжать?». Если обязательный критерий реально зависит от отсутствующего доступа/исходника, объясни точную причину и минимальное действие пользователя; не выдавай фиктивный100%.


## Дополнение — Windows Word/PDF и CLI, 13.10.2026

Draft PR145: https://github.com/maxim505885-jpg/engineer-os/pull/145, current head `1bb9b37240dc93eccb3682e704228838909c2517`, based on merged candidate b2c29604d3a8a2a8079a670a7affca4f55b2b9c6. Full details and source evidence are in map/master-plan §149 and `docs/qa/2026-10-13-stage13-word-reference-windows.md`.

Read-only Word2021 build16.0.14228.20204 comparison used a byte-identical copy of V4 DOCX SHA `c0ca593f4dec5c101d01282523032e05b147e9169fb043a144af5fbd479a5685`; original unchanged. Word PDF491 pages; source V4 PDF534. First491 pages have bounded native text correspondence, but physical/page raster equivalence is not established. Full application native visual audit on source pages492–534 found vector content43/43,40 pages with no native text, and BLOCK43/43. Local OCR is unavailable. DOCX has21 PBrush OLE parts (44,983,296 bytes) without semantic reading. Item13 remains OPEN.

Verified CLI defect: Cyrillic JSON failed through ASCII stdout. Proposed fix emits ASCII-escaped JSON while retaining UTF-8 report files and current gates; Windows workflow run171 SUCCESS, including the legacy stdout CLI regression; Core Tests run969 SUCCESS; Security Guard run694 SUCCESS. CodeQL and all seven GitHub checks for the current head also succeeded. Local full suite remains 1058 tests/0 assertion failures/13 Windows environment errors/49 skips; do not call the local full suite green. LIRA/SCAD calculations remain deferred.

Next: bind the 43 source graphic sheets to DOCX package objects and page placement, provide local OCR for the full vector corpus with source-bound visual review, finish font/layout and B3 coverage. Do not infer unread values from captions/index or close №13 without evidence.

## Дополнение — полный OCR-кандидат и OLE previews, 13.10.2026

В продолжение §149: исходный PDF SHA проверен; все 43 листа 492–534 обработаны локальным Tesseract 5.5.3 (rus+eng, OEM 1, PSM 11, 300 dpi). Получено 19,644 слов-кандидатов и TSV; weighted mean confidence 71.35, 29.12% ниже 60. Все 21 PBrush OLE relationship сопоставлены с 20 уникальными fallback PNG и paragraph indices; OCR previews дал 616 кандидатов, mean confidence 61.82. Это технический поиск текста, не полная/точная вычитка: labels, dimensions, orientation, omissions и native OLE payloads не верифицированы. 43 PDF vector pages остаются BLOCK в приложении. Источники неизменны; private manifests/TSV остаются в stage13-qa. QA report and plan updated in draft PR145; item13 OPEN. Следующий шаг — page-bound OLE mapping и ручная source-bound validation OCR по каждому листу, затем B2 layout/fonts и B3 corpus coverage. ЛИРА/SCAD отложены.

## Дополнение — фактические профили OCR приложения, 13.10.2026

Продолжение §150: штатный TesseractOCR приложения обработал все43 source PDF листа двумя конфигурациями. Default whole: 11,993 слова/2,530 блоков, mean line confidence43.38,58.22% строк ниже50. Regions: 30,607 слов/7,235 блоков, mean47.79,52.07% ниже50; 5/5 региональных проходов выполнены, но кандидаты перекрытий не слиты. В обоих режимах все43 страницы остаются BLOCK из-за low confidence, а vector-content guard также остаётся активным. Другой полный PSM11 профиль300dpi дал19,644 слова и weighted confidence71.35, но не верифицирован по исходнику. Режимы не являются взаимозаменяемым доказательством полноты.

Все21 PBrush OLE relationship увязаны с20 fallback previews и paragraph indices; native payload/page placement не завершены. Источники DOCX/PDF не менялись. Draft PR145 QA report/plan обновлены; head a7bd87ac8fa20d475b30817e02479e2d76d4756a, новые workflows проверяются. №13 OPEN: далее улучшаем/валидируем OCR по каждому листу, затем native OLE и физическую пагинацию, fonts/layout, B3 corpus. ЛИРА/SCAD отложены.

## Дополнение — source packet mapping all43 V4 appendix sheets, 13.10.2026

Two original Drive PDFs were fetched read-only and SHA-verified: graphics packet 10,793,106 bytes (SHA-256 fc2e720d13039b5fa9628b05125e8ce3bc6ba2c8756bfcb882243a67ec69d44c) and geodesy packet 7,563,047 bytes (SHA-256 6092ab2298bf328a545379a850b0a740cc40f3c5592703fbf876c32f459913ce). The one-to-one mapping is graphics1–21→V4 p492–512, geodesy1–22→V4 p513–534. PyMuPDF page rectangles, native-text hashes and 72dpi pixel hashes equal43/43. This establishes page provenance/render identity at one renderer/resolution; it does not decode semantic content. Forty pages still have no native text. All43 remain BLOCK due vector/low-confidence OCR controls. PR145 head bded12a438bdffaf4d551eabb05cf8b20505738f, Security710 SUCCESS, Windows177/Core975 pending. Item13 OPEN.

## Amendment — §153 OLE mapping and current PR state, 13.10.2026

## §153 — exact OLE ShapeID binding and corrected placement counts (13.10.2026)

PR145 draft now includes the corrected QA report and plan at head 42ac6b0bd29a158912c14da9950e7e7d82ae9786; exact-head CI for this newest documentation commit is pending. The preceding documentation-only head 3e1e94ac8c62f1fc385164d98f159a3d439a957f has Core run977, Windows local runtime run179, Security Guard run716, and PR check run486 all SUCCESS. Code head 6b132093c8d4adb164ce7071275d3b6ed77b0413 passed Core run976 (1,059 tests, 7 skips, including HTTP/DOM and Chromium), Windows run178, and Security run715. The candidate branch remains at b2c29604d3a8a2a8079a670a7affca4f55b2b9c6; PR145 is open and draft.

A corrected OOXML resolver binds each OLEObject ShapeID to the VML shape with the same ID and its imagedata relationship. This avoids the ambiguous paragraph-level pairing used in an earlier diagnostic. The 21 OLE objects map to 20 distinct preview PNGs; OLEObject12 and OLEObject17 share image67.png. The application's read-only DOCX parse returns 14,689 logical units and classifies all 21 as BOUND_PACKAGE_OBJECT, with available BMP bitmaps and no activation. All 21 native Ole10Native BMP render outputs are pixel-identical to the exact ShapeID-bound OOXML preview.

Exact pixel matching against Word's 491-page PDF establishes XObject page associations for 18 object instances / 17 distinct previews. image166.png (OLEObject15), image180.png (OLEObject16), and image200.png (OLEObject20) have no exact standalone XObject match; their printed page positions remain unproven. Paragraph/page context does not count as proof. The comparison establishes bitmap/fallback equivalence only, not PBrush print-stream engineering semantics or linkage to the 43-sheet PDF appendix.

No source file changed: V4 DOCX SHA-256 remains c0ca593f4dec5c101d01282523032e05b147e9169fb043a144af5fbd479a5685; V4 PDF SHA-256 remains b5d95b660b35bfb6b2441623635cba91c235efd754bc283dfe1405f075834916. Both production OCR layouts still BLOCK all 43 vector pages on confidence; candidate OCR has not been exhaustively checked against every label, dimension, symbol, rotation, and omission. Physical Word pagination, fonts/layout, and full B3 semantic corpus remain unresolved. Item13 remains OPEN; no 100%, ACCEPTED, or closure claim.


## Amendment — §154 current visual OLE page associations, 13.10.2026

## §154 — визуальная привязка оставшихся OLE-превью к страницам Word (13.10.2026)

At PR145 head 7d7347293714c50e87fdb4106b4279e02430adbc, Security Guard run722 has succeeded; Core run979 and Windows local runtime run181 were in progress at the latest check. The preceding code head 6b132093c8d4adb164ce7071275d3b6ed77b0413 passed Core run976 (1,059 tests, 7 skips, including HTTP/DOM and Chromium), Windows run178, and Security run715. The latest merged candidate remains b2c29604d3a8a2a8079a670a7affca4f55b2b9c6; PR145 is open and draft.

Side-by-side inspection of the 596×843 rendered Word pages and the three previews lacking an exact standalone PDF image XObject establishes their page-level visual association: image166.png / OLEObject15 appears as the right-hand reinforcement detail on page74; image180.png / OLEObject16 matches the left grid/deflection diagram on page84; image200.png / OLEObject20 matches the paired braced-column diagrams with arrows and numeric annotations on page99. Combined with the 18 exact-XObject object instances, page-level association is now identified for all21 OLE objects. The three visual matches do not establish exact PDF object decomposition, image bounds or scale. They also do not establish whether any objects correspond to the 43-sheet V4 appendix.

The §153 findings remain: exact OOXML ShapeID→VML→imagedata binding for all21 objects; 20 unique fallback PNGs (OLEObject12 and OLEObject17 share image67.png); application parse classifies 21/21 as bound package objects with available BMP bitmaps and no activation; native Ole10Native BMP renders pixel-match the exact ShapeID-bound fallback preview 21/21. All43 vector appendix pages still BLOCK under both app OCR layouts. Full label/dimension/symbol/rotation/omission review, PBrush print semantics, exact visual bounds/scale, relationship to the appendix, physical pagination/fonts and B3 corpus remain open. Item13 stays OPEN; no 100%, ACCEPTED or closure claim.


## Amendment — §155 exact-head CI completion, 13.10.2026

## §155 — exact-head CI completion (13.10.2026)

At exact PR145 head 7d7347293714c50e87fdb4106b4279e02430adbc, all four checks completed successfully: ENGINEER OS Core Tests run979, Windows local runtime run181, Repository Security Guard run722, and PR check run492. The draft remains open and the base remains the merged candidate b2c29604d3a8a2a8079a670a7affca4f55b2b9c6. No merge or release acceptance is implied.


## Дополнение — OLE bounds, Word fonts и точный статус PR145, 13.10.2026

PR145 draft head `1bb9b37240dc93eccb3682e704228838909c2517`; exact-head Core/Windows/Security checks are Core run992 SUCCESS (1,060 tests, 7 skips; HTTP/DOM, Chromium and vendored PDF.js PASS); Windows run194 SUCCESS; Security Guard run746 SUCCESS. Bounds/scale for the three previously decomposed OLE rasters are measured within 0.151 pt, axis-aligned with no rotation; the source font inventory is recorded (27 names, 6,302 references, no embedded DOCX fonts, 17 exact registry-name matches, 18/27 PDF font XRefs embedded). All43 appendix pages remain OCR BLOCK. Stage13 remains OPEN; no ACCEPTED/100% claim. Merged candidate base is `b2c29604d3a8a2a8079a670a7affca4f55b2b9c6`.

Bounds audit: three previously visually associated image XObjects (Word pages74/84/99) match source VML dimensions within0.151pt; all transforms are axis-aligned/no rotation. Reproducible files are `scripts/qa/audit_stage13_ole_pdf_bounds.py` and `docs/qa/2026-10-13-stage13-ole-word-xobject-bounds.json`.

Font inventory: 27 explicit DOCX names across6,302 references; no embedded DOCX font programs; exact local Windows registry matches for17 names; Word PDF has27 font XRefs,18 with embedded subset data. A mismatch may be an unused style/fallback; it is not proof of substitution. No fonts were installed. Evidence: `scripts/qa/audit_stage13_font_inventory.py` and `docs/qa/2026-10-13-stage13-word-font-inventory.json`.

These results close only two bounded inventory subcriteria. Full font/run/layout, OLE print semantics, appendix linkage and source-bound OCR/B3 corpus remain open. User-deferred calculations stay deferred.


## §159 handoff addendum — source-bound OCR false read (13.10.2026)

A page-513 high-recall OCR candidate `54.185` (46.66 confidence) was visually checked against the hash-verified V4 source crop and is a false read of `−4.185` (lost minus plus spurious leading digit). This confirms an engineering-risk OCR failure; it remains blocked by the application’s recorded vector/low-confidence gates (43/43). QA record: PR145 `docs/qa/2026-10-13-stage13-ocr-source-bound-sample.json`. Current renderer replay (PyMuPDF 1.26.6 / MuPDF 1.26.11) matches the standalone source packet and combined PDF page at 72/150/300 dpi, but does not reproduce the prior manifest’s 300-dpi raw hash; original renderer version/options are absent. Keep this provenance discrepancy open.

Only one sample has been reviewed here. B3 corpus, all-sheet semantics, OLE/appendix link, and physical Word layout/fonts remain OPEN. Latest PR145 head `098506e6271d3070c0aa109306f5bc5400f5efe2`: Security run755 passed; Core run994 and Windows run196 pending at documentation time. No item13 closure/100%/ACCEPTED. Next: await exact-head checks; then add source-bound high-risk samples and systematic page-by-page review while preserving BLOCKs.


## §160 — page 513 numeric OCR screening (13.10.2026)

A source-bound visual contact-sheet screen covered 162 numeric OCR candidate boxes on V4 page513. Three candidate errors were confirmed: `54.185` (46.66 confidence; bbox `[5538,491,76,34]`) for printed `−4.185`; `202` (93.87; `[5909,503,44,23]`) as a fragment of `−4.202`; and `4.19` (91.0; `[5986,510,46,22]`) for printed `−4.197`. The two high-confidence fragments lose the sign/prefix; one is also truncated. Reproduction evidence: PR145 `docs/qa/2026-10-13-stage13-ocr-source-bound-sample.json`; local 162-candidate contact sheets are in private `stage13-qa/ocr-full-v4-p492-p534/page-513-numeric-review/`.

This is a numeric screen on one sheet, not full page transcription or qualification; all42 other appendix sheets and nonnumeric page content remain unreviewed. The product continues to BLOCK all43 vector appendix pages. Current PyMuPDF 1.26.6/MuPDF1.26.11 source/combined-page renders match each other, while the old 300-dpi manifest hash still differs because its renderer options/version were not recorded. Item13 remains OPEN. At PR145 exact head `101f8cbcca413689bb8de9808a9ce5eb5eb4eafe`, Security run770 passed; Core run997 and Windows run199 are pending.

## §161 — exact-head PR145 validation and current blockers (13.10.2026)

PR145 remains a draft on exact head `101f8cbcca413689bb8de9808a9ce5eb5eb4eafe`, based on merged candidate `b2c29604d3a8a2a8079a670a7affca4f55b2b9c6`. Fresh GitHub Actions results for that exact SHA: Core run997 SUCCESS, 1,060 tests with 7 skips; HTTP/DOM workflow, real Chromium workflow, and vendored PDF.js checks succeeded. Windows local runtime run199 SUCCESS, including restart/persistence, backup/lock, document CLI, offline PDF viewer, local Ollama inference, and four browser workflows. Repository Security Guard run770 SUCCESS. These are CI results and do not establish a clean physical-PC install or engineering acceptance.

The PR has a separate CodeQL inline alert #45 (`py/path-injection`) at `engineering/local_app/lock.py:52`. A read-only caller trace identifies the line as the second `Path.lstat()` used to recheck a SQLite WAL/SHM unlink race. Its callers include explicit local data-root selection, and uploaded source paths are generated UUID paths; the recovery API is loopback/token/origin guarded. This suggests a likely static-analysis false positive for the supported local folder selection, but the GitHub connector did not expose the alert's SARIF source nodes. Leave the alert unresolved until those nodes are reviewed; a passing Security Guard workflow is not evidence that the CodeQL alert is closed. No production change or dismissal was made for this alert.

The V4 page513 source-bound screen reviewed 162 numeric OCR candidate boxes and confirmed three incorrect/truncated outputs (`54.185` for `−4.185`, fragment `202` for `−4.202`, and `4.19` for `−4.197`). This remains a one-page numeric screen, not full semantic qualification. All43 vector appendix pages remain BLOCK in the app. The 300-dpi renderer hash discrepancy remains unresolved. Item13 stays OPEN; no ACCEPTED/100% claim.

Next action: finish page-by-page source-bound review for pages492–534, record missed labels and uncertain associations, and rerun the app's full acceptance corpus only after its source-ground truth is complete. Then continue physical Word/layout and B3 requirements. Keep original DOCX/PDF immutable.

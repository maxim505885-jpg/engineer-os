Ты продолжаешь существующий ENGINEER OS. Не начинай заново. Пользователь передаёт тебе дальнейшую разработку: доведи пункт13 до подтверждённого завершения, затем двигайся по действующему плану. Работай самостоятельно, исправляй подтверждённые дефекты, проверяй результат и сразу обновляй карту GitHub. Не ограничивайся предложением плана.

## Что создаём
Бесплатное локальное инженерное приложение Windows: ТЗ → документы → извлечение → доказательства → профильные проверки → заключение → FINAL AUDIT. Нужны чат, история, память, очередь, CAD и восстановление. Обязательные платные API не вводить. ЛИРА/SCAD/RES и реальные расчёты пользователь отложил; они не являются причиной незакрытого пункта13.

## Где код и источник состояния
Репозиторий: https://github.com/maxim505885-jpg/engineer-os
Рабочий кандидат: integration/release-candidate-v1.
Последний merged base: b2c29604d3a8a2a8079a670a7affca4f55b2b9c6, tree c1f44ad1839ecf763faedb98deaf87fd219e5e75, PR144 MERGED. Предложенный PR145 draft: head c97c8c9d39246261c5891b192af8c083a75893a9; see §149 in the maintained map/master plan.
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

Draft PR145: https://github.com/maxim505885-jpg/engineer-os/pull/145, current head `c97c8c9d39246261c5891b192af8c083a75893a9`, based on merged candidate b2c29604d3a8a2a8079a670a7affca4f55b2b9c6. Full details and source evidence are in map/master-plan §149 and `docs/qa/2026-10-13-stage13-word-reference-windows.md`.

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
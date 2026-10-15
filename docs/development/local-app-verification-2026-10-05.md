# Локальный сценарий — фактическая проверка 05.10.2026

Основа ветки: опубликованные интеграции 06ed75bddf6bf1849e58d48ae03b9f6ec4240763 (201 Python-тест). Эта ветка не включает неопубликованные PDF-исправления e649885/13200ab.

- 228 Python-тестов, 4 Node-теста: PASS.
- Python compileall, JavaScript syntax, git diff --check: PASS.
- Реальный loopback HTTP и SQLite: загрузка оригинала → очередь → ответ синтетического сервиса → история → повторное открытие базы: PASS.
- Отдельный DOM integration (jsdom, не настоящий браузер): запуск Python CLI, работа worker, событие upload, выбранный текст в запросе модели, ответ, инертный script-текст, повторная загрузка истории и переключение диалогов: PASS. Найдена и исправлена блокировка навигации после отправки; регрессия сначала FAIL, после исправления PASS.
- Реальный исходник V4, 74,522,583 байта: оригинал сохранён, SHA256 совпал с b5d95b660b35bfb6b2441623635cba91c235efd754bc283dfe1405f075834916. Текст-кандидат только первых 20/534 страниц, text_truncated=true, UNVERIFIED, acceptance=false. Это не повторная проверка PDF и не снятие его инженерного BLOCK.
- Default Ollama 127.0.0.1:11434 в этой среде: недоступна. Реальное qwen3 inference и Windows launcher: NOT_RUN. Наличие qwen3 на Windows пользователя известно из предыдущей работы, но сегодня не проверено.
- Визуальная проверка Chromium: NOT_RUN. Playwright не нашёл browser binary; загрузка Chromium не удалась. Cloud Browser отклонил loopback URL (ERR_BLOCKED_BY_CLIENT). DOM-проверка не заменяет проверку layout/CSP в настоящем браузере.

Ограничения: кабинет пока не соединён с доказательным ENGINEER CORE, Drive OAuth, OCR/Docling, подтверждённой инженерной памятью, CAD или solver-run. Результат модели сохраняется как непроверенный контекст. История на диске — уже работающая часть сценария; принятого инженерного заключения этот кабинет не выдаёт.

Независимое ревью всей ветки выявило три Important/P2: неканонический HTTP target обходил токен, числовой PDF-текст отбрасывался, 201-е вложение исчезало из UI. Все три воспроизведены регрессионными тестами (FAIL), исправлены одним проходом; полный набор 228 Python + 4 Node и DOM smoke после исправлений PASS. Нестандартный request target отклоняется до маршрутизации; лимит 200 вложений проверяется атомарно, непринятая загрузка удаляется с диска; числовой текст сохраняется как UNVERIFIED. Socket timeout не обещает жёсткий общий срок inference.

## Дополнение 06.10.2026 — локальная подготовка CORE

232 Python + 4 Node PASS; DOM smoke дополнительно проверяет explicit CORE_PLAN, отсутствие model request, показ плана и восстановление после повторного открытия диалога. Тест миграции старой SQLite-базы сохраняет незавершённый CHAT. API проверен настоящим loopback HTTP. Независимое ревью: некорректный mode []/{} давал 500, воспроизведён FAIL и исправлен на 400; повторный полный набор PASS.

Работает EngineerCore.plan, не исполнение специалистов. Источники UNVERIFIED_SOURCE, evidence_ids=[], FINAL AUDIT NOT_RUN, acceptance=false. План доступен без модели. Настоящий браузер снова вернул ERR_BLOCKED_BY_CLIENT для 127.0.0.1:8765; layout/CSP NOT_RUN. Windows и настоящая qwen3 по указанию пользователя проверяются последними.

## Дополнение 06.10.2026 — локальные кандидаты доказательств

238 Python +4 Node PASS; compileall/JS syntax/diff PASS. Новые проверки: сохранение/повторное открытие, ложная цитата, чужой источник, изменение оригинала, точная PDF-страница 21 вне ограниченного preview, недоступный parser, защищённый token API и игнорирование присланного acceptance=true. DOM smoke дополнен созданием кандидата, инертным markup, reload и изоляцией черновика. Все новые функции сначала воспроизведены FAIL.

Независимое ревью воспроизвело сохранение черновика при смене диалога; очищаются quote/statement/page, регрессия FAIL→PASS. Остальных Critical/Important нет; reviewer отдельно проверил 15 evidence/API тестов и DOM. MATCH не утверждает правдивость факта, UNVERIFIED/NOT_CHECKED не поступают в принятую evidence базу. PDF полнота и прежние 11 BLOCK не перепроверялись; Windows/live inference/visual browser остаются NOT_RUN.

## Дополнение 06.10.2026 — происхождение и координаты native PDF цитаты

245 Python +4 Node PASS; DOM smoke и compileall/JS syntax/diff PASS. Проверены одиночная цитата, повторы, многострочный фрагмент, TXT без PDF-координат, page_rotation=90 и восстановление геометрии. Четыре начальные geometry теста сначала FAIL, затем реализация.

Независимое ревью выявило ложное UNIQUE для abcABC/abc (один объединённый bbox case-insensitive поиска) и ababa/aba (перекрытие). Обе регрессии сначала FAIL; теперь учитываются перекрытия и требуется точное равенство native get_textbox найденной области и quote; оба случая AMBIGUOUS и source-binding BLOCK. Остальные Critical/Important не найдены.

UNIQUE вызывает существующие DI evidence_candidates и validate_evidence_candidate на частичном native-quote документе; VALIDATED относится только к source binding. Полнота документа, смысл, классы данных и принятие остаются непроверенными; UNVERIFIED/acceptance=false/FINAL AUDIT NOT_RUN. OCR и ручное подтверждение geometry не выполнены; Windows/live model/real browser по-прежнему NOT_RUN. PDF V4 не перепроверялся.

## Дополнение 06.10.2026 — PNG страницы с подсветкой

251 Python +4 Node PASS; expanded DOM smoke и compileall/JS syntax/diff PASS. Четыре начальных preview теста сначала FAIL; после реализации проверены исходные байты/SHA256, PNG bounds, red-pixel location для rotation90, чужой диалог/изменённый исходник, TXT/повреждённый PDF. Реальный HTTP проверяет token, image/png, nosniff/no-store, чужой session и 429 при занятых двух renderer slots. DOM отсутствующий viewer сначала FAIL, после реализации PNG fetch/data URL/source caption/смена диалога PASS. Это не визуальная проверка браузера.

Независимое ревью нашло исчезновение рамки при offset CropBox + rotation90/180/270. Три subtests сначала FAIL; временно обнуляется rotation в копии PDF при рисовании unrotated geometry, затем восстанавливается перед get_pixmap. Pixel position/original-byte регрессия PASS во всех трёх ориентациях; полный набор PASS. Других Critical/Important нет. PDF parsing complexity не ограничена лимитом PNG, жесткий total deadline не заявляется.

Просмотр не подтверждает содержание и не меняет UNVERIFIED/acceptance=false/FINAL AUDIT NOT_RUN. Исходный V4 не перепроверялся; 11 BLOCK неизменны. Windows/live qwen3/real-browser layout по-прежнему NOT_RUN.

## Дополнение 06.10.2026 — журнал source review и контекст CORE

258 Python +4 Node PASS; compileall/JS syntax/diff PASS; DOM smoke дополнен сохранением решения, инертным замечанием, сохранностью черновика при poll и очисткой при смене диалога. Первые пять journal тестов сначала FAIL; changed-source CORE план отдельно FAIL→FAILED-job после rehash. Missing persistent review-form DOM сначала FAIL, после UI PASS.

Проверяются неизменяемая история/повторное открытие, revision conflict, invalid/empty fields, чужой session/изменённый original, запрет подтверждения unchecked PDF, source-only CORE context. HTTP проверяет token, 409 при stale revision, игнорирование acceptance/actor_verified из body. Независимое ревью: 18 review/HTTP тестов PASS; 8 одновременных revision0 запросов сохранили ровно1 event, остальные7 ReviewConflict. Critical/Important не найдено.

Это SOURCE_REVIEW_ONLY с подписью, указанной пользователем. Инженерное содержание, классы данных, полнота, нормы и расчёты не приняты; UNVERIFIED/acceptance=false/FINAL AUDIT NOT_RUN сохраняются. CORE делает versioned snapshot решения по выбранным файлам, до100 кандидатов с explicit truncation; специалистов не исполняет. Windows/live qwen3/realbrowser остаются NOT_RUN, PDF V4 не перепроверялся.


## 06.10.2026 — предварительное исполнение профильных ролей CORE

CORE_RUN связан с LocalModel/worker/SQLite/UI. Выбранные роли выполняются последовательно, затем preliminary audit. Размер/SHA выбранных оригиналов проверяются до и после каждого вызова; изменения фатальны. Per-role checkpoints сохраняют результаты при сбое/прерывании. Strict JSON разрешает только UNCERTAINTY/BLOCK, известные source IDs и ограниченные поля; принимающие статусы и proof grants не допускаются. source context/review events и усечение записываются; ошибки инструкции/модели/формата видны последующим ролям.

**280 Python PASS, 4 Node PASS, expanded HTTP/DOM PASS**, compileall/JS syntax/diff-check PASS. Добавлены 9 CORE_RUN регрессий и actual loopback HTTP тест. До реализации CORE_RUN все 8 первоначальных регрессий отклонялись отсутствующим режимом; DOM показал missing mode. После реализации последовательность/ТЗ/история, ошибочное acceptance, чужие ссылки, сбои, изменение оригинала до/во время вызова, прерывание и бюджет контекста PASS. Независимое ревью выявило необработанное отсутствие skill; новый тест сначала FAIL (1 вместо 2 model calls), после исправления role ERROR сохранён и audit продолжился. Повторное ревью: оставшихся actionable findings нет, все 9 целевых тестов PASS.

DOM запускает настоящий launcher/worker и синтетический model protocol: 4 requests всего (1 чат +3 роли); проверяет выбор режима/ролей, инертную разметку, историю после reload. Это jsdom, не настоящий rendering/CSP. В draft results evidence_ids=[], PRELIMINARY_ANALYSIS, acceptance=false; формальный FINAL AUDIT NOT_RUN. SUCCEEDED относится к сохранению результата обработки и не скрывает core_run.status ERROR/BLOCK.

Live Ollama/qwen3, Windows и принятый инженерный кейс NOT_RUN; Windows/live model последние по указанию пользователя. PDF V4 не менялся и не перепроверялся: прежний 523 UNCERTAINTY /11 BLOCK сохраняется.

## Дополнение 06.10.2026 — локальный импорт Drive

291 Python +4 Node PASS; compileall/JS syntax/git diff --check PASS. Actual HTTP route использует существующий GoogleDriveClient с синтетическим transport: token protection, session isolation, upload saturation, сохранение оригинала, MD5/recomputed SHA256/expected SHA256, source change, запрещённые форматы и отсутствие OAuth без фиктивного успеха. Импортёр имеет 9 тестов, HTTP добавлено 2. SQLite migration сохраняет старые файлы; происхождение восстанавливается после открытия базы.

Независимое ревью нашло сохранение файла до успешного cleanup и coercion строковых прав через bool(). Обе проблемы воспроизведены RED→GREEN: регистрация перенесена после TemporaryDirectory cleanup, metadata требует явные boolean canDownload/trashed. Ошибки не раскрывают private exception/token.

Два DOM smoke PASS: общий launcher/worker с 4 synthetic model requests и отдельный Drive submit с actual local HTTP/synthetic Google opener. Проверены configured-not-connected, selected original, provenance reload, отсутствие токена, смена диалога/очистка draft и failed checksum без ложного файла. Test transport существует только в тестах. jsdom не подтверждает rendering/CSP настоящего браузера.

Live Google OAuth/Drive NOT_RUN; интерактивное подключение аккаунта не реализовано. Windows/live qwen3/real browser NOT_RUN, Windows последними. UNVERIFIED/NOT_EVIDENCE/acceptance=false, FINAL AUDIT NOT_RUN. PDF V4 не перепроверялся и старые неопубликованные PDF-изменения не включены.

## Дополнение 06.10.2026 — покрытие извлечения

301 Python +4 Node PASS; два actual HTTP/jsdom сценария, compileall/JS syntax/diff-check PASS. Добавлены 10 coverage tests: mixed 23-page PDF с 20 попытками/пропущенным native-текстом, char limit на первой странице, readable/empty/whitespace PDF, повреждённый PDF/UTF8, legacy SQLite migration и restart, CORE_PLAN/CORE_RUN metadata и CHAT actual context cut. Первоначальные 9 тестов RED по отсутствующему покрытию, затем GREEN. HTTP upload assertions проверяют JSON coverage, DOM впервые RED по отсутствующей карточке, после UI GREEN.

Независимое ревью нашло CHAT prompt без фактического context_text_truncated и whitespace page count, оставшийся ненулевым после discard. Оба воспроизведены RED→GREEN. Повторное ревью: Critical/Important нет, 10 tests PASS; отдельные one-file/twenty-file CHAT repro остались в 16k.

RECORDED — наблюдаемое покрытие preview, не подтверждение полноты. UNKNOWN для прежних файлов/ошибок; NOT_CHECKED/NOT_RUN/UNVERIFIED/acceptance=false сохраняются. PDF V4 не перепроверялся, старые неопубликованные PDF-правки не включены. Полный Docling/OCR, live Google/qwen3, real browser/CSP и Windows NOT_RUN; Windows последними.

## Дополнение 06.10.2026 — фоновое постраничное извлечение PDF

313 Python +4 Node PASS; оба actual HTTP/jsdom smoke, compileall/JS syntax/diff-check PASS. 11 extraction regressions и новый protected HTTP workflow. Первоначальные 8 extractor tests RED по отсутствию очереди; API RED404 и DOM RED missing action, после реализации GREEN. Real native 23-page PDF обработан за пределами preview20, page23 без текста BLOCK; исходные байты/hash не меняются, сохраняются journal/checkpoint/restart/resume.

Проверены changed source до регистрации страницы, foreign job/file isolation, partial page/aggregate budget/resume protection, missing Docling explicit FAILED, existing adapter page_range с synthetic converter и source provenance. Converter reuse regression uncached RED2 loads→cached GREEN1. Независимое ревью выявило OCR history reset on resume: существующий adapter/synthetic failure воспроизвёл RED NOT_RUN, исправление сохраняет REQUESTED_NOT_VERIFIED до вызова и в durable page record; GREEN11 tests, весь набор313PASS. Других blocking findings reviewer не обнаружил.

DOM запускает actual launcher/worker, native queue/journal/saved text; модельных запросов при извлечении нет (4 прежних chat/CORE calls). Другая Drive integration также PASS. Журнал хранит summaries отдельно от page blocks; JSON paths/exception secrets не публикуются.

Docling/onnxruntime/OCR здесь отсутствуют, live Docling/OCR NOT_RUN; контракт synthetic не подтверждает распознавание, качество таблиц, offline weights или производительность. Новый результат не заменяет автоматически CORE preview. UNVERIFIED/NOT_EVIDENCE/NOT_CHECKED/acceptance=false/FINAL AUDIT NOT_RUN сохранены. PDF V4 не перепроверялся; Windows/live qwen3/Google OAuth/real browser NOT_RUN, Windows последними.

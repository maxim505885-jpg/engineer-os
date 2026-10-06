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

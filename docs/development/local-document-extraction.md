# Фоновое постраничное извлечение PDF

В карточке PDF есть два явных действия: «Все страницы · native без OCR» и
«Docling · OCR и таблицы». Задача использует существующую очередь/worker,
работает без модели и сохраняет промежуточные результаты. Это обработка страниц,
не подтверждение полноты инженерного документа.

## Режимы и зависимости

Native использует PyMuPDF, читает текст каждой страницы, сохраняет page number.
BBox не выдумывается; пустой native-текст — BLOCK/NO_NATIVE_TEXT. Это может быть
пустая страница, растр или недоступное содержание. Таблицы/графика/OCR не проверены.

Docling использует существующий DoclingDocumentParser с отдельным (n,n) page_range,
сохраняет нормализованные blocks/provenance/table rows. Прежние table-loss guards
не ослаблены. Нужны установленный optional Docling/OCR runtime,
ENGINEER_OS_DOCUMENT_INTELLIGENCE=true и локальный ENGINEER_OS_DOCLING_ARTIFACTS_PATH.
Converter создаётся один раз на задачу. Ошибка конфигурации/инициализации даёт
видимый FAILED без native fallback. Приложение не устанавливает зависимости и
не запускает download command; completeness локальных весов и offline поведение
самого runtime здесь ещё не подтверждены. Prefetched weights передаются через
artifacts_path согласно [официальной документации](https://docling-project.github.io/docling/usage/advanced_options/).

REQUESTED_NOT_VERIFIED означает, что parser с OCR был запрошен; не доказывает,
что OCR реально сработал или правильно распознал страницу. Признак ставится
перед вызовом, хранится в странице и сохраняется при resume/ошибках.

## Сохранение и продолжение

jobs EXTRACT_NATIVE/EXTRACT_DOCLING содержат компактный extraction checkpoint:
file ID/hash/backend, total/processed/failed/blocked pages, stored chars, текущую
страницу и ограничения. SQLite extraction_pages хранит отдельные page records
с execution COMPLETED/FAILED, status UNCERTAINTY/BLOCK, blocks, errors и truncation.
Processed pages — зарегистрированные попытки, включая FAILED, не подтверждённые
страницы. SUCCEEDED означает законченный цикл, который может содержать ошибки.

Hash оригинала проверяется до/после страницы и перед resume. Изменённый источник
останавливает задачу до регистрации текущего ответа. Прежние records сохраняются.
Успешно сохранённые COMPLETED страницы пропускаются при продолжении; FAILED
повторяются. Пустой или усечённый COMPLETED/BLOCK не переписывается автоматически.
Можно начать отдельную задачу другим backend. При shutdown/restart RUNNING
прерывается; replay только вручную. Остановить текущий parser посередине вызова
этот маршрут не умеет; checkpoint появляется после страницы.

«Продолжить извлечение» доступно для FAILED или завершённого цикла с failed pages.
Другой активный job в диалоге не позволяет resume. Законченный без ошибок цикл и
исчерпанный бюджет не возобновляются. Ещё раз нажать запуск — отдельная задача.

Ограничения: до 5000 PDF-страниц, 20000 сохранённых text chars/1000 блоков на
страницу, до 2000000 text chars на задачу. Усечение — BLOCK/TEXT_LIMIT; общий
бюджет останавливает следующие страницы, resume не обходит лимит. Эти пределы
ограничивают retained text, не сложность PDF decoding или время parser. Геометрия
и metadata нормализованного adapter сохраняются отдельно от текста.

## Защищённые API и кабинет

- POST /api/sessions/:id/extraction — file_id и backend native/docling.
- POST /api/sessions/:id/jobs/:job/resume — явное продолжение.
- GET /api/sessions/:id/jobs/:job/pages?offset=0&limit=50 — summaries до 50 записей.
- GET /api/sessions/:id/jobs/:job/pages/:page — сохранённые blocks выбранной страницы.

Все API требуют существующий loopback/token/Origin контракт и принадлежность
job/источника диалогу. Публичный journal не содержит private source paths. UI
показывает progress/counts/errors, страничный журнал и инертный текст без markup
execution. Тексты не помещаются целиком в conversation snapshot.

UNVERIFIED_EXTRACTION/NOT_EVIDENCE, completeness NOT_CHECKED, acceptance=false,
FINAL AUDIT NOT_RUN. Новый результат не заменяет автоматически старый preview
или контекст CORE: подключение выбранных извлечённых страниц к анализу — отдельный
следующий этап, с сохранением границ и усечения.

## Фактическая проверка

Real native 23-page PDF, пустая страница, original bytes/hash, checkpoints,
stop/restart/resume, ошибки parser, changed source, isolation, clipping/budget,
missing Docling, cached converter и OCR history проверены регрессиями. Docling
contract использует существующий adapter и synthetic converter, не настоящий OCR.
Actual HTTP проверяет token/isolation/pagination, jsdom — запуск native, journal
и сохранённый текст; модельных запросов при извлечении нет.

В этом окружении Docling/onnxruntime/OCR не установлены: live Docling/OCR NOT_RUN.
Windows/qwen3/Google OAuth/real-browser layout/CSP также NOT_RUN. PDF V4 не
перепроверялся; его прежний инженерный BLOCK не снят.

# Покрытие извлечения в локальном кабинете

Карточка оригинала и материал CORE_PLAN раскрывают наблюдаемое покрытие preview.
Та же сводка передаётся в CHAT/CORE_RUN. Цель — не давать частичному тексту
выглядеть прочитанным целиком документом. Оригиналы и их SHA256 не меняются.

## Что сохраняется

`files.extraction_coverage` — отдельный JSON, независимый от Drive provenance.
SQLite мигрирует прежние базы. Для прежней записи без покрытия возвращается
UNKNOWN/LEGACY_UNKNOWN: количество страниц не вычисляется задним числом.

Для PDF сохраняются total_pages, фактический attempted_pages, pages_with_text,
pages_without_text (номера только обработанных страниц), unattempted_pages и
до 20 page_records. В записи страницы — исходные/сохранённые native символы,
TEXT / PARTIAL_TEXT / NO_NATIVE_TEXT. Последнее означает, что get_text не дал
значимого текста; страница может быть пустой, содержать растровую графику или
недоступное текстовое содержание. Это не доказательство отсутствия содержания.

Preview по-прежнему ограничен первыми 20 страницами и 100000 символами вместе
с маркерами страниц. Причины остановки PAGE_LIMIT/CHAR_LIMIT и фактическое число
попыток раскрываются. Если лимит достигнут на первой странице, нельзя писать,
что прочитаны 20. Page stored_chars учитывает native символы без маркеров;
верхний stored_chars — длину фактически сохранённого preview с маркерами.
Полностью отброшенный whitespace preview имеет нулевые сохранённые счётчики.

Для TXT/MD method=UTF8, source_chars/stored_chars в символах после UTF-8-sig
декодирования, а PDF page counts неприменимы (null). Повреждённый PDF, ошибка
parser/декодирования или недоступный parser дают UNKNOWN/EXTRACTION_UNAVAILABLE,
сохраняя оригинал. Ошибки извлечения не подменяются фиктивным OCR.

Во всех случаях scope TEXT_PREVIEW_ONLY, completeness NOT_CHECKED, ocr NOT_RUN.
Статус RECORDED означает сохранённые счётчики, а не проверенную полноту.
Таблицы/графика/смысл/координаты фактов не проверяются этим preview. Кандидаты
остаются UNVERIFIED/NOT_EVIDENCE, acceptance=false, FINAL AUDIT NOT_RUN.

## Модель и история

CHAT сохраняет source_coverage в результате и передаёт её в user message как
непроверенные данные. Для каждого выбранного источника указаны фактические
context_text_chars/context_text_truncated. Вложения вместе с coverage/wrapper
ограничены 16000 символами; metadata резервируется до slicing, затем сообщение
собирается с фактическими счётчиками. История имеет отдельный прежний бюджет.

CORE_RUN передаёт компактную сводку без per-page records; текст имеет прежние
4000 на файл/12000 суммарно, actual context counts раскрываются отдельно.
CORE_PLAN сохраняет coverage snapshot материалов. UNKNOWN, пропущенный native
текст или stop reason помечают context_truncated даже без общего усечения строк.
Полностью представленный текст по-прежнему не подтверждает документ в целом.

## Проверка и следующий шаг

10 регрессий проверяют mixed 23-page PDF/20-page limit, остановку на первой
странице по char limit, readable native PDF без ложного acceptance, пустые и
whitespace страницы, повреждённые исходники, UTF8, legacy migration/restart,
CORE context и CHAT cut disclosure. Все первоначальные 9 тестов наблюдались RED;
review regressions также RED→GREEN. Actual HTTP показывает coverage в upload
response; jsdom проверяет карточки UTF8/PDF и прежние сценарии.

Полное извлечение Docling/OCR и подтверждение полноты сюда не добавлены.
Следующий этап — подключение существующего DI/Docling к фоновой обработке
документа с журналом страниц и явными недоступными областями. Live Google/model,
Windows и настоящий браузер layout/CSP пока NOT_RUN; Windows последними.

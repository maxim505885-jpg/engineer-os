# Проверка восстановленной таблицы PDF

`scripts/verify_pdf_recovery.py` перечитывает объявленные фрагменты таблицы из
исходного PDF. Это локальная проверка привязки текста, а не автоматическое
восстановление произвольных таблиц и не запись в Evidence Register.

Нужен существующий изолированный Python проекта. Дополнительная бесплатная
зависимость устанавливается только в это окружение:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-pdf-review.txt
.\.venv\Scripts\python.exe scripts\verify_pdf_recovery.py .\.engineer-os\v4-drive-source.pdf recovery-source-manifest.json --output recovery-source-verification.json
```

Не создавать глобальную установку Python ради этой команды. В текущей Linux
проверке использовался уже доступный PyMuPDF 1.26.6. Текстовый reader можно
внедрять в функцию `verify()`; её тесты не требуют PyMuPDF.

Карта содержит SHA256 исходного PDF, объявление проверки (`reviewer`, время с
часовым поясом, область проверки), непустые контексты заголовка/разделов и строки.
Каждая строка имеет уникальный `candidate_id`, список одной или двух соседних
страниц, ссылку на заголовок/раздел и ровно шесть столбцов. Ячейка содержит текст
и отдельные `source_fragments` со страницей, SHA256, TOPLEFT bbox и исходным текстом.
Пустые ячейки сохраняются. Фрагменты двух страниц не заменяются одной ссылкой.

Проверяются оригинальный файл, тип PDF, страницы, конечные координаты, текст,
общая полоса строки, смежность столбцов и совпадение столбцов между страницами.
Склейка использует только записанные фрагменты и нормализацию пробелов, без
исправления обозначений или чисел. Выходной файл не может заменить входной PDF
или карту, включая жёсткие ссылки. Повреждённый файл получает отчёт BLOCK.

PASS относится только к проверке привязки текста. Выход всегда сохраняет
`document_status=BLOCK`, `evidentiary_status=NOT_EVIDENCE`, `acceptance_granted=false`.
Нативный текстовый слой не доказывает отсутствие содержимого в графике/сканах,
полноту документа или правильность инженерного толкования. Контексты и связи
строк объявлены проверяющим, не обнаруживаются автоматически. Этот режим не
вызывается из production evidence pipeline и не является fallback внутри Docling.

Проверка V4 на страницах 396–404: 91 строка, 546 логических ячеек, 570 исходных
фрагментов; все привязки совпали с исходным PDF. Карта и результат сохранены в
приватных материалах проверки. Это позволяет воспроизводить извлечение этой
таблицы, сохраняя блокировку инженерного принятия и всего документа.

## Экспорт кандидатов в формат ENGINEER OS

Опциональный `--candidate-output` повторно проверяет исходный PDF и выдаёт
`blocks` с существующей структурой `block_id/kind/text/provenance`. Для каждого
столбца сохраняется отдельный `table_cell`, включая пустые ячейки и обе страницы
разорванной строки. Заголовки/разделы остаются `table_context`; исходные `rows`,
`context_fragments` и объявление review также сохраняются без изменения.

```powershell
.\.venv\Scripts\python.exe scripts\verify_pdf_recovery.py .\.engineer-os\v4-drive-source.pdf recovery-source-manifest.json --output recovery-source-verification.json --candidate-output recovered-table-candidates.json --project-id 2c436f43-98e4-43ad-b3b1-533c6ef4f8b2 --document-id f5e7c759-721f-48c3-8e0e-ced590eecce8
```

Экспорт имеет `parser=reviewed_pdf_regions_v1`, `status=UNCERTAINTY`,
`document_status=BLOCK`, `complete_document=false`, `acceptance_granted=false`.
Диапазон `page_start/page_end` обозначает страницы объявленных регионов, а не
проверку всего содержимого этих страниц. Верхние метаданные задают TOPLEFT и
SHA256 для всех блоков. ID проекта/документа назначает вызывающая сторона;
команда не проверяет их в БД. Оба выходных файла должны отличаться от входов и
друг друга, включая жёсткие ссылки. Неуспешная повторная проверка заменяет старый
экспорт пустым BLOCK. Ошибка аргументов не запускает проверку и не меняет файлы.

Это отдельный локальный вход для очереди review. Он не заменяет ошибки Docling
на PASS и не вызывается автоматически из batch/runtime или Evidence Register.
Для подключения к UI ещё нужен просмотр и инженерное подтверждение кандидатов.

## Использование из bounded batch

`local_docling_batch.py --reviewed-manifest recovery-source-manifest.json`
выполняет обычные Docling chunks и дополнительно запускает повторную проверку
карты. Исходные `pages-*.json` и `pages-*.audit.json` не заменяются кандидатами.
Ошибки Docling остаются BLOCK; восстановление отдельных регионов не доказывает
полноту страниц. Все body pages карты должны входить в выбранный диапазон
batch (максимум 20 страниц); header context может быть на более ранней странице.
SHA256 карты должен совпадать с `--sha256` batch.

Чтобы повторно проверить только карту без дорогого запуска Docling:

```powershell
.\.venv\Scripts\python.exe scripts\local_docling_batch.py .\.engineer-os\v4-drive-source.pdf --start 396 --end 404 --sha256 b5d95b660b35bfb6b2441623635cba91c235efd754bc283dfe1405f075834916 --project-id 2c436f43-98e4-43ad-b3b1-533c6ef4f8b2 --document-id f5e7c759-721f-48c3-8e0e-ced590eecce8 --output-dir .\.engineer-os\reviewed-regions --reviewed-manifest recovery-source-manifest.json --reviewed-only
```

Нужна optional зависимость из `requirements-pdf-review.txt` в том же окружении.
В `.venv-docling` текущего Linux checkout PyMuPDF отсутствует; контрольный
reviewed-only запуск выполнен системным Python с уже установленным PyMuPDF.
В нём не запускался Docling. На Windows наличие пакетов следует проверять.

Выход: `reviewed-regions.audit.json`, `reviewed-regions.candidates.json` и
`batch-review-summary.json`. Summary сохраняет результат Docling, заблокированные
диапазоны, результат recovery и флаги неполноты/непринятия. Reviewed-only всегда
возвращает код 2 и `docling_status=NOT_RUN`, даже при успешной привязке источника:
это сигнал незавершённого документа, а не ошибка восстановленной таблицы.
Обычный batch без новых флагов сохраняет прежнее поведение.

Этот локальный batch теперь умеет потреблять проверенную карту. Автоматическое
обнаружение новых повреждённых таблиц, UI review и runtime-подключение ещё не выполнены.

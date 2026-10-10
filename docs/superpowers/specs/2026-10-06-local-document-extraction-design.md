# Фоновое извлечение PDF

Продолжение существующего кабинета по поручению пользователя: сделать локально,
Windows последними, сохранить карту. Не менять runtime или acceptance contract.

Одна PDF-копия текущего диалога ставится в существующие jobs/Worker как
EXTRACT_NATIVE или EXTRACT_DOCLING. Native использует PyMuPDF без OCR; Docling
использует имеющийся DoclingDocumentParser с page_range=(n,n). Это два явных
режима, без скрытого fallback. Модель и платные API не вызываются.

SQLite extraction_pages хранит отдельный record на страницу (execution/status,
непроверенные blocks/text/provenance, ошибки, truncation). Job checkpoint хранит
компактные counts/current page/limitations, не все тексты. Журнал API страничный,
по 50 summaries; отдельная страница доступна с сохранёнными blocks. GUI показывает
прогресс, журнал и явное продолжение FAILED или завершённой с failed pages задачи. Уже COMPLETED страницы не
перечитываются; FAILED страницы повторяются. Перезапуск прерывает RUNNING,
сохраняет журнал, не делает автоматического replay. SHA256 проверяется до/после
каждой страницы и перед resume, чужие диалоги отклоняются.

Лимиты: 5000 страниц, 20000 символов текста/1000 блоков на страницу, 2000000
сохранённых символов на задачу. Усечение явно BLOCK, достижение общего бюджета
останавливает дальнейшие страницы. Resume не обходит бюджет. Парсер не получает
новых произвольных URL/путей или model tools. Для production Docling нужны DI
enabled, установленные dependencies и локальный artifacts directory; кабинет не запускает installer/download command. Prefetched artifacts передаются
адаптеру; фактический offline runtime ещё требует проверки весов OCR. Ошибка парсера sanitized, не раскрывает пути.
Локальный маршрут создаёт converter один раз на задачу и переиспользует его;
производительность живого Docling не обещается; in-flight parse имеет прежние ограничения остановки.

Записи UNVERIFIED/NOT_EVIDENCE/acceptance=false, completeness NOT_CHECKED,
FINAL AUDIT NOT_RUN. Native пустой текст — BLOCK/NO_NATIVE_TEXT, а не отсутствие
содержания. Docling table guards остаются прежними. SUCCEEDED означает завершение
цикла обработки, даже если отдельные страницы BLOCK/FAILED. Исходные ограниченные
preview и CORE context не заменяются автоматически новым извлечением.

Проверить реальный native PDF >20 страниц, checkpoint/resume и restart,
ошибки/изменения источника, междиалоговую изоляцию, budgets, HTTP token и DOM.
Docling contract test использует существующий adapter + synthetic converter;
live OCR/Docling/Windows отдельно NOT_RUN при отсутствии dependencies.

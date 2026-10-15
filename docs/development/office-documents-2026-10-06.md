# Пункт 4 — Подключить остальные форматы

На базе PR55 добавлены локальные DOCX/XLSX adapters и отдельная DOC→DOCX конвертация. Пользователь прикрепляет файл или импортирует оригинал Drive; существующий Worker сам читает его и передаёт части в CHAT/CORE. Дополнительные обязательные Python packages не нужны для OOXML.

DOCX: абзацы и ячейки таблиц основного текста, привязка к XML part/paragraph/table/row/column. XLSX: лист, адрес ячейки, исходная формула и сохранённое значение раздельно; вычисление формул не выполняется. Стили, даты и числа остаются raw values. Физические страницы Office неизвестны: интерфейс показывает логические элементы, page refs=None.

DOC: исходные байты сохранены, отдельная производная копия с original/derived SHA256. Linux LibreOffice с временным профилем, MacroSecurityLevel=3, запретом сетевых syscalls через seccomp, timeout90с и resource limits. Это ограничение сети/ресурсов, а не filesystem sandbox или испытание всех вредоносных документов. Координаты относятся к производному DOCX; точность конвертации не принята. Здесь испытан LibreOfficeDev26.8.0.0.alpha0. Отсутствие конвертера/ошибка дают явный отказ, без текста fallback.

Проверки: 376 Python tests, 4 Node dashboard tests, compileall, JS syntax и git diff --check PASS. Оба реальных launcher/HTTP/Worker/jsdom сценария PASS; модель и Drive transport в них контролируемые, не живые Qwen/OAuth. XLSX upload и адрес Нагрузки!C1 проверены в UI. DOCX/XLSX прошли общий Drive pipeline на controlled transport. Перезапуск сохраняет logical source refs; DOC resume проверяет cached derivative SHA вместо повторной конвертации. Изменённый parser/config/source блокирует прежнее продолжение.

Реальные пользовательские «Расчет  .doc», «Расчет  .docx», «Таблицы.xlsx» прошли production Store/Worker/DocumentModel, с настоящим parser/LibreOffice и контролируемой моделью. Прочитаны соответственно492,487,125 логических элементов, цикл завершён. Количество BLOCK и подробные ограничения записаны в docs/qa/2026-10-06-stage4-office.json. Оригиналы сверены побайтно. Полные исходники, extracted text и prompts не публикуются. Качество ответов живой модели на Office здесь не проверялось.

Один независимый review нашёл два Important; оба исправлены после воспроизведения RED→GREEN. Word специальные дефисы сохраняются; font-specific symbol не угадывается, остаётся токеном с BLOCK. Excel фонетические аннотации исключены из shared/inline значения. Minor: SHA конвертера пока относится к launcher; runtime fingerprint следует усилить перед обновлением LibreOffice или поддержкой Windows. Не обновлять runtime в ходе незавершённого анализа.

Ограничения раскрыты: drawings, Word equations, headers/footnotes, tracked changes, merged/nested tables, специальные Excel formulas, raw styles и конвертация DOC. SUCCEEDED означает завершение обработки поддержанных частей; semantic completeness NOT_CHECKED, FINAL AUDIT NOT_RUN, acceptance=false. Office evidence register пока явно отклоняет попытку использовать PDF page: соединение logical locators с source review/доказательствами — пункт5.

Пункт4 реализован как проверенный кандидат. Main/deployment не изменены; Windows остаётся последним пунктом9. Дальше: пункт5 — Связать анализ с доказательствами и ТЗ.

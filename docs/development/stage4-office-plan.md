# Пункт4 — форматы документов; план и журнал

Основание: утверждённый план06.10.2026, пункт4. BASE=a86a63f/PR55/tree97067928. Рабочая ветка feat/office-documents-stage4-20261006. Windows последней; без main merge/deploy. Сохранённый оригинал, fail-closed, acceptance=false.

1. DOCX/XLSX: bounded ZIP/XML parser без вычисления формул, внешних ссылок и макросов. DOCX main body paragraphs/table cells с XML-part/index/row/column; неизвестные физические страницы не выдумывать. XLSX sheets/cell addresses/formulas/stored caches; стили/даты показывать как непроверенные raw values. Объединения, картинки и сложные структуры раскрывать.
2. DOC: отдельная локальная LibreOffice conversion с временным profile, отключёнными макросами/сетью, timeout/лимитами; сохранить originalSHA и derivedSHA отдельно. Не выдавать координаты производного DOCX за координаты DOC. Недоступный converter/защита/пустой результат → явная ошибка.
3. Общая загрузка/Drive/automatic-analysis/CORE и durable checkpoints. Новые форматы попадают в тот же DocumentModel. Журнал использует логические units, не физические страницы; refs хранят locator/units и textSHA. PDF поведение сохраняется.
4. TDD, реальные пользовательские DOCX/XLSX/DOC, HTTP/UI, полный suite, один независимый review всей ветки, публикацияdraftPR и карта.

Pre-flight: parser identity→Store child cache→automatic batch refs должны совпадать; для Office backend определяется suffix независимо от PDF OCRsetting. Unit identity включает locator; page=None для Office. PDF counters совместимы, Office счётчики явно labeledunits. Conversioncache требуетimmutableconverter identity; изменения adapters делают старый resume непригодным.

Ruling: stdlib ZIP/XML вместо обязательных python-docx/openpyxl — снижает runtime dependencies; поддержанные содержания явно ограничены и требуют source review. Цена ошибки: сложный Office layout потребует отдельного adapter, не ложного ACCEPTED.

Статус: четыре задачи выполнены локально. DOCX/XLSX/DOC проходят upload/Drive/automatic CHAT/CORE; сохранены оригиналы, logical locators и ограничения. 376Python/4Node PASS; оба actualHTTP/jsdom сценария PASS. Реальные источники повторены после исправлений review. Публикация фиксируется в живой карте.

Review: один независимый read-only whole-branch review. Два Important воспроизведены RED→GREEN: Word noBreakHyphen/softHyphen теперь сохраняются, font-specific sym остаётся явным токеном с SYMBOL_NOT_DECODED; XLSX phonetic rPh не попадает в значение shared/inline strings. Minor отложен: converter fingerprint пока идентифицирует launcher, а не весь LibreOffice runtime. Runtime нельзя обновлять под действующим resume; усилить идентичность перед поддержкой обновлений/Windows. Это ограничение, а не подтверждение immutable runtime.

Дополнительные RED→GREEN: повторная DOC-конвертация при resume заменена проверкой cached derivative; Office evidence API запрещает подмену логического элемента PDF-страницей. npm запуск из e2e выявил относительный tests path; fixture запускается с repo cwd. Пункт5 подключит Office locators к доказательствам и ТЗ, пункт9 — Windows.

# №13 — точная геометрия native ячеек PDF, 11.10.2026

## Потеря и изменение

До изменения `pdf_table_candidates` сохранял только `table.extract()` (матрицу строк) и округлённый bbox всей таблицы. Индивидуальные прямоугольники ячеек, пустые/неопределённые slots и внешний header терялись. Следствием была невозможность адресной сверки значения с оригиналом по сохранённому payload.

Новый payload `ENGINEER_OS_PDF_TABLE_CELLS_V2` сохраняет прежнюю матрицу `values`, row/column каждого slot (1-based), точный detector bbox или null, `DETECTED_UNVERIFIED`/`UNRESOLVED_SLOT`, header geometry/names, page rotation/rect/cropbox и явный coordinate system. Null не превращается в доказанную связь объединения. Native extraction не объявляется чтением растрового содержимого. Все кандидаты остаются UNCERTAINTY; `content_verified=false`.

PyMuPDF find_tables на rotated PDF преобразовывал геометрию в display space. Reader теперь нормализует rotation только в памяти на время detection/extraction и восстанавливает его; физический source не сохраняется. Regression сопоставляет rectangle с native text clip оригинальной rotated page. SHA источника проверяется до и после extraction; изменение файла отклоняет весь результат.

Изменение формата намеренно меняет payload SHA и candidate ID. Прежние immutable candidate rows не переписываются и не считаются V2. API tuple `(DocumentAssetEvidence, bytes)` и asset kind `table_cells` сохранены. Не меняются validated-text RPC или acceptance gates.

## Реальный источник и сверка

V4 PDF найден в подключённом Drive, ID `1Ycw-dcevqNSHgvb_y0pVa7B1lM4uhK6g`, 74522583 bytes, SHA256 `b5d95b660b35bfb6b2441623635cba91c235efd754bc283dfe1405f075834916`. Оригинал после probe имеет тот же SHA.

На страницах 15–16 обнаружены три detector candidates: две рамки листов 8×10 с 51 null slot каждая и настоящая native таблица страницы 15, 8×3, 24/24 rectangles. Рамки не объявлены настоящими инженерными таблицами и не отброшены молча. Для таблицы П.2.1 все 24 cell texts после нормализации пробелов совпали с независимым `page.get_text(clip=cell_bbox)`; native значения и видимая сетка просмотрены на render всей исходной страницы. Сохранены в том числе `S₀`, `W₀`, знаки температур и строки нормативных ссылок, без проверки применимости норм или инженерных значений.

Выбранный реальный candidate успешно повторно получен через публичный backend callable `persist_selected_unverified_asset` с capture transport. Отдельный file-ledger записан с hash validation и readback. Это НЕ live Supabase HTTP/RPC и НЕ пользовательский UI/Store/model replay. Receipt: `2026-10-11-pdf-table-cell-provenance.json`.

## Проверка и предел результата

RED подтвердил потерю individual/merged rectangles; GREEN проверяет native 2×2, merged top row/null slot, rotated page source clip и изменение source во время extraction. Профильные reader/backend/entrypoint: 12 tests PASS. Полная Python regression: 910 tests / 66.196 s, OK, 17 environment skips. 10 Node tests, architecture guard, JS syntax, compile и diff checks PASS. Независимый review: Critical/Important нет; minor header coverage suggestion закрыт internal/external/null tests. CI exact-head результаты фиксируются отдельно после публикации.

Подэтап: source mapping native table-cell candidates. №13 остаётся открытым: raster/mixed cell values, OCR conflicts, графические подписи и Word/EMF layout, visual OMML fidelity, full app HTTP/UI roundtrip и qualified corpus не подтверждены. На ПК пользователя не установлено; engineering acceptance=false. Расчёты ЛИРА/RES отложены.

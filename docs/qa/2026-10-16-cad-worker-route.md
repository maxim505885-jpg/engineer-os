# T08: ограниченный DXF-маршрут — 16.10.2026

База d8e9ae5, существующая ветка codex/v1-completion-20261015. Пункт 2 остаётся
отложенным. Пользовательский dirty checkout, работающий сервер и реальные DWG
не изменялись. Разработка продолжает существующие CAD adapters и очередь.

## Реализованный участок

CAD_INVENTORY/CAD_DIFF доступны в обычной форме и существующей ENGINEERING_RUN
очереди. Они принимают только текущие DXF оригиналы того же проекта с точными
file IDs/SHA/revision и пустыми options. Входные декларации PROJECT, автоматического
Evidence или acceptance нет. DWG_CONVERT и CAD_ANNOTATE в очередь не включены.

Новый cad_process создаёт собственные снимки после ограниченного хеширования,
использует существующий calculation_process и повторяет source/snapshot checks.
Граница: 2GiB памяти,30s,2MiB JSON,один CAD child одновременно. Это ограничение
ресурсов, не доказанный network/filesystem sandbox. Прежний DXF inventory API
делегирует этому worker; native annotation/export/locator остаются прежними.

Сохранены бюджеты20MiB/50000 inventory entities и отдельный10000 edit limit.
Показ первых100 объектов Model не выдаётся за полный список всех блоков.
При срабатывании лимита нет заявления inventory_read_complete. Сравнение —
строгие сериализованные DXF данные, не визуальная или DWG эквивалентность.

Отдельно воспроизведён и устранён приёмный read race: после stat файл мог вырасти,
а read_bytes не проверял новую длину. Теперь чтение ограничено MAX_BYTES+1 и
длина проверяется повторно; исходники не исправляются и не пересохраняются.

## Проверки и review

RED: отсутствующий CAD worker/очередь, отсутствующие UI options и рост файла
после stat. GREEN:58 focused tests (CAD worker/API/roundtrip/conversion/queue,
IFC jobs и resource limits). Проверены staged copy вместо оригинального пути,
change-during-child, identity/count/cancel negatives, output cap, неполный census
и обе CAD-задачи через Worker без автоматического Evidence.

Chromium CAD: инвентаризация, изменение линии по handle, сравнение двух разных
исходников,PROJECT/no acceptance,desktop/mobile без переполнения,очистка проекта
PASS. Скриншоты просмотрены. Повторные существующие Chromium сценарии IFC
inventory/geometry/requirements/diff/GUID,rectangle/beam/planar actual child и
CAD inventory→annotation→download→project isolation PASS.

Независимое review важных actionable дефектов не выявило. Его тестовый запуск
ограничен sandbox PermissionError и не считается независимым PASS. Замеченная
неоднозначность подписи total устранена: UI пишет «Всего объектов DXF» вместо
«Объектов модели». UI detector для изменённого JS не сообщил предупреждений.

CAD requirements теперь включают общий process-adapter. Offline pip dry-run
подтвердил установленные ezdxf1.4.4/pywin32 312; пакеты не устанавливались.
Optional CI добавляет CAD requirements/test и браузерный сценарий; это настройка,
а не receipt уже исполненного CI.

Полная Windows-регрессия: **1308 tests,389.460s,34skipped,OK,exit0**.
В журнале есть diagnostic ConnectionAbortedError HTTP-сервера при закрытии
соединения; unittest не зарегистрировал failures/errors. Source/PDF/BLOCK
сообщения отрицательных fixtures не являются приёмкой документов.
Architecture/repository guards,JavaScript syntax и diff check PASS.

## Остаток T08

Реальные DWG, независимый native census, полные геометрические проверки,
large-file путь, квалификация преобразования и остальных native операций
остаются OPEN. Прежние ODA/AutoCAD ошибки и лимиты сохранены; новые результаты
на синтетических DXF их не закрывают. Пункт 4 целиком и выпуск не объявлены готовыми.

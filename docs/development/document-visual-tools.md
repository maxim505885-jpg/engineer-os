# Локальные инструменты визуальной проверки документов

## Границы

Это дополнение к T03/T04 и `document-qualification.md`. Пользователь разрешил внедрение связки Gotenberg → существующий Docling → diff-pdf; PaddleOCR используется как независимый кандидат для спорных областей. Инструменты не выдают ACCEPTED/FINAL_AUDIT. Локальная установка, запуск адаптера, визуальное совпадение и инженерная приёмка — разные проверки.

## Визуальное сравнение PDF

`scripts/compare_document_visuals.py` запускает явно выбранный diff-pdf на приватных копиях двух PDF. SHA исходника, эталона, executable и адаптера сохраняются в новом каталоге; до выдачи квитанции проверяется неизменность входов, копий и executable. Существующий output не перезаписывается. Symlink/junction пути, не-PDF и входы свыше256MiB отклоняются. Timeout1..1200s, по умолчанию180s.

```powershell
.venv-engineering/Scripts/python.exe scripts/compare_document_visuals.py --source SOURCE.pdf --reference REFERENCE.pdf --output NEW-DIRECTORY --executable PATH-TO-diff-pdf.exe
```

Exit0: пиксельное сравнение PASS / READY_FOR_INDEPENDENT_REVIEW. Exit1: DIFFERENCES_FOUND / REVIEW_REQUIRED. Exit2: BLOCK, ошибка, timeout, отсутствующий/невалидный diff или изменившийся вход. Различие не является доказанной инженерной ошибкой. Равенство не удостоверяет эталон, скрытые объекты, OCR, значения параметров или правильность расчёта. `acceptance_granted`, `engineering_verified`, `reference_authority_verified`, `execution_isolation_verified` остаются false.

diff-pdf запускается обычным локальным процессом, не квалифицированной песочницей. Поэтому этот пилот не подключён автоматически к пользовательским загрузкам/API. Сравнение нельзя использовать как обход отсутствующей защищённой обработки Office. Внешний пакет не добавлен в Git и не перераспространяется; лицензии бинарного комплекта и зависимостей проверяются отдельно перед поставкой.

Официальный пакет: https://github.com/vslavik/diff-pdf/releases/tag/v0.5.3
ZIP SHA256:31c6dd5472f3d83b4a6023cf929b475ded04ba5fa24b2d027fae3a3098b169ea. Приватная установка: `.engineer-os/tools/diff-pdf-0.5.3/bin/diff-pdf.exe`. На собственных PDF подтверждены отсутствие различий и обнаружение замены2500→2800; diff просмотрен визуально. Это synthetic integration, не проверка полного реального комплекта.

## Offline Gotenberg pilot

`scripts/render_document_gotenberg.py` принимает DOCX и заранее загруженный официальный `gotenberg/gotenberg@sha256:...`. Tag/latest не допускаются, implicit pull запрещён. Скрипт использует локальный Docker endpoint, не переменные remote Docker context. Linux Podman вызывается с `--remote=false`; Windows Podman transport в этом пилоте не поддержан.

```powershell
.venv-engineering/Scripts/python.exe scripts/render_document_gotenberg.py --source SOURCE.docx --output NEW-DIRECTORY --image gotenberg/gotenberg@sha256:ACTUAL-APPROVED-DIGEST
```

ACTUAL-APPROVED-DIGEST в примере — обязательный реальный SHA256 заранее проверенного образа, не готовая команда. Образ следует проверять по актуальным advisories, фиксировать версию и digest; старый образ с уязвимостями нельзя считать безопасным только из-за digest.

Для каждого запуска создаётся отдельный контейнер: network=none, без published ports и bind mounts, readonly root, пользователь1001:1001, HOME=/tmp, tmpfs/tmp2GiB, память3GiB,2CPU,256pids, cap-dropALL/no-new-privileges. HTTP запрос передаётся через stdin команды `docker exec curl` внутри контейнера на его loopback; host HTTP port не нужен. DownloadFrom, Chromium routes и webhooks выключены, LibreOffice URL deny-list запрещает всё. Есть health check, тайм-ауты и обязательное удаление только собственного UUID контейнера. Cleanup failure/timeout и изменение исходника возвращают BLOCK. Даже успешный результат — DERIVED_UNVERIFIED; `isolation_qualified=false`, приёмка false.

Это ещё не квалифицированная production изоляция: Docker engine и этот exact image/config должны быть реально испытаны, включая файловые/сетевые canary, макросы/ссылки, fonts и долгие документы. На данном Windows ПК Docker/Podman отсутствуют; WMI сообщил HypervisorPresent=false и VirtualizationFirmwareEnabled=false. DISM feature inventory потребовал административный token. BIOS/Windows features не изменялись; перезагрузки не было. Следующий инфраструктурный шаг — включить аппаратную виртуализацию и подготовить локальный Linux container engine либо предоставить доверенную локальную Linux-машину. Подключение внешнего сервера подразумевало бы передачу документов и не разрешено этим пилотом.

Официальные сведения: https://gotenberg.dev/docs/configuration и https://gotenberg.dev/docs/outbound-url-filtering ; advisories: https://github.com/gotenberg/gotenberg/security/advisories .

## Независимый OCR

В проекте уже имеются `table_worker.py`/`table_readback.py` и UI выбор PaddleOCR. Это не новый интегрированный движок: требуются отдельный Python, paddleocr/paddlepaddle3.2.0, PyMuPDF1.26.6, локальные модели и явный manifest восьми директорий. Поиск готового backend не подтверждает связь HTML таблицы с распознанными ячейками; существующий adapter сохраняет mapping UNVERIFIED. Настройка OCR не должна загружать модели во время анализа пользовательского документа. Полнота формул этим table profile не проверяется.

Отдельный CPU profile установлен в `C:/Users/maxim/engineer-os/.engineer-os/paddle32` (короткий путь обходит Windows MAX_PATH), без изменения окружения приложения: PaddleOCR3.2.0/PaddlePaddle3.2.0/PaddleX3.2.1/PyMuPDF1.26.6. `pip check` PASS; полный freeze сохранён приватно. Модели хранятся в `C:/Users/maxim/engineer-os/.engineer-os/paddle32-models`; подготовлены7из8, SLANeXt_wired не завершён. Загрузка оставшейся большой модели прекращена после отрицательного числового OCR control, backend автоматически не активирован.

Реальный Paddle OCR выполнен на собственной строке «Пролёт 2500 мм» и двух оригинальных PNG ТЗ с явными локальными det/rec и блокировкой Python HTTP requests. Это не доказанная системная сетевая изоляция. Paddle вернул «ролёт 25оомм» (нули заменены кириллической о); Tesseract на том же PNG вернул точную строку. Мелкий текст ТЗ Paddle прочитал ненадёжно. Поэтому этот профиль пока НЕ подходит для доверенного извлечения инженерных чисел; нельзя считать его установленность закрытием OCR/ТЗ. Кандидаты/координаты/хеши сохранены приватно, автоматическая нормализация о→0 не выполнялась. Неисправленная гипотеза о причине ошибки не записывается как доказанный дефект модели.

См. [QA текущего прохода](../qa/2026-10-16-document-visual-tooling.md).

## Закрытие этапа2

После квалификации renderer: source-bound reference для четырёх DOCX; адресная сверка визуального отображения ячеек/формул/рисунков с extraction; независимый OCR спорных изображений и чисел; разрешение семи UNCERTAINTY ТЗ; проверка сохранения и повторного чтения результатов через приложение. Подтверждённые ранее native cells/OMML/media payloads не подменяют эти проверки.

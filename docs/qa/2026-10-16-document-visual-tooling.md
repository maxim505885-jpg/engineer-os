# Дополнение этапа2: внешние инструменты, 15–16.10.2026

## Объём и сохранённая база

Продолжение `codex/v1-completion-20261015` после f4a8b24, не новая разработка с нуля. Существующие qualification.py, reader, evidence/acceptance и ранее проверенные native cells/OMML/media не заменены. Добавлены2явных CLI и тесты; новые проекты/репозитории в ENGINEER OS не копировались. Внешние бинарники/модели — приватные зависимости. Пользовательский dirty checkout, его ветка и сервер8765 не заменялись. Установка отдельного Paddle venv в его игнорируемом `.engineer-os` не меняет зависимости работающего приложения.

Контракт и команды: [document-visual-tools.md](../development/document-visual-tools.md). Это подготовка T03/T04; этап2 остаётся OPEN.

## Фактическая проверка

- Официальный portable diff-pdf0.5.3: archive SHA25631c6dd5472f3d83b4a6023cf929b475ded04ba5fa24b2d027fae3a3098b169ea совпал; локальный install receipt сохраняет также executable SHA.
- Реальный executable: одинаковые синтетические PDF →exit0/PASS; замена2500→2800 →exit1/DIFFERENCES_FOUND. PDF с подсветкой отдельно отрендерен и просмотрен. Это synthetic integration, не полнота документов объекта.
- Новый comparator: source/reference/engine/adapter hashes, private snapshots, повторная проверка неизменности, новый output/readback; нет engineering acceptance. Ошибка/timeout/изменение входа/невалидный diff →BLOCK. Обычный процесс diff-pdf не объявлен безопасной песочницей; автозапуск на пользовательских загрузках не включён.
- Offline Gotenberg pilot: pinned image только из локального engine, Docker local endpoint, networknone, readonly root, UID1001, без host mounts/ports, tmpfs/resource limits, удаление собственного контейнера. Реальный image/config не запускался: Docker/Podman отсутствуют, HypervisorPresent=false, VirtualizationFirmwareEnabled=false; feature inventory DISM требует admin token. BIOS/OS features не менялись, reboot не выполнялся. `isolation_qualified=false`, DERIVED_UNVERIFIED даже при успешном будущем conversion.
- CPU PaddleOCR3.2.0/PaddlePaddle3.2.0/PaddleX3.2.1/PyMuPDF1.26.6 установлены отдельно; pipcheckPASS. Первая попытка: connectionreset; повтор в длинном worktree path: MAX_PATH; короткий отдельный venv установлен успешно. Транзитивные версии зафиксированы private freeze; profile ещё не distribution-qualified.
-7из8явных моделей скачаны с официального BOS, SHA архивов/файлов сохранены. SLANeXt_wired не завершён; две собственные попытки полной/Range загрузки прекращены после отрицательной OCR квалификации. Эти собственные downloader processes остановлены адресно, не пользовательский app.
- Paddle реально обработал контрольную кириллическую строку и2исходных PNG ТЗ. Контроль: ожидается «Пролёт 2500 мм», Paddle «ролёт 25оомм», числовые токены25вместо2500; Tesseract вернул точную ожидаемую строку. Ненадёжный мелкий текст ТЗ не повышен до подтверждённой транскрипции. Высокая confidence не исправляет ошибку. Причина ошибки не установлена; нет заявления о неисправности всех моделей Paddle. Python HTTP requests блокировались, но системная network isolation не квалифицирована.
-29/29пользовательских файлов совпали с expected-sources.json; добавленных/пропавших/изменённых0. Семь UNCERTAINTY ТЗ не закрыты и не переименованы в PASS.

## Тесты и review

Новые тесты сначала дали8FAIL на отсутствующем поведении; после реализации8PASS. Дополнительная проверка безопасного local endpoint сначала дала1FAIL, после уточнения реализацииPASS. Итоговые13тестов покрывают differences/failure/mutation/output overwrite/invalidPDF/timeout/missing or malformed diff, pinned image/local transport, отсутствие runtime, cleanup failures/timeouts, false qualification и удаление remote env.

Независимый read-only review не установил важных дефектов; предложенные lifecycle/timeout/artifact/environment случаи добавлены. Reviewer fullsuite не запускал.

**Штатное `.venv-engineering`, PyMuPDF1.26.6:** полный свежий suite **1288tests,400.496s,OK,34skipped,exit0**. Фокусный повтор проблемных PDF/OCR модулей32tests/16.448s/OK. Architecture guard/repository guard PASS; после итогового staging repository tracked656. Diff whitespace checkPASS. Реальная Gotenberg/полная Paddle table интеграция не тестировалась.

**Отдельное системное окружение, PyMuPDF1.28.2:**1266tests/361.244s,8failures/4errors/95skips,exit1. Этот запуск не PASS. Подтверждено: `import fitz` печатает предупреждение в stdout перед JSON probe; закреплённый interpreter этого не делает. Совместимость с незакреплённым PyMuPDF/Pillow не реализовывалась, системные пакеты не изменялись.

Сбои системного запуска: `test_pdf_fixed_probe_really_reads_and_rasterizes`; `test_ole_original_asset_and_authenticated_bitmap_preview`; `test_actual_language_reaches_worker_and_persisted_request_binding`; `test_explicit_preprocessing_survives_worker_history_and_rejects_tampering`; `test_native_read_persists_and_reloads_without_evidence`; `test_stored_result_tampering_and_storage_limit_are_rejected`; `test_single_line_request_survives_authenticated_history_reload`; `test_object_pixels_reach_source_checkpoint_and_preview_without_acceptance`; errors: `test_optional_psm_binding_survives_real_worker_save_and_reload`(psm7/11), `test_real_isolated_worker_preserves_exact_source_and_selection`, `test_saved_request_binding_disagreement_rejects_hash_valid_record`. На штатном полном suite эти сбои не воспроизвелись. Точная причина отдельных bitmap несовместимостей отдельно не доказана.

## Приватные доказательства

`.engineer-os/v1-completion/document-qualification/visual-tools-0c4de27b4cda405a9a893ce71a8ffa3d`: snapshots/manifests/diff/preview. Рядом `visual-tools-pinned-regression.log`, `visual-tools-regression.log`, `visual-tools-pinned-focused.log`, `source-preservation-visual-tools.json`.

`.engineer-os/tools/diff-pdf-0.5.3/install-receipt.json`; `.engineer-os/tools/paddleocr-3.2.0`: install logs/freeze/probe scripts/raw outputs/ocr-control-comparison.json. Короткий main checkout `.engineer-os/paddle32-models/provision-receipt.json`:7моделей и явные причины BLOCK, не полный рабочий manifest.

## Следующее необходимое действие

Подготовить локальную Linux container среду: включить аппаратную виртуализацию и установить/настроить engine с административными правами, либо использовать доверенную локальную Linux-машину. После этого проверить exact Gotenberg image/config на собственных canary и только затем на четырёх DOCX. Визуальные эталоны, адресная семантическая сверка, OCR спорных чисел, семь UNCERTAINTY ТЗ и end-to-end сохранение/reload всё ещё обязательны. Новые инструменты не заменяют существующую разработку и не закрывают весь этап автоматически. Merge/deploy/release не выполнены.

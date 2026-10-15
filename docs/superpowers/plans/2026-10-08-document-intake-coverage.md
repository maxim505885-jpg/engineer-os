# №6 — обработка документов: implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Native execution is authorized by the user's instruction to complete the work in one pass.

**Goal:** Принимать заявленные оригиналы, показывать сохранённое покрытие и непрочитанные части, давать визуальную сверку и локальный OCR без ложного инженерного принятия.

**Architecture:** Сохранение оригиналов и SHA256 остаётся в files.py. PDF/изображения используют прежний журнал extraction_pages; локальный OCR вызывается отдельным ограниченным адаптером. LIR и расчётные экспорты принимаются как непроверенные оригиналы, без выдуманного декодирования solver. Просмотр страницы отделён от подтверждения источника.

**Tech Stack:** Python3.12+, SQLite, PyMuPDF, Pillow, optional local Tesseract5 rus+eng, existing optional Docling, plain JavaScript/Chromium.

**Spec:** docs/development/master-plan.md, №6; ENGINEER_OS_PROJECT_MAP.md, раздел57.

## Global Constraints

- MAX_FILE_BYTES=100 MiB; extraction MAX_PAGES=5000, MAX_PAGE_TEXT=20000, MAX_BLOCKS=1000, MAX_TOTAL_TEXT=2000000.
- Оригинал не изменяется. Возобновление требует того же SHA256 и идентичности parser, модели OCR и лимитов.
- NOT_EVIDENCE, completeness=NOT_CHECKED, acceptance=false; V4 может оставаться BLOCK.
- OCR без сети и shell, фиксированные параметры, конечный тайм-аут и ограниченные pixels/output. Отсутствие binary/language даёт явный отказ.
- Не менять main. Windows — №16; семантика LIR/solver — №9; DWG — №11.

## Review Focus

- PDF с текстом и растровой/векторной частью: текст не должен скрывать непрочитанные области.
- Повреждённый/зашифрованный оригинал: сохранность файла и понятный отказ без данных из исключения.
- OCR rotated/cropped pages и превышение лимита: корректная область либо явная неопределённость, никакого принятия.
- LIR/JSON/CSV: не путать сохранение контейнера с декодированием/проверкой расчёта.
- Отмена/продолжение: не повторять завершённые страницы, не менять происхождение и не сбрасывать бюджет.

### Task 1: Приём оригиналов и покрытие PDF

Files: files.py, extraction.py; tests/test_document_intake_coverage.py.

- [ ] Failing tests: LIR accepted with MODEL_DECODER_UNAVAILABLE and same SHA256; image accepted with OCR_REQUIRED; encrypted PDF has ENCRYPTED_PDF; mixed page retains text bbox and IMAGE_CONTENT_UNVERIFIED.
- [ ] Run new tests and confirm expected failures.
- [ ] Extend allowlist with LIR, PNG/JPG/JPEG, JSON/CSV; preserve bounded preview and explicit unverified export scope. Native blocks carry page_no and bbox; page journal records visual omissions.
- [ ] Run new tests and existing extraction/coverage tests.

### Task 2: Local OCR and resumable provenance

Files: new ocr.py, extraction.py, analysis_identity.py, automatic_analysis.py, store.py; tests/test_local_ocr.py.

Interfaces: ocr.identity() -> dict; ocr.page_blocks(page,page_no) -> list[dict]. Existing execute/store journal remains authoritative.

- [ ] Failing tests: missing binary/language, real OCR Russian+English scan, finite timeout, source coordinates, changed language identity rejecting resume.
- [ ] Add EXTRACT_OCR; render bounded page, run fixed Tesseract TSV command shell=False, bound outputs and convert pixel boxes to unrotated page coordinates. Fingerprint binary and local language models.
- [ ] Support image-as-one-page without altering original; OCR limitations stay explicit. Native remains default, OCR is an explicit action/selected backend.
- [ ] Verify actual local OCR plus interrupted extraction resumption.

### Task 3: Original preview and Office coverage

Files: preview.py, server.py, office.py, ui/app.js, ui/index.html, drive_import.py; HTTP/browser tests.

Interfaces: render_original(store,session_id,file_id,page) -> PNG bytes; private GET /api/sessions/{session}/files/{file}/preview?page=N.

- [ ] Failing tests: original preview before candidate, wrong project, changed SHA256, page bounds; Office per-sheet/per-table coverage.
- [ ] Add bounded original preview, page input, OCR action and expanded upload labels. Display sheet/table manifests and explicit omissions.
- [ ] Run authenticated HTTP and actual Chromium: upload LIR/image, refusals, page view, extraction/OCR journal, original download.

### Task 4: Declared corpus, review and handoff

- [ ] Verify real V4 identity and all-page native journal, real LIR originals and Office sources; retain honest BLOCK/UNCERTAINTY.
- [ ] Exercise generated blank/mixed/rotated/encrypted/corrupt/large examples, scanned Cyrillic, merged/hidden/formula Office examples; each omission has a reason or refusal.
- [ ] Run full Python, Node, DOM/Chromium, architecture guard, compileall and diff checks. Independent review and fixes.
- [ ] Publish stacked draft; update the same master plan/map and guarded file identities. Close №6 only for the documented corpus and supported versions; report remaining source-specific limits and next №7.

## Выполнение 08.10.2026

✅ Tasks1–4 выполнены в объявленных границах. 544 Python, 4 Node, HTTP/DOM и настоящий Chromium PASS. Реальный набор: V4 534 страницы, DOCX487/DOC492/XLSX125 логических элементов, два текущих LIR. Локальный ru+en OCR реально выполнен; Docling live не заявлен. Ревью Important image-limit исправлен и повторно проверен. Подробности: docs/qa/2026-10-08-document-intake-coverage.md. V4 BLOCK и acceptance=false сохраняются. Следующий мастер-пункт №7; Windows №16.

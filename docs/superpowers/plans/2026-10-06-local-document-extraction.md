# Фоновое извлечение PDF Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans. Реализация в текущей сессии, независимый reviewer в конце.

**Goal:** Обработать выбранный PDF через существующий Worker с durable page journal.
**Architecture:** Store хранит extraction_pages и resume; extraction.py вызывает native или существующий Docling adapter. Server/UI управляют задачей без модельных инструментов.
**Tech Stack:** Python 3.12+, SQLite, PyMuPDF, optional Docling, plain JS.
**Spec:** ../specs/2026-10-06-local-document-extraction-design.md

## Global Constraints

- 5000 страниц, 20000 символов/1000 блоков на страницу, 2000000 символов/задачу.
- UNVERIFIED/NOT_EVIDENCE/acceptance=false, completeness NOT_CHECKED, FINAL AUDIT NOT_RUN.
- Windows последними; no paid API, no automatic replay or original mutation.

## Review Focus

- Changed original: stop before registering current-page output; resume rechecks hash.
- Foreign conversation/job: reject journal, page and resume access.
- Missing Docling: explicit failure, no fake native fallback.
- Stop/restart: retained checkpoints, explicit resume skips only completed pages.
- Oversized parse: bounded retained blocks/text; truncation BLOCK, no budget bypass.

## Task 1: Queue, extraction and user flow

Files: create engineering/local_app/extraction.py; modify store.py/worker.py/server.py/UI;
tests/test_local_document_extraction.py and HTTP/DOM smoke; development contract.
Interfaces: Store.enqueue_extraction(session_id,file_id,backend),
Store.resume_extraction(session_id,job_id), Store.extraction_pages(session_id,job_id,offset,limit),
Store.extraction_page(session_id,job_id,page), extraction.execute(store,job,stop_event).

- [x] Write regression tests for >20-page PDF, errors/hash/isolation/resume/budgets and adapter contract.
- [x] Run tests: expected failure because extraction queue is missing.
- [x] Implement page records and checkpoint counts, worker routing and native/Docling readers.
- [x] Add protected routes and GUI queue/resume/journal, test real loopback and jsdom.
- [x] Run full unittest suite, Node, compileall/JS/diff, independent review; fix meaningful findings.
- [ ] Commit/publish separate draft PR based on PR47; update same living map ID and GitHub docs branch.

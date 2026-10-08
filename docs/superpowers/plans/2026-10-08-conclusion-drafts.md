# Conclusion drafts Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:executing-plans. User authorized one-pass inline execution; do not add approval pauses.

**Goal:** Проверяемый редактируемый черновик и согласованный DOCX/PDF экспорт.
**Architecture:** conclusions.py assembles immutable versioned document records from current real-case and live sources; conclusion_export.py renders their single content structure. Existing authenticated server/UI expose save/history/export.
**Tech Stack:** Python stdlib SQLite/OOXML, existing PyMuPDF Story, native JS.
**Spec:** docs/superpowers/specs/2026-10-08-conclusion-drafts-design.md

## Global Constraints
Draft only; no engineering acceptance or FINAL AUDIT issuer. Existing originals immutable. No paid dependencies. №9 deferred by user; no fake solver result.

## Review Focus
- Source or TЗ changes reject export until basis rebuilt.
- Foreign project IDs and concurrent stale saves reject without overwriting history.
- Tampered stored content never exports.
- Long Cyrillic text, tables and XML/HTML characters preserve content without remote fetch.
- UI refresh/project changes preserve unsaved edits and revision guards.

### Task 1: Document versions and export
Files: engineering/local_app/conclusions.py, conclusion_export.py, store.py; tests/test_conclusion_drafts.py.
Interfaces: build(store,session_id,expected_revision,author,summary,recommendations,limitations); report(store,session_id); export(store,session_id,revision,format) returns bytes/MIME.
- [ ] Write failing tests for draft status, references, restart/history, stale basis, conflicts/isolation, tampering, text escaping, DOCX/PDF content and pagination.
- [ ] Run unittest discover -s tests -p test_conclusion_drafts.py; expect missing module RED.
- [ ] Implement persistent revisions and live revalidation, single structured content, bounded renderers.
- [ ] Run targeted tests; expect PASS. Render DOCX/PDF and inspect page images.

### Task 2: Authenticated user route
Files: server.py, ui/app.js, tests/test_local_app_http.py, e2e/local_conclusion_ui_smoke.cjs.
Consumes: Task1 build/report/export. Produces: /api/sessions/:id/conclusions and /conclusions/:revision/:format, visible editable form/history/downloads.
- [ ] Write failing HTTP and Chromium save/edit/reload/export tests; verify RED.
- [ ] Add endpoints and editable form with captured revision, safe textContent, project reset and authenticated download.
- [ ] Run targeted HTTP/Chromium; expect PASS including foreign project and stale edits.

### Task 3: Verification and handoff
- [ ] Run full Python, Node, DOM/Chromium, architecture_guard, compileall, diff-check.
- [ ] One independent whole-branch code review, reproduce material findings RED→GREEN.
- [ ] Publish draft PR, preserve main; save report and replace existing canonical map with fresh version guard. Mark №9 deferred and document exact №10 result/limits.

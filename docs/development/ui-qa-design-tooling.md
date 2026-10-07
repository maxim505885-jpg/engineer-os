# UI/QA tooling boundary

This document defines development-only UI and browser tooling for ENGINEER OS.
None of these tools may grant engineering acceptance, alter evidence status, or
bypass ENGINEER CORE gates.

## Microsoft Playwright

Repository: https://github.com/microsoft/playwright

Purpose: real-browser end-to-end verification of the local cabinet. The existing
`e2e/local_app_ui_smoke.cjs` launches the actual local Python app and worker,
uses a controlled synthetic model transport, uploads a source file, sends a
message, verifies inert model markup, reload persistence, conversation
navigation, and a mobile viewport.

CI pins Playwright to `1.55.0` and installs Chromium in the ephemeral runner.
This is a development/test dependency only. The normal local application does
not require Node or Playwright.

Run locally after installing the pinned browser dependency:

```bash
npm ci --prefix e2e --ignore-scripts --no-audit --no-fund
npx --prefix e2e playwright install chromium
npm run test:browser --prefix e2e
```

A browser PASS proves only the tested UI workflow. It does not prove OCR quality,
normative applicability, calculation semantics, solver execution, Windows
compatibility, FINAL AUDIT, or ACCEPTED.

## Impeccable

Repository: https://github.com/pbakaus/impeccable

Use as design-review guidance for typography, spacing, hierarchy, accessibility,
layout, palette, and UI polish. Do not vendor the repository into ENGINEER CORE.
Do not let a design skill rewrite engineering statuses, evidence labels, source
traceability, safety copy, or acceptance logic.

Recommended use: audit proposed UI changes before merge, then validate behavior
with automated tests and Playwright.

## Emil Kowalski Skills

Repository: https://github.com/emilkowalski/skills

Use selectively for interaction and motion review. Motion must remain optional,
interruptible, accessible, and must never hide BLOCK/UNCERTAINTY/error states or
delay access to evidence/source-review controls.

Do not install these skills as runtime dependencies of ENGINEER OS. They are
developer guidance only.

## Trust boundary

The controlling order is:

1. ENGINEER CORE contracts and evidence/acceptance gates.
2. Functional/API/unit tests.
3. Real browser behavior via Playwright.
4. Design/motion guidance from external skills.

Visual quality can improve presentation but can never promote an engineering
result. Any conflict is resolved in favor of ENGINEER CORE and fail-closed
status behavior.

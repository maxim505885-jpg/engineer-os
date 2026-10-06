# Пункт 5 — Связать анализ с доказательствами и ТЗ

> Исполнение самостоятельно: superpowers:executing-plans; user authorised all ordinary local work and draft publication. Windows9 последней, без main merge/deploy.

Goal: explicit requirement checklist, source-bound conclusions and visible source gates. Existing SQLite evidence/source review/CORE stay controlling; no model-created accepted evidence.

Design: immutable requirement sets (1–50 user-authored lines, each≤2000 chars), append-only assessments (conclusion≤2000, evidence IDs≤20, SUPPORTS/CONTRADICTS/UNKNOWN, expected revision). Persist revision and source-review snapshot, show changed/rejected/unchecked source. A source-confirmed quotation enables traceability only: SOURCE_LINKED/UNCERTAINTY, never engineering PASS/ACCEPTED. Normative/calculation verification remains stage6.

Office candidate registers through existing extraction child ID/logical unit and server-owned locator/text; fresh bounded parsing and exact quote verifies main DOCX/XLSX original. DOC validates preserved derived hash; DERIVED_UNVERIFIED cannot become an original source confirmation. PDF retains native exact quote/provenance path. Analysis receipt refs can prefill the candidate form but never create evidence automatically.

### Task 1: Source binding
- [ ] Tests: Office exact locator/text registration and source revalidation; wrong session/unit/quote/hash fail; blocked unit/DOC cannot be source-confirmed; PDF existing behavior.
- [ ] Implement source_binding.py and evidence/review API optional source_job/logical_unit. Source-match != engineering truth, source limitations retained.
- [ ] Run tests/test_stage5_evidence_tz.py RED→GREEN; commit.

### Task 2: Requirements and gates
- [ ] Tests: checklist durable/versioned; assessments trace quote/type/review; review changes/foreign or changed originals block; contradiction remains visible; unknown/no evidence fails closed.
- [ ] Implement requirements.py; SQLite immutable sets/events and optimistic revision. APIs checklist/assessment/report, limits and session isolation.
- [ ] Run focused tests RED→GREEN; commit.

### Task 3: Analysis and UI
- [ ] Tests: CORE/CHAT context sees checklist, original-only source ref cannot imply reviewed evidence, requirement changes invalidate resume. HTTP/jsdom end-to-end Office candidate→review→requirement assessment, reload and session isolation.
- [ ] Add deterministic requirement/source trace report to CORE/job result and identity; UI checklist/assessments, source-unit form and receipt prefill. All displayed source/model content uses textContent.
- [ ] Run targeted tests RED→GREEN; commit.

### Task 4: Review and publication
- [ ] Full Python/Node/HTTP-DOM checks, actual DOCX/XLSX production source-binding sample; independent whole-branch review (one reviewer, one Important fix pass).
- [ ] Report exact limitations; publish draftPR on PR56, verify tree/CI, update same live map and nine-stage plan.

Pre-flight: Task1 output candidate locator/source binding feeds Task2 gate; Task2 requirements/report feeds Task3 identity/context. Gates revalidate original and latest source review; never trust stored SOURCE_LINKED alone. Existing PDF review/source geometry stays unchanged. No reachable separate spec: this approved plan's intent and current AGENTS.md bind provisional implementation decisions. User requires autonomous work, no repeated routine approval handoffs.

Review focus: repeated quote in logical element; model text claiming accepted; mutable derivative/checkpoint; concurrent assessment/review; selected files excluding requirement evidence. Treat missing/changed/ambiguous data as BLOCK; never silently omit limits.

## Журнал выполнения

Tasks1–3 complete: Office original quote/locator revalidation; immutable user checklist and append-only assessments; source gates/context identity; UI source candidate→review→requirement, durable reload. All targeted RED→GREEN;24focused tests. Harness fixture errors (public file lacks private path, completed extraction write protection) fixed without weakening production guards. Requirements context function aliased to avoid shadowing existing attachment text list.

Task4 checks:400Python/4Node/compileall/JS/diff PASS; both actual launcher/HTTP/Worker/jsdom scenarios PASS. Real user DOCX/XLSX source locations confirmed as quoted text only, source-linked requirements remain UNCERTAINTY; DOC derivative remains NOT_ESTABLISHED/BLOCK, originals preserved. QA repeated after final source-gate reason fix. Controlled model and test checklist, not real engineering case/ТЗ or live Qwen quality.

Final review: one independent whole-branch read-only review. Two Important fixed RED→GREEN: unselected requirement-dependent source reviews now participate in live/resume identities; polling preserves focused control/caret/selection and expanded history. Full400suite PASS after Python fixes; DOM PASS after UI fixes.

Final Ruling: reviewer Minor “finding_gates hidden in CORE UI” regraded Important because stage5 requires user-visible reasons for source BLOCK; fixed RED→GREEN actual HTTP/DOM. Cost if wrong: extra source-gate detail in role results, no change to engineering status. No deferred new minors. Inherited stage4 converter launcher-only fingerprint remains open; do not upgrade converter runtime inside unfinished jobs.

Ruling: checklist and SUPPORTS/CONTRADICTS assessments are user-authored declarations, not automatic semantic extraction or truth verification. Cost if wrong: incomplete checklist/wrong declared relation remains possible; all outputs disclose origin, data-class verification=false and acceptance=false. True normative/calculation checks are stage6, accepted real case stage7, Windows stage9.

# №7 — исходное ТЗ, ответственность и предметный разбор источников

User intent: завершить оставшиеся критерии №7 за один проход, используя предоставленные документы; Windows №16, нормы №8 и solver №9 остаются отдельными этапами. Approval handoffs explicitly waived by the user's one-pass instruction; draft publication and same-map updates already authorized.

Scope: existing requirements/review/CORE/UI flow, not a new acceptance subsystem. Evidence first; no invented measurements or normative decisions. Spec: AGENTS.md, master-plan №7 and living map §59.

1. [x] Correct source transcription: visually inspect V4 pages5–9, tasks11.1–11.12 and related scope/deliverable/qualification/access conditions. Inspect geodesy/graphics and all3 project calculation books. Record source-bound comparisons and actual gaps; correct prior false paraphrases explicitly.
2. [x] RED→GREEN: freeze optional ToR source candidate bases in create_set; report current source gates, stale basis and absent original binding. Add declared assessment actor (never authenticated engineer). CORE reconciliation blocks missing/invalid ToR basis and missing responsible assessment actor. HTTP/UI expose existing forms; preserve legacy history.
3. [x] RED→GREEN native geometry fix: only harmless right-end horizontal PDF padding may be ignored, never internal text/line/region ambiguity. Recheck actual quote after implementation; preserve engineering_verified=false.
4. [x] Reproducible real-source dossier and requirement-by-requirement outcomes; whole suite/DOM/Chromium and one independent final branch review. Publish draft stacked on PR80, update same map/plan/Library files. Close №7 only if its actual criterion is evidenced; otherwise state exact blocking evidence, never relabel BLOCK as verified.

Interfaces: create_set(..., source_evidence_ids=None) freezes candidate/source-review basis; assess(...,actor=None) keeps legacy clients compatible but absent actor cannot satisfy CORE responsibility. requirements.report exposes tor_sources/tor_source_status and row assessment_actor/assessment_actor_verified=false; engineering_review consumes these without authenticating declared identity. API forwards optional fields; UI sends selected ToR bases and author. Existing acceptance gate unchanged.

Execution: source inspection,42-row preliminary dossier,564 Python/4 Node/DOM/Chromium and independent18-test review completed. №7 closure deliberately withheld: missing verified transcription and factual source responsibility. Draft PR81 published; same-map/plan update prepared. Whole №7 remains open for the documented source gates.

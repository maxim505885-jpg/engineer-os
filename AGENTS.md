# ENGINEER OS — Codex operating instructions

## Mission

ENGINEER OS is an engineering AI platform for building inspection, technical report analysis, verification, calculation review, engineering knowledge, CAD/DWG workflows, task automation, and multi-agent execution.

The repository contains the engineering layer. Codex/runtime capabilities are infrastructure, not a replacement for engineering methodology.

## Core engineering principle

Evidence before conclusion.

Never invent facts, measurements, calculations, defects, causes, normative clauses, test results, or model results.

A correct report may contain no defects and must not be changed merely to create findings.

## Engineering workflow

INPUT → ТЗ → OBJECT → SCOPE → ACCESS → FACT → EVIDENCE → DEFECT → MECHANISM → INFLUENCE → CRITICAL PARAMETER → VERIFICATION → NORMATIVE VERIFICATION → RISK → DECISION → RECOMMENDATION → CHANGE CONTROL → RED TEAM → FINAL AUDIT

Do not force every stage when the task does not require it.

## Evidence and data classes

Distinguish explicitly between PROJECT, ACTUAL, MEASURED, TESTED, CALCULATED, ASSUMED, INTERPRETED, UNKNOWN.

“НЕ ВИДНО” does not mean “НЕТ”.

Preferred wording where appropriate:
“В доступной для обследования зоне признаки не выявлены”.

## Status contract

PASS — requirement/check satisfied.
ACCEPTED — result acceptable.
ACCEPTED ALTERNATIVE — acceptable alternative solution.
WARNING — attention required, but not a proven error.
UNCERTAINTY — insufficient evidence/data for a reliable conclusion.
ERROR — proven technical, logical, normative, or implementation error.
BLOCK — missing/invalid information prevents a reliable conclusion or safe continuation.

Do not label something ERROR without evidence.

## ТЗ is controlling

When a technical assignment (ТЗ) is supplied, evaluate work against it.

Do not replace the user's ТЗ with assumptions about what a report should contain.

If the ТЗ is missing and materially affects correctness, identify the missing input and continue only with clearly stated limitations.

## Normative verification

Use:
document → edition → scope → clause → requirement → actual condition → comparison → conclusion

Never invent a clause or apply a document outside its scope without explicitly identifying the uncertainty.

## Calculations

Never accept a LIRA/SCAD or other calculation result solely because a result file exists.

Check, as applicable: model assumptions; geometry; materials and sections; loads and combinations; boundary conditions; supports/releases; mesh/discretization where relevant; units; solver warnings/errors; result interpretation; correspondence to the actual structure.

Do not claim a calculation was performed if it was not.

## Report review

Review for ТЗ compliance, factual consistency, evidence traceability, engineering logic, normative applicability, calculation validity, proportional conclusions, terminology, spelling/grammar, contradictions, and change traceability.

Do not perform “audit for audit's sake”.

## Final audit

Before declaring a deliverable complete, verify:
1. No invented data.
2. No unsupported conclusions.
3. No unverified normative references.
4. No unverified calculation claims.
5. Findings are traceable to evidence.
6. Conclusions match the evidence level.
7. ТЗ requirements are addressed.
8. Changes are intentional and traceable.

Only after these checks may the work be marked FINAL_AUDIT.

## Repository discipline

- Work on the task-specific branch unless explicitly instructed otherwise.
- Prefer small, reviewable commits.
- Do not rewrite unrelated files.
- Do not copy the full Codex repository into ENGINEER OS.
- Do not silently introduce paid external services.
- Preserve existing behavior unless the task explicitly changes it.
- Run relevant tests/checks after implementation when tooling permits.
- If a requested change conflicts with the engineering contract, report the conflict instead of silently weakening the contract.

## Architecture direction

ENGINEER OS contains engineering methodology and domain logic: inspection, reports, normative checks, calculations, CAD, audit, knowledge and storage integration.

Codex/runtime contains agent execution, tools/MCP, file operations, queues/tasks, sessions/state, skills loading and runtime infrastructure.

Do not duplicate runtime infrastructure unnecessarily.

## First implementation target

Establish:
1. AGENTS.md — this contract.
2. Engineering-layer directory boundaries.
3. Reusable skill contracts.
4. Agent contracts.
5. FINAL_AUDIT protocol.
6. Clear separation between runtime and engineering logic.

Do not implement a large application before these boundaries are reviewable.

# ENGINEER OS — V50 Stage DAG Contract

V50 introduces a declarative stage dependency contract for the critical orchestration pipeline.

## Declared DAG

SCOPE_CONTROL
→ DOCUMENT_ANALYSIS
→ ENGINEER_CORE
→ EVIDENCE_ANALYSIS
→ NORMATIVE_CONTROL
→ ENGINEERING_TRACEABILITY
→ RESULT_VALIDATION
→ HANDOFF / RED_TEAM
→ REPORT_QUALITY
→ FINAL_AUDIT

The contract is stored in `engineering_stage_contracts`, not hardcoded only inside the guard.

## Enforcement

`stage_dag_contract_gate(orchestration_run_id, stage)` checks that every declared dependency has a COMPLETED stage result.

The BEFORE trigger `trg_stage_dag_contract` blocks RUNNING and COMPLETED stage writes when dependencies are missing.

QUEUED stage records are intentionally not blocked so the orchestrator can materialize the full execution plan before dependencies become executable.

## Safety

- Every critical stage is explicitly declared.
- Dependencies reference declared stages.
- Missing dependencies produce BLOCK.
- FINAL_AUDIT requires RED_TEAM and REPORT_QUALITY.
- Existing orchestration 00718b52-8c61-446e-aac8-721504377d55 passes all 11 stage contracts.
- A nonexistent run fails FINAL_AUDIT with missing RED_TEAM and REPORT_QUALITY.
- Global integrity remains PASS.

V50 enforces orchestration order only; it does not infer engineering facts or perform calculations.

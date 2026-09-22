# ENGINEER OS — Architecture Integrity v46

## Purpose

v46 adds a read-only integrity gate to ENGINEER OS. It does not alter engineering state.

## Invariants

1. Terminal orchestration runs must not have QUEUED/RUNNING jobs.
2. One orchestration run may not have more than one active job for the same stage.
3. Evidence claims with explicit PENDING/UNVALIDATED status are reported as validation debt.
4. Blocking unresolved contradictions are reported as validation debt.

## Runtime

`public.engineer_os_integrity_snapshot()` returns:

- PASS/BLOCK integrity status;
- active orchestration/job/task-run counts;
- duplicate active stages;
- terminal orchestration with active jobs;
- unvalidated evidence claims;
- unresolved blocking contradictions.

## Validation-first rule

The snapshot is diagnostic only. It must not invent, repair, or rewrite historical engineering state. Any BLOCK condition must be investigated through the existing orchestration, evidence, validation and red-team pipeline.

## Next architecture layer

The existing database already contains the core entities required for the next Evidence/Claim architecture:

- evidence
- evidence_claims
- engineering_conclusion_traces
- engineering_result_validations
- engineering_result_handoffs
- engineering_contradictions

The next implementation step is to enforce claim-to-evidence traceability at the validation gate rather than adding a parallel data model.

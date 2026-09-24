# ENGINEER OS — V49 Validation Contract Gate

## Purpose

V49 converts the final validation path into one explicit contract:

`RESULT_VALIDATION → EVIDENCE → TRACEABILITY → RED_TEAM → FINAL_AUDIT`

The database must not allow RED_TEAM or FINAL_AUDIT to enter an executable state unless the upstream validation chain is satisfied.

## Contract

For RED_TEAM:

1. At least one result validation exists for the orchestration.
2. At least one validation is PASS / ACCEPTED / ACCEPTED_ALTERNATIVE.
3. No validation is BLOCK / ERROR / FAILED.
4. Claim-to-evidence traceability gate is PASS.

For FINAL_AUDIT:

1. All RED_TEAM prerequisites above are satisfied.
2. RED_TEAM is already COMPLETED.

The contract deliberately does not require non-empty validation evidence_refs by itself. A successful validation may legitimately have zero direct evidence references when the validated result contains no claim requiring a direct evidence reference; claim-level traceability remains enforced by V47/V48.

## Enforcement

V49 replaces the internal decision used by `guard_red_team_final_audit()` with `validation_contract_gate()`.

The existing V48 BEFORE trigger on `orchestration_stage_results` therefore remains the enforcement point. No parallel trigger is introduced.

## Safety properties

- Missing validation blocks RED_TEAM.
- Failed/blocking validation blocks RED_TEAM.
- Failed traceability blocks RED_TEAM.
- FINAL_AUDIT cannot start before RED_TEAM completes.
- Existing successful orchestration `00718b52-8c61-446e-aac8-721504377d55` passes both RED_TEAM and FINAL_AUDIT contract checks.
- A nonexistent orchestration fails the contract and the guard returns false.

## Non-goals

V49 does not reinterpret engineering findings, create defects, infer causes, or perform calculations. It enforces execution order and validation provenance only.

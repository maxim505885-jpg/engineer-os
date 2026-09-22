# ENGINEER OS V47 — Claim → Evidence Traceability Gate

## Purpose
Prevent engineering conclusions from reaching a trusted state without traceable facts/evidence and without unresolved blocking contradictions.

## Gate
public.claim_evidence_traceability_gate(orchestration_run_id)

Checks:
- conclusion traces must have evidence_refs and fact_refs unless already PASS/ACCEPTED/ACCEPTED_ALTERNATIVE;
- weak/unverified FINDING/CONCLUSION/FACT claims are reported;
- blocking contradictions must be resolved/closed/accepted.

## Decision
- PASS: no untraceable conclusions and no blocking contradictions.
- BLOCK: at least one untraceable conclusion or blocking contradiction.

This gate reuses the existing ENGINEER OS traceability model. No parallel evidence model is introduced.

## Global integrity
engineer_os_integrity_snapshot() now includes the traceability invariant.

V47 is intentionally a validation gate, not an audit-for-audit's-sake layer.

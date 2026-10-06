# ENGINEER CORE

ENGINEER CORE is the deterministic orchestration layer for ENGINEER OS.

It converts a user task into explicit specialist-agent tasks and combines only returned agent statuses. It never fabricates engineering facts, measurements, calculations, normative clauses, or conclusions.

## Contract

Input: task id + ТЗ + material references + requested checks.

Plan: specialist tasks for inspection, report review, normative verification, calculation review, and mandatory FINAL_AUDIT.

Output: aggregate status based only on specialist results:

- ERROR/BLOCK are blocking;
- UNCERTAINTY prevents a false positive conclusion;
- WARNING remains visible;
- complete, valid specialist results plus an accepting FINAL AUDIT with exact
  specialist coverage and an explicitly passing external acceptance gate can
  produce ACCEPTED. A missing gate never grants acceptance.

The mutable collection state is bound to the original task ID, ТЗ, material
identities and requested checks. Changing that execution scope requires a new
state and new specialist results. Before collection and final status calculation,
CORE revalidates the canonical plan, result identities, statuses, proof shapes,
duplicates and audit ordering. Invalid stored state yields BLOCK before invoking
the external gate; a rejected incoming batch does not partially modify state.

Proof IDs establish the contract shape, not proof authenticity. The external
auditable gate remains responsible for evidence identity, domain verification
and engineering acceptance. These in-process checks are not a tamper-proof
boundary against code with access to private Python objects.

The Codex adapter includes the controlling ТЗ and materials as untrusted task
data. Prior results include failed specialists and malformed-output failures,
so FINAL AUDIT cannot silently lose the latest runtime error.

CORE_PLAN only prepares and persists the plan. CORE_RUN executes preliminary
specialist drafts via the local model and persists per-role errors/results; its
model "final-audit-agent" remains preliminary and cannot grant acceptance.

Stage 8 adds a separate deterministic local FINAL AUDIT over the current
immutable Stage-7 case snapshot. That audit may feed ENGINEER CORE through
LocalFinalAuditAcceptanceGate only when it is fresh, ACCEPTED, and bound to the
same CORE_RUN task_id. Production may additionally require the existing
SupabaseAcceptanceGate. See [local execution contract](../../docs/development/local-core-run.md)
and [Stage-8 FINAL AUDIT](../../docs/development/stage8-final-audit.md).

The current real Naberezhnaya case remains BLOCK because upstream point-6/V4
prerequisites are open; no real-object ACCEPTED is claimed. Windows transport
remains the final plan item.

See [core audit](../../docs/development/engineer-core-audit-2026-10-06.md) for
the current implementation findings and verification limits.

The runtime that executes specialists can be Codex or another compatible agent runtime. ENGINEER OS owns the engineering contracts and skills; the runtime owns execution, tools, files, sessions and queues.

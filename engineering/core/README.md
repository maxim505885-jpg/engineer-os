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
- complete accepted results produce ACCEPTED.

The runtime that executes specialists can be Codex or another compatible agent runtime. ENGINEER OS owns the engineering contracts and skills; the runtime owns execution, tools, files, sessions and queues.

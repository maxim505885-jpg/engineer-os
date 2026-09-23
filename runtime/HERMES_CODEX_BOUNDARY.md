# Hermes ↔ Codex Boundary

## Purpose

Document the exact responsibility split before adding a Hermes process to ENGINEER OS.

### Hermes responsibilities

Hermes may provide:

- persistent sessions;
- runtime memory;
- skills/runtime discovery;
- subagent coordination;
- background/cron execution;
- gateway/channel integration;
- lifecycle around long-running agent work.

### Codex responsibilities

Codex App Server provides:

- agent turns;
- repository/file operations;
- shell execution where policy permits;
- MCP;
- sandbox and approval policy;
- execution state/events.

### ENGINEER OS responsibilities

ENGINEER OS remains authoritative for:

- ТЗ;
- object/scope;
- evidence;
- engineering facts;
- engineering findings;
- normative verification;
- calculation verification;
- report review;
- risk/decision;
- RED TEAM;
- FINAL_AUDIT.

## Required data flow

```
user/task
  -> ENGINEER OS EngineerTask
  -> runtime session
  -> specialist turn
  -> AgentResult
  -> ENGINEER CORE aggregation
  -> FINAL_AUDIT
```

The runtime may add session identifiers, thread identifiers and execution receipts, but it must not rewrite engineering findings.

## No duplicate orchestration

Do not create a second engineering orchestrator in Hermes.

ENGINEER CORE remains the planner/contract authority. Hermes may schedule or host execution, but specialist scope and result validation remain controlled by ENGINEER OS.

## Migration sequence

1. Keep the current direct Codex App Server adapter working.
2. Introduce a runtime-neutral execution interface.
3. Add Hermes as an optional host implementing that interface.
4. Run the same ENGINEER OS task through both paths.
5. Compare `AgentResult` contracts and terminal status.
6. Only then make Hermes the default host.

This avoids making the engineering system dependent on an unverified runtime integration.
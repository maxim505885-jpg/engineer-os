# External orchestration boundary

ENGINEER OS may use LangGraph, Hermes, Codex, Open WebUI or another runtime to
schedule execution. These runtimes are executors/orchestrators, not authorities
for engineering truth.

## Invariants

1. EngineerCore owns the planned agent set.
2. An external graph may only select a pending agent already present in that plan.
3. External orchestration cannot create PASS, ACCEPTED or ACCEPTED_ALTERNATIVE.
4. AgentResult validation, evidence gates, domain proof, FINAL AUDIT and the
   database-backed acceptance gate remain authoritative.
5. Unknown or replayed orchestration steps fail closed.
6. No LangGraph dependency is required by ENGINEER OS core; a concrete adapter
   can be installed separately and must target this boundary.

This prevents a graph-runtime upgrade, prompt change or external checkpoint from
becoming an acceptance bypass.

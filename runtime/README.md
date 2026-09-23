# ENGINEER OS Runtime Integration

This directory defines the boundary between the ENGINEER OS engineering layer and external agent runtimes.

## Runtime ownership

ENGINEER OS owns:

- engineering contracts;
- evidence and traceability;
- inspection/report/normative/calculation workflows;
- engineering skills;
- FINAL_AUDIT.

The runtime owns:

- sessions and long-lived execution;
- subagent scheduling;
- tool/MCP execution;
- file access;
- process lifecycle;
- runtime memory;
- Codex App Server transport.

## Target composition

```
ENGINEER OS
    |
    +-- engineering core
    +-- engineering skills
    |
    v
Hermes runtime (optional orchestration/runtime layer)
    |
    v
Codex App Server
    |
    +-- files
    +-- shell/execution
    +-- MCP
    +-- sandbox
```

Hermes is not copied into this repository. Its runtime capabilities are consumed through a narrow adapter boundary.

Codex is not copied into this repository. ENGINEER OS communicates with Codex App Server through `engineering/core/codex_runtime.py`.

## Integration rules

1. One task has one ENGINEER OS `task_id`.
2. Runtime execution must preserve that `task_id`.
3. Specialist results must conform to `AgentResult`.
4. Runtime failures map to `ERROR`; interruption maps to `BLOCK`.
5. Missing engineering evidence maps to `UNCERTAINTY` or `BLOCK`, never invented certainty.
6. Runtime state must not become the source of truth for engineering conclusions.
7. Secrets and runtime databases must not be committed to Git.
8. The adapter must remain replaceable: Codex can be called directly or through Hermes without changing engineering skills/contracts.

## Current implementation

The first runtime path is:

`EngineerRunner -> EngineerCore -> CodexRuntimeAdapter -> CodexAppServerClient`

The Hermes layer is intentionally an orchestration option rather than a second engineering core.
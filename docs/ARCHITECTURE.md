# ENGINEER OS Architecture

## Purpose

ENGINEER OS is the engineering specialization layer that can run on top of an agent runtime such as Codex.

## Boundary

### Runtime layer

Responsible for execution infrastructure:
- agent loop;
- tools and MCP;
- sessions/state;
- task queues;
- file access;
- memory/runtime services;
- skills loading;
- Git/worktree operations.

### ENGINEER OS layer

Responsible for engineering workflows:
- inspection analysis;
- evidence handling;
- technical report review/generation;
- normative verification;
- calculation verification;
- CAD/DWG workflows;
- risk/decision logic;
- final audit.

## Target structure

ENGINEER OS/
├── AGENTS.md
├── docs/
│   └── ARCHITECTURE.md
├── engineering/
│   ├── inspection/
│   ├── reports/
│   ├── normative/
│   ├── calculations/
│   ├── cad/
│   └── audit/
├── knowledge/
├── skills/
│   ├── inspection-audit/
│   ├── report-review/
│   ├── normative-check/
│   ├── calculation-review/
│   └── final-audit/
└── storage/

Empty directories are intentionally not committed yet; executable implementation should add files with concrete contracts.

## Agent roles

- ENGINEER CORE
- INSPECTION AGENT
- EVIDENCE AGENT
- REPORT AUDIT AGENT
- NORMATIVE AGENT
- CALCULATION AGENT
- CAD/DWG AGENT
- RISK/DECISION AGENT
- FINAL AUDIT AGENT

Agents should have narrow responsibilities and explicit inputs/outputs rather than overlapping hidden behavior.

## Source of truth

The user's supplied ТЗ controls the requested scope for each engineering task.

Engineering conclusions must be traceable to source evidence and must preserve uncertainty where evidence is insufficient.


## Runtime integration

The runtime boundary is documented in `runtime/README.md` and `runtime/HERMES_CODEX_BOUNDARY.md`.

The current executable path is:

```
EngineerRunner
  -> EngineerCore
  -> AgentRuntimeAdapter
  -> CodexRuntimeAdapter
  -> Codex App Server
```

Hermes is an optional runtime host. It must not replace ENGINEER CORE or redefine engineering result contracts.

The controlling ТЗ is passed to every specialist, including FINAL_AUDIT. Prior specialist results are read-only context for subsequent specialists.


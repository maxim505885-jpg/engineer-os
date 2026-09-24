# ENGINEER OS — Safe developer workflow

This document defines the intended development loop for ENGINEER OS.

## Roles

| Component | Responsibility |
|---|---|
| ChatGPT | Architecture, task decomposition, engineering methodology, review and final decision support |
| Claude Code | Repository implementation, tests, diagnostics and reviewable Git changes |
| Context7 | Current third-party developer documentation |
| GitHub | Source control, branches, commits, PRs and CI |
| ENGINEER OS | Engineering domain logic, evidence, validation and FINAL_AUDIT |

## Standard loop

```text
Task
  ↓
Architecture / acceptance criteria
  ↓
Task branch
  ↓
Repository inspection
  ↓
Context7 documentation check (when needed)
  ↓
Minimal implementation
  ↓
Targeted tests
  ↓
Broader verification
  ↓
Diff + contract review
  ↓
Pull Request
  ↓
Human review
  ↓
Explicit merge
```

## Non-negotiable boundary

Developer tooling may help write or verify code, but it must not become an engineering authority.

The engineering core must continue to own:
- evidence;
- claims;
- traceability;
- calculations;
- normative verification;
- uncertainty handling;
- RED TEAM;
- FINAL_AUDIT.

## Change policy

Documentation-only and developer-tooling changes should be isolated from application behavior whenever possible.

Runtime/application changes require:
- a clear reason;
- a task-specific branch;
- relevant tests;
- an inspectable diff;
- explicit review before merge.

## Failure policy

If verification cannot be completed, report the exact missing verification.

Do not replace a missing test with a claim that the code is correct.
Do not hide uncertainty.

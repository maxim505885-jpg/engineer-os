# Runtime architecture

ENGINEER OS now exposes one runtime boundary with selectable backends:

- **Hermes**: agent loop, sessions, memory, skills, subagents, MCP and provider orchestration.
- **Codex**: execution, sandbox, terminal, files and app-server.
- **ENGINEER CORE**: engineering semantics, evidence, status rules and FINAL_AUDIT.

`EngineeringRuntimeRouter` selects a backend by policy. This is an infrastructure
choice only; it cannot alter engineering status semantics.

The first production policy is intentionally explicit:
`RuntimePolicy(backend="hermes")` or `RuntimePolicy(backend="codex")`.
No automatic fallback between agent runtimes is enabled yet, because a runtime failure
must not silently change the provenance of an engineering result.

The existing Codex app-server adapter remains the Codex implementation. The Hermes
adapter remains subprocess-based and does not import Hermes internals.

Next: add a shared result validator, then connect the router to the existing TaskWorker
and model policy without changing `main`.

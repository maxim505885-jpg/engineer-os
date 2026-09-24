# Hermes integration

ENGINEER OS uses Hermes through a small runtime adapter instead of copying Hermes internals.

## Boundary

- Hermes: sessions, memory, skills, subagents, MCP, scheduling and provider runtime.
- Codex: execution backend for terminal, files, sandbox and app-server where selected.
- ENGINEER CORE: engineering contracts, evidence semantics, planning, specialist skills and FINAL_AUDIT.
- Supabase: durable metadata/task state. Engineering files remain in storage.

## Runtime flow

ENGINEER CORE -> HermesRuntimeAdapter -> Hermes -z -> skill/tool execution -> AgentResult -> ENGINEER CORE -> FINAL_AUDIT.

The adapter uses Hermes' documented non-interactive oneshot interface and deliberately does not import Hermes private Python modules. This keeps the integration replaceable when Hermes changes.

## Safety boundary

The adapter never promotes UNCERTAINTY, invents evidence, or decides engineering correctness. ENGINEER CORE remains the authority for status semantics and FINAL_AUDIT.

## Next stages

1. Connect Hermes session/project identity to ENGINEER OS metadata.
2. Route selected Hermes toolsets to ENGINEER OS MCP servers.
3. Add a Codex execution provider behind the same runtime boundary.
4. Connect the existing local ModelGateway/Ollama provider policy.
5. Build the desktop shell around the Hermes session layer.

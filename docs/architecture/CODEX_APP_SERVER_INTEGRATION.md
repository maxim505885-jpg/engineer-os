# Codex App Server integration boundary

Status: design-validated, implementation intentionally deferred until a local runtime smoke test is available.

## Purpose

ENGINEER OS may use the user's `maxim505885-jpg/codex` repository as an execution runtime. Codex remains an external runtime; its source is not vendored into ENGINEER OS.

## Verified Codex boundary

The Codex repository exposes:

- `codex-rs/app-server` — JSON-RPC application server.
- `codex-rs/app-server-protocol` — versioned RPC protocol.
- `codex-rs/app-server-transport` — stdio/WebSocket/other transports.
- v2 thread/turn APIs, including `thread/start` and `turn/start`.
- `turn/start` supports structured `input`, working-directory overrides, model selection, additional context, and an optional output schema.

The stdio transport is newline-delimited JSON-RPC. It performs the `initialize` handshake and then exchanges JSON-RPC messages over stdin/stdout.

## ENGINEER OS ownership

ENGINEER OS remains authoritative for:

1. engineering task planning;
2. evidence and document intelligence;
3. engineering statuses and uncertainty;
4. normative verification;
5. calculation/model verification;
6. result validation;
7. cross-agent conflicts;
8. FINAL_AUDIT.

Codex must not become the source of engineering truth.

## Adapter boundary

The eventual adapter should expose only a small ENGINEER OS runtime contract:

```
SpecialistTask
    -> Codex execution request
    -> Codex response/events
    -> normalized AgentResult
    -> ENGINEER OS Result Validator
```

The adapter should not expose Codex internals to ENGINEER CORE.

## Safety rules

- `main` remains untouched.
- No Codex source is copied into ENGINEER OS.
- No paid API key is required by the architecture.
- No automatic merge.
- No change to engineering semantics merely to fit Codex.
- The first executable test must be read-only and local.
- A failed/missing Codex runtime must produce UNCERTAINTY/ERROR through the existing runtime contract, not silently fall back to an invented result.

## Next implementation gate

Before implementing the adapter, run one local Codex App Server smoke test:

1. start the user's Codex App Server;
2. send `initialize`;
3. start a minimal thread;
4. start a read-only turn;
5. capture the complete response/notification sequence;
6. only then implement the smallest client matching the observed protocol.

This gate is deliberate: it prevents ENGINEER OS from depending on assumptions about the current Codex CLI transport or event sequence.

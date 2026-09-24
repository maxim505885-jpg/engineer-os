# ENGINEER OS — Open WebUI Integration Boundary

## Decision

Open WebUI is an integration shell, not the engineering source of truth.

It may provide:
- desktop/web user interface;
- model/provider selection;
- document ingestion and retrieval;
- MCP/tool presentation;
- general memory and conversation features;
- Google Drive file selection where configured.

ENGINEER OS retains:
- engineering task contracts;
- evidence and provenance semantics;
- PROJECT/ACTUAL/MEASURED/TESTED/CALCULATED/ASSUMED/INTERPRETED/UNKNOWN classification;
- engineering statuses;
- specialist skills;
- normative verification;
- calculation verification;
- report audit;
- FINAL_AUDIT;
- engineering conclusions.

Hermes remains the general agent/runtime layer. Codex remains an execution backend. The EngineeringRuntimeRouter remains the stable boundary.

## Non-goals

Do not copy Open WebUI internals into ENGINEER OS merely to reproduce UI/RAG/memory features.

Do not make Open WebUI responsible for engineering conclusions.

Do not silently switch runtime backends.

Do not treat retrieved text as engineering evidence until it is bound to an ENGINEER OS material/evidence identity.

## Target flow

Open WebUI/Desktop
→ ENGINEER OS task/session adapter
→ EngineeringRuntimeRouter
→ Hermes or Codex
→ Result Validator
→ ENGINEER CORE
→ FINAL_AUDIT
→ durable task/audit state

Large source files remain in external file storage. Supabase stores task state, metadata, relationships, provenance and audit state.

## Integration rule

The adapter must be transport-oriented and configurable. It must not hard-code an Open WebUI deployment URL, authentication secret, model, storage provider or paid API.

The first production integration should use an OpenAI-compatible endpoint or another explicitly documented Open WebUI interface, with endpoint/auth supplied by runtime configuration.

## Current implementation status

This document records the boundary only. A concrete Open WebUI client must be implemented only after its exact deployed API contract is verified. This avoids building against inferred endpoint names or unstable internal modules.

## License

Before copying Open WebUI source into ENGINEER OS, review the exact license and branding obligations of the current Open WebUI revision. Prefer integration as a separate component/dependency where practical.

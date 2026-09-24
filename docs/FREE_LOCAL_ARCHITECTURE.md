# ENGINEER OS — Free/Local Runtime Architecture

## Goal

ENGINEER OS must not require a paid LLM API. Paid providers may be added later, but they are optional adapters.

## Boundary

The engineering core should depend on a provider-neutral ModelGateway, not directly on Codex/OpenAI/Ollama.

Architecture:

    Task Engine -> Agent/Skill -> ModelGateway -> Ollama (local)
                                             -> llama.cpp (future)
                                             -> optional remote provider (future)

## Cost policy

FREE_ONLY means the configured provider list contains only local/free providers. The gateway must never silently introduce a paid fallback.

## Engineering truth

LLM output is not engineering evidence. Evidence comes from source documents, measurements, tests, calculations, and explicitly classified assumptions. Model output must pass validation, traceability, RED TEAM and FINAL_AUDIT.

## Large documents

Do not send entire reports blindly to an LLM. Target pipeline:

    source file -> document parser -> pages/sections/tables -> evidence -> claims -> agents -> FINAL_AUDIT

Docling is a planned document-ingestion adapter and remains separate from the model gateway.

## Migration

Codex remains supported as an optional runtime during migration. It must not be required by engineering logic or free-mode tests.

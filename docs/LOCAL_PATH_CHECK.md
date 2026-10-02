# Local execution and recovery check — 2026-10-02

Branch: `codex/local-path-check-20261002`, based on `hardening/openwebui-runtime` at `fec8a2a`.

The local execution implementation exists on this runtime branch. These fixes have not been merged into `main` or the V4 document diagnostics branch.

## Changes

- Save RUNNING before invoking the runtime. If that save fails, do not invoke the model and leave the in-memory task queued.
- Clear the previous result and state when explicitly retrying a failed or interrupted task.
- Restore the planned agent requests when reopening saved tasks, and validate the restored results through the core collector.
- Fail the Open WebUI smoke check for errors, incomplete results or acceptance claims from its fixture without verified materials. Transport success does not establish engineering acceptance.
- Default the Windows launcher to the local `qwen3:8b` model. Explicit model overrides still apply.

## Verification

`python -m unittest discover -s tests`: 75 tests passed.

`python scripts/local_lifecycle_check.py docs/local_lifecycle_receipt.json`: six checks passed using an actual loopback HTTP server with synthetic model responses. This exercises the Open WebUI client and adapter, persisted queue, worker execution, reopened plan/results/status, interrupted RUNNING persistence and explicit retry.

`git diff --check`: passed.

The generated receipt is [local_lifecycle_receipt.json](local_lifecycle_receipt.json). The lifecycle checker uses temporary storage and requires no model download or API key.

## Remaining work

- Test the real Windows launcher, installed Open WebUI and Ollama/qwen instance. They were not available in this test environment.
- Integrate the runtime with the stricter evidence and acceptance gates from the modern core. This branch's legacy core can accept results without verified evidence; these recovery fixes do not resolve that production blocker.
- Verify or implement the local browser task/history flow. The existing web frontend depends on Supabase; this check does not establish a complete independent local UI.
- Add durable history across repeated attempts if required. The current store retains the current run, and retry clears the previous in-memory result.
- Resolve V4 document extraction separately using verified source regions. These changes neither rerun Docling nor remove the PDF BLOCK.

The verified scope is local execution and persistence with synthetic HTTP responses, not complete product readiness or engineering acceptance.

# Security policy

ENGINEER OS is a local-first engineering application.

## Reporting a vulnerability

Do not publish credentials, OAuth tokens, private engineering documents, or exploit details in a public issue.

Repository owner: @maxim505885-jpg.

When reporting a security problem, describe:
- affected commit or release;
- affected component;
- expected versus observed behavior;
- whether secrets, local files, evidence, acceptance state, or project isolation may be affected.

Never include real client documents, passwords, API keys, OAuth refresh tokens, cookies, or private URLs.

## Security invariants

- secrets and OAuth credentials are never committed;
- the local app binds only to 127.0.0.1;
- model output cannot grant engineering acceptance;
- BLOCK/UNCERTAINTY cannot be bypassed by UI or provider changes;
- accepted state requires a fresh FINAL AUDIT and upstream gates;
- remembered context is NOT_EVIDENCE in a new task;
- original engineering files are preserved; derived files are separate.

Security fixes must preserve fail-closed behavior.

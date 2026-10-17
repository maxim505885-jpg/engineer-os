# ENGINEER OS product context

## Platform
Web application with an optional Windows desktop shell. Primary user: engineer reviewing building-inspection sources and reports locally.

## User-approved direction
On16.10.2026 the user supplied the existing SPU platform and approved reusing both its interface and Electron application. Preserve the ENGINEER OS engineering methodology,authenticated backend,originals and checks. Source SPU and its working data remain unchanged. No automatic migration or acceptance of historical SPU results.

## Workflows and truth
Project workspaces contain sources,ToR,Evidence candidates,normative/calculation packets,CAD/IFC tasks,case snapshots,audit,memory and draft reports. Source review,engineering acceptance and model output are distinct. Loaded sessions are workspaces,not automatically verified physical objects. Models and missing data never fabricate measurements or normative conclusions.

## Stack
Existing Python/SQLite/authenticated loopback API and vanilla JS UI; user-supplied Electron shell. Reuse existing runtime services and task queue; no second Flask backend. No automatic paid service or network font activation.

## Current constraints
Stage2 is deferred by user. Preserve previous implementation and tests. Desktop packaging and historical data import require their own verified outcomes; local shell operation is not a release claim.

# Engineering stream integration plan

**Goal:** combine candidate fce4367 and engineering stream 99ca7db into one reviewable tree without weakening evidence or replacing the candidate/main prematurely.

**Architecture:** merge both histories in integration/engineering-streams-20261009. Keep the candidate layout and browser gates; keep engineering source, solver-integrity and conclusion controls. Use one bounded backup engine that reads both existing archive schemas. Canonical numbering remains the candidate's19-point plan, with explicit mapping from17.

**Constraints:** free local mode, no fabricated engineering acceptance, solver and physical Windows deferred; original data preserved; no main/candidate merge in this task.

## Tasks

- [x] Resolve9 merge conflicts; preserve status presentation, source coordinates, full ToR input and model controls.
- [x] Demonstrate incompatible backup interfaces, then consolidate APIs and verify legacy archive restore, missing-key limitation, tamper refusal, no-replace and all-table counts.
- [x] Replace conflicting master-plan numbering with one19-point ledger and retain17-point history. Report Generator remains partial: draft export is implemented, accepted publication/images/templates remain open.
- [x] Run Python, Node, architecture/security, compile, DOM and real Chromium on the stable merged tree; fix reproducible regressions with focused tests.
- [x] Fresh independent review of merge decisions, then publish a draft PR against the candidate and synchronize map.

## Review focus

Legacy archives must remain usable without inventing an issuer key; unknown archive members and traversal must fail closed. Migration recovery must precede schema writes. Candidate accessibility/responsive styles must survive. Conclusion pending edits/stale basis must survive. Report and case acceptance must not be inferred from tests or draft export.

## Decisions and evidence

Use19 canonical numbers because the official candidate already uses them; preserve17 mapping. Native solver and physical Windows remain explicitly deferred. An early test process overlapped the merge and is not valid baseline evidence; only final stable-tree runs count.

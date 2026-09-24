# ENGINEER OS — Claude Code operating contract

## Mission

Claude Code is an implementation and verification executor for ENGINEER OS. It may inspect the repository, edit code, run tests, diagnose implementation failures, and prepare reviewable Git changes.

Claude Code is NOT the source of engineering truth. Engineering methodology, evidence rules, normative conclusions, calculation conclusions, and FINAL_AUDIT remain governed by ENGINEER OS.

## Mandatory order before coding

1. Read `AGENTS.md`.
2. Inspect the relevant architecture and existing implementation.
3. Identify the smallest change that satisfies the task.
4. If a third-party library/API/SDK/CLI/MCP contract is involved, consult the project's Context7 source/docs before writing integration code when available.
5. Check the current branch and working tree.
6. Never work directly on `main` unless explicitly authorized.

## Safety rules

- Never modify `main` for an implementation task unless the user explicitly authorizes it.
- Prefer a dedicated task branch.
- Do not merge pull requests unless explicitly requested.
- Do not rewrite unrelated files.
- Do not replace working architecture with a new framework merely because it is available.
- Do not copy external repositories wholesale into ENGINEER OS.
- Do not add paid services, API keys, or recurring dependencies without explicit approval.
- Never commit secrets, tokens, passwords, private keys, or credentials.
- Never weaken evidence, validation, traceability, or FINAL_AUDIT contracts to make tests pass.
- If the requested change conflicts with an ENGINEER OS safety/engineering contract, stop and report the conflict.

## Context7 rule

Use Context7 as a developer documentation source for current third-party library/API/SDK/CLI/MCP usage.

Context7 is NOT authoritative for:
- engineering facts;
- inspection findings;
- normative requirements;
- structural calculations;
- safety conclusions;
- report acceptance;
- FINAL_AUDIT.

When Context7 documentation conflicts with the actual installed version or repository constraints, verify the installed dependency/version and report the discrepancy instead of guessing.

## Implementation discipline

Before editing:
- locate the relevant module;
- understand its callers and tests;
- identify public contracts;
- check whether the behavior already exists;
- avoid duplicate abstractions.

After editing:
1. Run the narrowest relevant tests.
2. Run broader tests when practical.
3. Inspect the final diff.
4. Check for accidental unrelated changes.
5. Check for secrets or hard-coded credentials.
6. Report exactly what was changed and what was verified.

## Engineering integrity

Never invent:
- measurements;
- defects;
- causes;
- calculations;
- normative clauses;
- test results;
- model results;
- evidence;
- conclusions.

Preserve:
PROJECT / ACTUAL / MEASURED / TESTED / CALCULATED / ASSUMED / INTERPRETED / UNKNOWN.

Preserve:
PASS / ACCEPTED / ACCEPTED_ALTERNATIVE / WARNING / UNCERTAINTY / ERROR / BLOCK.

Do not convert UNKNOWN, ASSUMED, or INTERPRETED into facts without evidence.

## Git discipline

Use small, reviewable commits.

Commit messages should describe the actual change.

Before presenting the result:
- provide branch name;
- provide commit SHA(s);
- provide tests/checks actually run;
- state any unverified items;
- provide the PR when one is created.

Never claim tests or CI passed unless their actual result was observed.

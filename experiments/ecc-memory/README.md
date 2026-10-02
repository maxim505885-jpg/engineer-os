# ECC memory and context monitor: isolated ENGINEER OS experiment

Date: 2026-10-02. Upstream: affaan-m/ECC, clean commit `ef648e01899ba3e8dc6371642deaaf64b4477775`. ECC is MIT licensed; upstream code is executed from its checkout, not copied into ENGINEER OS.

## Result

62 synthetic checks passed:

- 27 upstream in-memory source-integrity negative/boundary checks.
- 24 upstream real CLI/local stdio MCP checks on disposable synthetic vaults.
- 4 checks of ENGINEER OS's existing memory/result-contract boundary.
- 7 checks of ECC's exported context-monitor functions.

The existing ENGINEER OS unit suite also passed: 163 tests. `receipt.json` contains the execution timestamps, Node version, upstream file SHA-256 values and individual results. Ajv 8.20.0 was installed in a separate temporary dependency directory with install scripts disabled. No ECC plugin, hook or production backend was installed.

The CLI/MCP example demonstrates durable records across process restart, isolated project roots, explicit user-scope opt-in, configured host attribution, target filtering, rejection of spoofed identity and trust promotion. The three host labels `codex`, `claude`, `hermes` are synthetic MCP configurations; no native app sessions were used.

All ECC records retain `trust: unreviewed`. An example-only verifier checks exact source bytes against a separate synthetic catalog; it is not an automatic core memory verifier, author authentication or engineering acceptance. The catalog is process-local, not a permanent source archive. ENGINEER OS keeps memory metadata `NOT_EVIDENCE` even for `CONFIRMED_REFERENCE`; accepting results without evidence IDs are rejected. These checks do not prove that an LLM will resist arbitrary prompt injection or prevent a caller from fabricating an evidence identifier. Registered evidence and the final acceptance gate remain separate responsibilities.

The monitor flags five identical tool+argument hashes in its recent window. Four repeats or five different argument hashes do not trigger this rule. Context remaining at 35%/25% gives warning/critical levels. API-cost warnings can be disabled without disabling loop detection. These are pure-function checks: no live event bridge, warning deduplication, transcript integration or automatic recovery was exercised.

## Adoption decision

1. Keep this experiment separate; do not copy ECC's complete AGENTS.md, global config, MCP list or hooks into ENGINEER OS.
2. Memory is a reasonable candidate for task checkpoints and handoffs through a future adapter to our existing non-evidentiary memory boundary. Keep source documents and evidence IDs in the original registers.
3. Context-monitor logic is useful as diagnostics. Adapt its messages to our authorized autonomous checkpoint workflow: upstream critical-context wording asks for another user decision and forbids autonomous handoff unless requested. Do not import that policy verbatim.
4. Codex's provided ECC native hook file contains a SessionStart bootstrap, not the Claude PostToolUse monitor. Merely installing the plugin does not establish live monitoring in our current runtime. A supported tool-event source is needed first.
5. Native Windows remains untested here. Upstream documents native Windows memory/observer limitations; verify the exact user environment before relying on a production vault. No WSL requirement is imposed by this experiment.
6. Do not activate automatic instincts for engineering facts. Keep any learned development habits separate from validated normative/calculation evidence.
7. Preserve ENGINEER OS acceptance gates. This experiment neither changes the 137-page V4 extraction queue nor removes BLOCK.

## Reproduce

Requires Python, Git, Node and the clean pinned ECC checkout. No model or paid API is needed. `run_probe.py` checks the upstream commit, clean tree and Ajv version before execution; it executes reviewed upstream source, so do not substitute another checkout or modify the pin casually.

Example in a disposable Linux workspace (the tested platform):

```bash
git clone https://github.com/affaan-m/ECC.git ecc-probe-source
git -C ecc-probe-source checkout --detach ef648e01899ba3e8dc6371642deaaf64b4477775
npm install --ignore-scripts --no-audit --no-fund --prefix ./ecc-probe-deps ajv@8.20.0
python experiments/ecc-memory/run_probe.py ./ecc-probe-source ./ecc-probe-deps/node_modules ./ecc-probe-receipt.json
```

The runner forwards only PATH, NODE_PATH and essential Windows OS variables to subprocesses. Source examples use disposable synthetic memory roots and remove them after the run. Package manifest hashes are recorded, but the receipt is not a dependency-security audit or a proof of identical transitive dependencies; dependency installation must be reviewed separately for deployment.

No real documents, account credentials, OAuth, production database, external model or live harness were used. The probe does not register ECC output as ENGINEER OS evidence or alter production code.

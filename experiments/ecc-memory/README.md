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

## Opt-in ENGINEER OS read adapter

`engineering/memory/ecc_memory_adapter.py` now provides `ECCMemoryAdapter` through the existing `ExternalMemoryAdapter` interface. It does not install ECC, run shell commands, write memory, register evidence or change acceptance status. No default runtime enables it.

The host supplies two callbacks bound to the same authorized vault:

```python
adapter = ECCMemoryAdapter(
    search_transport,       # query -> ECC search response
    read_transport,         # (memory_id, scope) -> ECC read response
    harness="codex",
    scopes=("project", "team"),
)
context = memory_context(adapter.search("checkpoint"))
```

Search summaries are validated before full-body reads. The adapter rejects unknown schema/fields, promoted trust, inactive records, disallowed scopes/targets, invalid identifiers/timestamps/control characters, excessive sizes, duplicate IDs, changed read metadata, failed reads and diagnostic reports of invalid/symlink/truncated scans. A single bad entry rejects the whole batch; no partial result or excerpt fallback is returned. User-scope recall is deliberately unavailable in this adapter.

Returned records always have `UNVERIFIED` trust. Their context locator contains scope, claimed originating harness, ECC ID and exact body SHA-256; this is a context-integrity locator, not an evidence reference, proof of authorship, or verification of the body against an external source. ECC records do not contain a project identity that authenticates the callback's selected vault: project partition isolation is the host's responsibility. Callbacks must not silently change vaults or accept client-selected paths/credentials.

There is no transaction spanning search and read. Matching metadata detects ordinary record changes; body SHA-256 binds the bytes actually read, not an earlier body snapshot. No automatic trust promotion, factual freshness claim, model instruction execution or output caching occurs.

Fresh validation: **173 ENGINEER OS unit tests passed**, including 10 adapter tests. The separate real CLI probe passed **6 checks**: shared/target visibility, full Cyrillic body, non-evidentiary context, reproducibility across subprocesses, body digest and whole-recall rejection after an invalid file was added to the synthetic vault. See `adapter-receipt.json`.

Reproduce the real CLI adapter check without Ajv/MCP dependencies:

```bash
python experiments/ecc-memory/check_adapter_cli.py ./ecc-probe-source ./adapter-receipt.json
```

The disposable fixture is removed after execution. Only Linux was tested. Production callbacks, native Windows, live MCP/app integration, authenticated identities and persistent task checkpoint writes remain unconfigured. Search + one full read per result also has a per-record I/O cost; evaluate vault size before deploying rather than adding an unverified cache.

## Explicit CLI connection and Windows smoke runner

`engineering/memory/ecc_cli_transport.py` binds the callbacks to a local, clean ECC checkout at the reviewed commit. `ECCCLITransport(ecc_checkout, project).adapter()` uses a vault at `<project>/.engineer-os/ecc-memory`; an alternate vault must resolve inside that project and cannot be the project root itself. Project/team scopes are explicit; user recall is unavailable. Checkout path and Node/Git executable selection are trusted operator configuration, not memory-record fields.

The transport only invokes ECC search/read, with argument arrays and `shell=False`, a 30-second subprocess timeout and response validation. Ambient credentials, HOME, USERPROFILE, NODE_OPTIONS and NODE_PATH are not inherited; only PATH, essential OS/temp variables and explicit ECC partition variables are forwarded. Responses exceeding 1 MiB are rejected after collection; this is not an OS-enforced process-memory limit. Git revision/clean-tree checks are performed on construction, not an authentication or filesystem-race guarantee. Keep the operator-owned checkout immutable during a recall session. Search/read does not create or populate working memory.

`scripts/local_ecc_memory_recall.py` provides an explicit recall command and emits only a `NOT_EVIDENCE` envelope. An empty vault returns empty context, never acceptance. Failure returns code 2 with BLOCK and no raw backend error text. There is no automatic inclusion in prompts, chat, evidence or final audit.

`scripts/test_ecc_memory_windows.ps1` checks the project's existing virtualenv, Node and Git; if necessary it clones ECC into the sibling `engineer-os-ecc-runtime` directory and checks out the reviewed commit. It never resets or switches an existing checkout. The probe creates only disposable synthetic vault records and writes a diagnostic report to `.engineer-os/ecc-memory-windows-check.json`. No npm dependency or model/API is needed for this CLI-only test. If an earlier download leaves an unusable checkout, supply a fresh directory explicitly with `-ECCCheckout`; the script will not overwrite it.

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$HOME\engineer-os\scripts\test_ecc_memory_windows.ps1"
```

Latest local validation: **178 unit tests passed**; the **6 real CLI scenarios** now exercise the actual production read transport. The explicit recall script was checked against an empty synthetic project vault and produced `NOT_EVIDENCE` with zero records. The receipt records platform, Node version and execution time. PowerShell/native Windows execution is still pending; no Windows PASS is claimed from Linux results. The next user input is the generated Windows diagnostic JSON, before enabling persistent working memory.

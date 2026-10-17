# SPU interface and desktop reuse implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans inline; the user approved reuse of both supplied UI and desktop application.

**Goal:** Adapt the supplied SPU workspace and Electron application to existing ENGINEER OS APIs and checks.
**Architecture:** Reuse supplied layout, palette, hero asset, navigation and desktop window/tray/state components. Keep the existing authenticated Python backend and forms; publish existing loaded state to a small UI adapter, never add a duplicate Flask backend. Desktop launches only its own backend on port0, verifies a bounded startup descriptor against /api/build, and stops only its own process.
**Tech Stack:** Existing HTML/CSS/classic JS, Python3.12+, supplied Electron33.4.11 for local qualification only; no package download or deployment.
**Spec:** docs/design/spu-reuse-integration-20261016.md

## Global Constraints

- Source SPU code/database/installers remain unchanged. No automatic source DB migration or trusted import.
- Existing token/origin/CSP/source/job/verification gates remain. No external fonts or paid service activation.
- Default data directory selection reuses ENGINEER OS rules. Busy existing data is rejected, never forcibly unlocked.
- No fake project counts/acceptance; session workspaces are not verified physical objects.
- One existing backend, one desktop owner; no blind connection to busy8765.

## Review Focus

- Hostile titles and paths remain inert; no source HTML inline-handler compatibility bypass.
- Old-project replies cannot repopulate dashboard/chat; unsaved forms survive polls.
- Foreign local HTTP responder cannot masquerade as owned backend or receive requests.
- Electron IPC/navigation/download boundaries reject untrusted senders and schemes.
- Test startup/exit never changes original SPU or another running application's data/process.

### Task1: Reuse workspace shell

**Files:** create local_app/ui/spu-shell.js,spu-shell.css,spu-bg-building.jpg; modify index.html/app.js/server.py; create e2e/local_spu_shell_ui_smoke.cjs.
**Interfaces:** existing api,sessions,switchSession,refresh and snapshots; emits engineer-sessions/engineer-workspace events with current source data, plus cached state for late listeners.
- [x] RED browser requires SPU header/hero/project cards and real empty/populated counts.
- [x] Adapt supplied components/styles and hero asset with SHA provenance; retain existing DOM form IDs and listeners. Center sources/forms,chat to the right; mobile stacks normally. Navigation opens existing real panels and supports keyboard.
- [x] GREEN browser empty/project create/select/upload/counts/hostile title/draft polling/session changes and desktop/mobile overflow.
- [x] Run existing DOM and core browser workflows; commit independently testable shell.

### Task2: Reuse Electron application

**Files:** create desktop/main.js,preload.js,splash.html,server-owner.cjs,package.json,README.md,icons; scripts/launch_spu_desktop.py,Open_ENGINEER_OS_SPU.cmd; modify scripts/run_local_app.py; tests/desktop_owner.test.cjs and tests/test_spu_desktop.py.
**Interfaces:** --desktop-ready prints bounded JSON ready descriptor from owned Python server; Node owner verifies origin/build/data identity with existing authenticated routes. CLI --python/--project-dir/--data-dir/--state-dir/--self-test allow explicit independent test profile.
- [x] RED tests fail for missing descriptor/owner; reject foreign origin/build,invalid JSON/oversize stdout and exited process.
- [x] Adapt SPU window/tray/state/preload/splash to verified ENGINEER OS backend. No source Flask server or SPU DB copied. Use safe sender/origin and HTTP(S) external URL checks.
- [x] GREEN owner tests and real supplied Electron self-test with separate state/data,real page,preload,window-state and owned-child termination; preserve foreign busy local server.
- [x] Offline launcher finds explicit/supplied installed Electron and uses pinned project Python; no npm install/download. Document developer runtime versus qualified installer.

### Task3: Final integration verification

- [x] Run focused HTTP/build/desktop tests and existing catalog/CAD/IFC/calculation/conclusion browser scenarios.
- [x] Independent review once for entire change; important findings require RED→GREEN fix.
- [x] Full Windows unittest suite,architecture/repository guards,JS syntax,dependency consistency,diff check. Preserve failures and skips.
- [x] Update map/reuse manifest/QA; local commit without deployment or replacing user checkout. Standalone packaging and historical data import retain explicit status.

Execution evidence: docs/qa/2026-10-16-spu-core-integration.md. Shell and desktop
are committed together as one reviewable integration; no main-checkout replacement.
Standalone installer/current Electron release qualification are outside this local
integration and remain OPEN.

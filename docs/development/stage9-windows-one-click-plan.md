# Stage 9 - Windows one-click release plan

Goal: one double-click on `Start_ENGINEER_OS.cmd` replaces the manual PowerShell sequence.

## Startup sequence
1. Load local env files without printing secrets.
2. Reuse `.venv` or create it automatically with Python 3.13/3.12+.
3. Install Python dependencies only when requirement hashes changed.
4. Reuse or start Ollama in background.
5. Verify `qwen3:8b`; pull it once if missing.
6. Reuse or start Open WebUI when installed. Open WebUI is optional because the app can talk directly to Ollama.
7. Load Google Drive OAuth env if `.env.google-drive` exists. Drive is not a background process.
8. Start ENGINEER OS on 127.0.0.1:8765. Its durable worker starts inside the same process. If that port is occupied, select another free loopback port, for example `Start_ENGINEER_OS.cmd -Port 18765`; pass the same port to `Stop_ENGINEER_OS.cmd`.
9. Wait for the local ENGINEER OS HTML page and separately verify Ollama readiness; open the browser only after readiness.
10. Write logs and startup state under `.engineer-os`.
11. A second launch reuses healthy services and avoids duplicate app instances.

## Processes that should stay in background
Required: Ollama, ENGINEER OS server + built-in worker.
Optional/reused: Open WebUI.
On-demand only: Docling/OCR, OfficeCLI, extraction jobs, solver bridges. These should not consume RAM continuously.

## Stop behavior
`Stop_ENGINEER_OS.cmd` stops only the ENGINEER OS Python server. Ollama/Open WebUI remain available so the next start is fast.

## Final Windows verification
- cold start;
- second start without duplicates;
- reboot/restart with history preserved;
- Cyrillic, spaces and long paths;
- PDF/DOC/DOCX/XLSX/LIR;
- Drive import if OAuth exists;
- CORE_RUN -> Stage 7 -> FINAL AUDIT;
- expected Naberezhnaya BLOCK remains;
- no secrets in logs;
- no stale lock/process after restart.

Stage 9 closes only after this exact flow is executed on the real Windows PC.

## Evidence update 2026-10-14

The Windows Runtime CI completed a real cold start, recovery of an existing virtual environment with pip removed, startup and stop on alternate port 18765, repeat startup/restart, backup and lock checks, offline PDF viewer, local Ollama browser inference, and four browser workflows. The exact CI head and workflow results are recorded in the current project map. A separate local start/stop smoke on port 18767 also passed. The user's physical reboot, cross-machine data transfer, real-user workflow, and optional Open WebUI service remain unverified; this stage stays PARTIAL.

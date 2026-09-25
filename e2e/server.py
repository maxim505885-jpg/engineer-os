from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from engineering.core import EngineerRunner
from engineering.core.engineer_core import EngineerCore
from engineering.core.codex_runtime import CodexAppServerClient, CodexRuntimeAdapter, CodexServerConfig
from engineering.core.supabase_acceptance_gate import production_acceptance_gate


class Handler(BaseHTTPRequestHandler):
    def _json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path == "/health":
            self._json(200, {"status": "ok", "service": "engineer-os-runtime"})
            return
        self._json(404, {"error": "not_found"})

    def do_POST(self) -> None:
        if self.path != "/e2e":
            self._json(404, {"error": "not_found"})
            return
        if os.environ.get("ENGINEER_OS_E2E_ENABLED") != "true":
            self._json(403, {"status": "BLOCK", "reason": "E2E_DISABLED"})
            return

        task_id = os.environ.get("ENGINEER_OS_E2E_TASK_ID")
        if not task_id:
            self._json(500, {"status": "BLOCK", "reason": "E2E_TASK_ID_MISSING"})
            return

        client = CodexAppServerClient(
            CodexServerConfig(
                cwd="/app",
                model=os.environ.get("CODEX_MODEL"),
                sandbox="read-only",
                approval_policy="never",
                timeout_seconds=float(os.environ.get("CODEX_TIMEOUT_SECONDS", "900")),
            )
        )
        try:
            from engineering.core.contracts import EngineerTask, MaterialRef
            task = EngineerTask(
                task_id=task_id,
                tz="ENGINEER OS real runtime E2E smoke test. Do not invent engineering facts.",
                materials=(MaterialRef("e2e-input", "text", "runtime/E2E_INPUT.md"),),
                requested_checks=("report",),
            )
            gate = production_acceptance_gate()
            core = EngineerCore(acceptance_gate=gate)
            summary = EngineerRunner(core).run(task, CodexRuntimeAdapter(client))
            self._json(200, EngineerRunner.summarize(summary))
        except Exception as exc:
            self._json(500, {"status": "ERROR", "error": str(exc)})
        finally:
            client.close()


def main() -> None:
    ThreadingHTTPServer(("0.0.0.0", int(os.environ.get("PORT", "8080"))), Handler).serve_forever()


if __name__ == "__main__":
    main()

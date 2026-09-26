from __future__ import annotations

import hmac
import json
import os
import tempfile
from pathlib import Path
from urllib import parse as urlparse, request as urlrequest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from engineering.core import EngineerRunner
from engineering.core.engineer_core import EngineerCore
from engineering.core.codex_runtime import CodexAppServerClient, CodexRuntimeAdapter, CodexServerConfig
from engineering.core.supabase_acceptance_gate import production_acceptance_gate
from engineering.document_intelligence import DoclingDocumentParser
from engineering.document_intelligence.document_registration import SourceDocumentIdentity, assert_document_identity
from engineering.document_intelligence.supabase_document_identity import production_document_identity_verifier


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
            try:
                import docling  # noqa: F401
                self._json(200, {"status": "ok", "service": "engineer-os-runtime", "docling": "available"})
            except Exception:
                self._json(503, {"status": "BLOCK", "service": "engineer-os-runtime", "reason": "DOCLING_UNAVAILABLE"})
            return
        if self.path == "/document-intelligence/parse-remote":
            self._run_remote_document_parse()
            return
        if self.path == "/document-intelligence/health":
            try:
                import docling  # noqa: F401
                self._json(200, {"status": "ok", "docling": "available"})
            except Exception:
                self._json(503, {"status": "BLOCK", "reason": "DOCLING_UNAVAILABLE"})
            return
        if self.path == "/e2e" and os.environ.get("ENGINEER_OS_E2E_ALLOW_GET") == "true":
            self._run_e2e()
            return
        self._json(404, {"error": "not_found"})

    def do_POST(self) -> None:
        if self.path == "/document-intelligence/parse":
            self._run_document_parse()
            return
        if self.path != "/e2e":
            self._json(404, {"error": "not_found"})
            return
        self._run_e2e()

    def _run_remote_document_parse(self) -> None:
        if os.environ.get("ENGINEER_OS_DOCUMENT_REMOTE_PARSE_ENABLED") != "true":
            self._json(403, {"status": "BLOCK", "reason": "REMOTE_PARSE_DISABLED"})
            return

        remote_url = os.environ.get("ENGINEER_OS_DOCUMENT_REMOTE_URL", "")
        parsed_url = urlparse.urlparse(remote_url)
        if (
            parsed_url.scheme != "https"
            or not parsed_url.hostname
            or not parsed_url.hostname.endswith(".r2.cloudflarestorage.com")
        ):
            self._json(403, {"status": "BLOCK", "reason": "REMOTE_SOURCE_NOT_ALLOWED"})
            return

        project_id = os.environ.get("ENGINEER_OS_DOCUMENT_REMOTE_PROJECT_ID", "")
        document_id = os.environ.get("ENGINEER_OS_DOCUMENT_REMOTE_DOCUMENT_ID", "")
        source_sha256 = os.environ.get("ENGINEER_OS_DOCUMENT_REMOTE_SHA256", "")
        try:
            identity = SourceDocumentIdentity(project_id, document_id, source_sha256)
            production_document_identity_verifier().verify(identity)
        except Exception as exc:
            self._json(422, {"status": "BLOCK", "reason": type(exc).__name__})
            return

        max_bytes = int(os.environ.get("ENGINEER_OS_DOCUMENT_MAX_BYTES", str(100 * 1024 * 1024)))
        temp_path: str | None = None
        try:
            req = urlrequest.Request(remote_url, method="GET", headers={"User-Agent": "ENGINEER-OS/1"})
            with urlrequest.urlopen(req, timeout=120) as response:
                payload = response.read(max_bytes + 1)
            if len(payload) > max_bytes:
                self._json(413, {"status": "BLOCK", "reason": "REMOTE_DOCUMENT_TOO_LARGE"})
                return
            if not payload.startswith(b"%PDF-"):
                self._json(415, {"status": "BLOCK", "reason": "REMOTE_SOURCE_NOT_PDF"})
                return

            with tempfile.NamedTemporaryFile(prefix="engineer-os-remote-", suffix=".pdf", delete=False) as handle:
                handle.write(payload)
                temp_path = handle.name

            document = DoclingDocumentParser().parse(temp_path)
            assert_document_identity(document.source_sha256, identity)
            pages = {
                page.page_no
                for block in document.blocks
                for page in block.provenance
            }
            self._json(200, {
                "status": "ok",
                "document_id": document_id,
                "project_id": project_id,
                "parser": document.parser,
                "source_sha256": document.source_sha256,
                "bytes": len(payload),
                "blocks": len(document.blocks),
                "pages_with_provenance": len(pages),
            })
        except Exception as exc:
            self._json(422, {"status": "BLOCK", "reason": type(exc).__name__})
        finally:
            if temp_path:
                Path(temp_path).unlink(missing_ok=True)

    def _run_document_parse(self) -> None:
        if os.environ.get("ENGINEER_OS_DOCUMENT_INGEST_ENABLED") != "true":
            self._json(403, {"status": "BLOCK", "reason": "DOCUMENT_INGEST_DISABLED"})
            return

        expected_token = os.environ.get("ENGINEER_OS_DOCUMENT_INGEST_TOKEN", "")
        supplied_token = self.headers.get("Authorization", "")
        if not expected_token or not supplied_token.startswith("Bearer ") or not hmac.compare_digest(
            supplied_token[7:], expected_token
        ):
            self._json(401, {"status": "BLOCK", "reason": "UNAUTHORIZED"})
            return

        if self.headers.get_content_type() != "application/pdf":
            self._json(415, {"status": "BLOCK", "reason": "PDF_REQUIRED"})
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            content_length = 0
        max_bytes = int(os.environ.get("ENGINEER_OS_DOCUMENT_MAX_BYTES", str(100 * 1024 * 1024)))
        if content_length <= 0 or content_length > max_bytes:
            self._json(413, {"status": "BLOCK", "reason": "INVALID_DOCUMENT_SIZE"})
            return

        project_id = self.headers.get("X-Project-ID", "").strip()
        document_id = self.headers.get("X-Document-ID", "").strip()
        source_sha256 = self.headers.get("X-Source-SHA256", "").strip()
        try:
            identity = SourceDocumentIdentity(
                project_id=project_id,
                document_id=document_id,
                source_sha256=source_sha256,
            )
        except ValueError as exc:
            self._json(400, {"status": "BLOCK", "reason": str(exc)})
            return
        if not project_id or not document_id:
            self._json(400, {"status": "BLOCK", "reason": "DOCUMENT_IDENTITY_REQUIRED"})
            return

        temp_path: str | None = None
        try:
            production_document_identity_verifier().verify(identity)
            payload = self.rfile.read(content_length)
            if len(payload) != content_length:
                self._json(400, {"status": "BLOCK", "reason": "INCOMPLETE_DOCUMENT_BODY"})
                return
            with tempfile.NamedTemporaryFile(prefix="engineer-os-", suffix=".pdf", delete=False) as handle:
                handle.write(payload)
                temp_path = handle.name

            document = DoclingDocumentParser().parse(temp_path)
            assert_document_identity(document.source_sha256, identity)
            pages = sorted(
                {
                    page.page_no
                    for block in document.blocks
                    for page in block.provenance
                }
            )
            self._json(
                200,
                {
                    "status": "ok",
                    "document_id": document_id,
                    "project_id": project_id,
                    "parser": document.parser,
                    "source_sha256": document.source_sha256,
                    "blocks": len(document.blocks),
                    "pages_with_provenance": len(pages),
                },
            )
        except Exception as exc:
            self._json(422, {"status": "BLOCK", "reason": type(exc).__name__})
        finally:
            if temp_path:
                Path(temp_path).unlink(missing_ok=True)

    def _run_e2e(self) -> None:
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

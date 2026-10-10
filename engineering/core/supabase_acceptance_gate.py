from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

from .engineer_core import AcceptanceGate, CoreState


@dataclass(frozen=True)
class SupabaseAcceptanceGate:
    """Auditable, fail-closed final acceptance gate.

    The service-role key is read only at runtime and is never included in
    prompts, AgentResult payloads, or logs. This adapter is server-side only.
    """

    supabase_url: str
    service_role_key: str
    timeout_seconds: float = 10.0

    @classmethod
    def from_env(cls) -> "SupabaseAcceptanceGate":
        url = os.environ.get("SUPABASE_URL", "").rstrip("/")
        key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
        if not url or not key:
            raise RuntimeError(
                "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required "
                "for the production acceptance gate"
            )
        return cls(url, key)

    def __call__(self, state: CoreState) -> bool:
        task_id = state.task.task_id
        payload = self._rpc("claim_engineer_os_acceptance_gate", {"p_task_id": task_id})
        return payload.get("status") == "PASS" and payload.get("task_id") == task_id

    def evaluate(self, state: CoreState) -> dict[str, Any]:
        payload = self._rpc(
            "claim_engineer_os_acceptance_gate", {"p_task_id": state.task.task_id}
        )
        return payload

    def _rpc(self, function_name: str, payload: dict[str, Any]) -> dict[str, Any]:
        body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        request = urllib.request.Request(
            f"{self.supabase_url}/rest/v1/rpc/{function_name}",
            data=body,
            method="POST",
            headers={
                "apikey": self.service_role_key,
                "Authorization": f"Bearer {self.service_role_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                raw = response.read().decode("utf-8")
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise RuntimeError("Supabase acceptance gate unavailable") from exc

        try:
            result = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise RuntimeError("Supabase acceptance gate returned invalid JSON") from exc

        if not isinstance(result, dict):
            raise RuntimeError("Supabase acceptance gate returned a non-object response")
        return result


def production_acceptance_gate() -> AcceptanceGate:
    """Build the production fail-closed gate from server-side environment."""
    return SupabaseAcceptanceGate.from_env()

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from engineering.core.contracts import AgentResult, AgentStatus, SpecialistTask
from engineering.core.engineer_core import AgentRuntimeAdapter


class OpenWebUIRuntimeError(RuntimeError):
    """Open WebUI transport or response contract failure."""


@dataclass(frozen=True)
class OpenWebUIExecutionConfig:
    base_url: str = "http://127.0.0.1:8080"
    api_key: str | None = None
    model: str = ""
    timeout_seconds: int = 1800

    @classmethod
    def from_env(cls) -> "OpenWebUIExecutionConfig":
        return cls(
            base_url=os.getenv("ENGINEER_OS_OPEN_WEBUI_URL", "http://127.0.0.1:8080"),
            api_key=os.getenv("ENGINEER_OS_OPEN_WEBUI_API_KEY") or None,
            model=os.getenv("ENGINEER_OS_OPEN_WEBUI_MODEL", ""),
            timeout_seconds=int(os.getenv("ENGINEER_OS_OPEN_WEBUI_TIMEOUT", "1800")),
        )


def _build_prompt(task: SpecialistTask) -> str:
    materials = "\n".join(
        f"- {m.id} | {m.kind} | {m.name} | {m.uri or 'no-uri'}"
        for m in task.inputs
    )
    return (
        "ENGINEER OS specialist task.\n"
        "Never invent facts, measurements, calculations, defects, causes, norms, tests or model results.\n"
        "Use PROJECT/ACTUAL/MEASURED/TESTED/CALCULATED/ASSUMED/INTERPRETED/UNKNOWN.\n"
        "НЕ ВИДНО does not mean НЕТ. Insufficient evidence => UNCERTAINTY.\n"
        "A proven error => ERROR. Missing information preventing reliable continuation => BLOCK.\n"
        "ТЗ is controlling.\n\n"
        f"task_id: {task.task_id}\nagent: {task.agent}\nskill: {task.skill}\npurpose: {task.purpose}\n"
        f"ТЗ:\n{task.tz}\n\nMATERIALS:\n{materials}\n\n"
        "Return ONLY JSON with task_id, agent, status, findings, evidence_ids and message."
    )


def _extract_content(response: dict) -> str:
    try:
        content = response["choices"][0]["message"].get("content")
    except (KeyError, IndexError, TypeError) as exc:
        raise OpenWebUIRuntimeError("Open WebUI returned an invalid chat completion") from exc
    if not isinstance(content, str) or not content.strip():
        raise OpenWebUIRuntimeError("Open WebUI returned empty assistant content")
    return content


def _parse_result(content: str, task: SpecialistTask) -> AgentResult:
    value = content.strip()
    if value.startswith("```"):
        lines = value.splitlines()
        if len(lines) >= 3:
            value = "\n".join(lines[1:-1]).strip()
    try:
        payload = json.loads(value)
    except json.JSONDecodeError as exc:
        raise OpenWebUIRuntimeError("Open WebUI assistant content is not valid JSON") from exc
    if not isinstance(payload, dict):
        raise OpenWebUIRuntimeError("Open WebUI assistant JSON must be an object")
    if payload.get("task_id") != task.task_id or payload.get("agent") != task.agent:
        raise OpenWebUIRuntimeError("Open WebUI returned the wrong task or agent identity")
    try:
        status = AgentStatus(str(payload.get("status")))
    except ValueError as exc:
        raise OpenWebUIRuntimeError("Unknown ENGINEER OS status returned by Open WebUI") from exc
    findings = payload.get("findings", [])
    evidence_ids = payload.get("evidence_ids", [])
    if not isinstance(findings, list) or not isinstance(evidence_ids, list):
        raise OpenWebUIRuntimeError("Open WebUI returned invalid findings/evidence_ids")
    return AgentResult(
        task_id=task.task_id,
        agent=task.agent,
        status=status,
        findings=tuple(x for x in findings if isinstance(x, dict)),
        evidence_ids=tuple(x for x in evidence_ids if isinstance(x, str)),
        message=str(payload["message"]) if payload.get("message") is not None else None,
    )


class OpenWebUIClient:
    """Transport client for Open WebUI's verified /api/chat/completions boundary."""

    def __init__(self, config: OpenWebUIExecutionConfig | None = None, opener: Callable[..., object] | None = None) -> None:
        self.config = config or OpenWebUIExecutionConfig.from_env()
        self.opener = opener or urlopen

    def execute(self, prompt: str) -> dict:
        if not self.config.model:
            raise OpenWebUIRuntimeError("ENGINEER_OS_OPEN_WEBUI_MODEL is not configured")
        url = f"{self.config.base_url.rstrip('/')}/api/chat/completions"
        payload = json.dumps({
            "model": self.config.model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
        }).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        request = Request(url, data=payload, headers=headers, method="POST")
        try:
            with self.opener(request, timeout=self.config.timeout_seconds) as response:
                raw = response.read().decode("utf-8")
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise OpenWebUIRuntimeError(f"Open WebUI HTTP {exc.code}: {detail[:1000]}") from exc
        except URLError as exc:
            raise OpenWebUIRuntimeError(f"Open WebUI connection failed: {exc.reason}") from exc
        try:
            result = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise OpenWebUIRuntimeError("Open WebUI returned non-JSON HTTP response") from exc
        if not isinstance(result, dict):
            raise OpenWebUIRuntimeError("Open WebUI HTTP response must be an object")
        return result


class OpenWebUIRuntimeAdapter(AgentRuntimeAdapter):
    """ENGINEER OS runtime adapter using Open WebUI as the model gateway."""

    def __init__(self, client: OpenWebUIClient | None = None) -> None:
        self.client = client or OpenWebUIClient()
        super().__init__(handlers={})

    def execute(self, planned: list[SpecialistTask]) -> list[AgentResult]:
        results: list[AgentResult] = []
        for task in planned:
            response = self.client.execute(_build_prompt(task))
            results.append(_parse_result(_extract_content(response), task))
        return results
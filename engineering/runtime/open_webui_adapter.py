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
    fallback_models: tuple[str, ...] = ()
    timeout_seconds: int = 1800

    @classmethod
    def from_env(cls) -> "OpenWebUIExecutionConfig":
        return cls(
            base_url=os.getenv("ENGINEER_OS_OPEN_WEBUI_URL", "http://127.0.0.1:8080"),
            api_key=os.getenv("ENGINEER_OS_OPEN_WEBUI_API_KEY") or None,
            model=os.getenv("ENGINEER_OS_OPEN_WEBUI_MODEL", ""),
            fallback_models=tuple(m.strip() for m in os.getenv("ENGINEER_OS_OPEN_WEBUI_FALLBACK_MODELS", "qwen3:8b").split(",") if m.strip()),
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
        "Return ONLY one JSON object. Exact schema: {\"task_id\": string, \"agent\": string, \"status\": \"PASS\"|\"ACCEPTED\"|\"ACCEPTED_ALTERNATIVE\"|\"WARNING\"|\"UNCERTAINTY\"|\"ERROR\"|\"BLOCK\", \"findings\": [], \"evidence_ids\": [], \"message\": string|null}.\\n"
        "IMPORTANT: findings MUST ALWAYS be a JSON ARRAY, never a string. If status is UNCERTAINTY and there is no concrete finding, use findings: [].\\n"
        "Do not return markdown fences, prose, or a bare status word. Repeat the exact task_id and agent values provided above."
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
    # Small, semantics-preserving repair for local models that encode an empty
    # uncertainty finding as the literal status string. The engineering status
    # remains UNCERTAINTY; no engineering fact is invented.
    if isinstance(findings, str) and findings.strip().upper() == status.value:
        findings = []
    if not isinstance(findings, list) or not all(isinstance(x, dict) for x in findings):
        preview = json.dumps(findings, ensure_ascii=False)[:2000]
        raise OpenWebUIRuntimeError(f"Open WebUI returned invalid findings; raw findings={preview}")
    if not isinstance(evidence_ids, list) or not all(isinstance(x, str) and x for x in evidence_ids):
        raise OpenWebUIRuntimeError("Open WebUI returned invalid evidence_ids")
    return AgentResult(
        task_id=task.task_id,
        agent=task.agent,
        status=status,
        findings=tuple(findings),
        evidence_ids=tuple(evidence_ids),
        message=str(payload["message"]) if payload.get("message") is not None else None,
    )


class OpenWebUIClient:
    """Transport client for Open WebUI's verified /api/chat/completions boundary."""

    def __init__(self, config: OpenWebUIExecutionConfig | None = None, opener: Callable[..., object] | None = None) -> None:
        self.config = config or OpenWebUIExecutionConfig.from_env()
        self.opener = opener or urlopen

    def execute(self, prompt: str, model: str | None = None) -> dict:
        if not (model or self.config.model):
            raise OpenWebUIRuntimeError("ENGINEER_OS_OPEN_WEBUI_MODEL is not configured")
        url = f"{self.config.base_url.rstrip('/')}/api/chat/completions"
        payload = json.dumps({
            "model": model or self.config.model,
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
        except ConnectionResetError as exc:
            raise OpenWebUIRuntimeError(
                "Open WebUI closed the connection before returning a response "
                "(Windows WSAECONNRESET/10054). Check the selected model, Open WebUI "
                "server console, and the configured provider connection."
            ) from exc
        except TimeoutError as exc:
            raise OpenWebUIRuntimeError(
                f"Open WebUI request timed out after {self.config.timeout_seconds} seconds"
            ) from exc
        except OSError as exc:
            raise OpenWebUIRuntimeError(f"Open WebUI network error: {exc}") from exc
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
            prompt = _build_prompt(task)
            candidates = []
            for model in (self.client.config.model, *self.client.config.fallback_models):
                if model and model not in candidates:
                    candidates.append(model)
            if not candidates:
                raise OpenWebUIRuntimeError("ENGINEER_OS_OPEN_WEBUI_MODEL is not configured")
            errors = []
            for model in candidates:
                try:
                    response = self.client.execute(prompt, model=model)
                    result = _parse_result(_extract_content(response), task)
                    if model != self.client.config.model:
                        note = f"Runtime model fallback used: {model}."
                        result = AgentResult(
                            task_id=result.task_id,
                            agent=result.agent,
                            status=result.status,
                            findings=result.findings,
                            evidence_ids=result.evidence_ids,
                            message=f"{note} {result.message}" if result.message else note,
                        )
                    results.append(result)
                    break
                except OpenWebUIRuntimeError as exc:
                    errors.append(f"{model}: {exc}")
            else:
                raise OpenWebUIRuntimeError(
                    "All configured Open WebUI models failed: " + " | ".join(errors)
                )
        return results
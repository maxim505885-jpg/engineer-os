from __future__ import annotations

import json
import os
import re
import subprocess
from dataclasses import dataclass
from typing import Callable, Sequence

from engineering.core.contracts import AgentResult, AgentStatus, SpecialistTask
from engineering.core.engineer_core import AgentRuntimeAdapter, AgentHandler


class HermesRuntimeError(RuntimeError):
    pass


@dataclass(frozen=True)
class HermesExecutionConfig:
    executable: str = "hermes"
    model: str | None = None
    provider: str | None = None
    toolsets: tuple[str, ...] = ()
    timeout_seconds: int = 1800
    working_directory: str | None = None


def _extract_json(text: str) -> dict:
    value = text.strip()
    if value.startswith("```"):
        value = re.sub(r"^```(?:json)?\s*", "", value, flags=re.IGNORECASE)
        value = re.sub(r"\s*```$", "", value)
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", value, flags=re.DOTALL)
        if not match:
            raise HermesRuntimeError("Hermes did not return JSON")
        parsed = json.loads(match.group(0))
    if not isinstance(parsed, dict):
        raise HermesRuntimeError("Hermes result must be an object")
    return parsed


def _status(value: object) -> AgentStatus:
    try:
        return AgentStatus(str(value))
    except ValueError as exc:
        raise HermesRuntimeError("Unknown ENGINEER OS status: %r" % (value,)) from exc


def _build_prompt(task: SpecialistTask) -> str:
    materials = "\n".join(
        "- %s | %s | %s | %s" % (m.id, m.kind, m.name, m.uri or "no-uri")
        for m in task.inputs
    )
    return (
        "ENGINEER OS specialist task.\n"
        "Never invent facts, measurements, calculations, defects, causes, norms, tests or model results.\n"
        "Use PROJECT/ACTUAL/MEASURED/TESTED/CALCULATED/ASSUMED/INTERPRETED/UNKNOWN.\n"
        "НЕ ВИДНО does not mean НЕТ. Insufficient evidence => UNCERTAINTY.\n"
        "A proven error => ERROR. Missing information preventing reliable continuation => BLOCK.\n"
        "ТЗ is controlling.\n\n"
        "task_id: %s\nagent: %s\nskill: %s\npurpose: %s\nТЗ:\n%s\n\nMATERIALS:\n%s\n\n"
        "Return ONLY JSON: {\"task_id\":\"%s\",\"agent\":\"%s\",\"status\":\"PASS|ACCEPTED|ACCEPTED_ALTERNATIVE|WARNING|UNCERTAINTY|ERROR|BLOCK\",\"findings\":[],\"evidence_ids\":[],\"message\":\"...\"}."
        % (task.task_id, task.agent, task.skill, task.purpose, task.tz, materials, task.task_id, task.agent)
    )


class HermesSubprocessClient:
    def __init__(self, config: HermesExecutionConfig | None = None, runner: Callable[..., subprocess.CompletedProcess[str]] | None = None):
        self.config = config or HermesExecutionConfig()
        self.runner = runner or subprocess.run

    def execute(self, prompt: str, *, skills: Sequence[str] = ()) -> str:
        command = [self.config.executable, "-z"]
        if self.config.model:
            command += ["--model", self.config.model]
        if self.config.provider:
            command += ["--provider", self.config.provider]
        if self.config.toolsets:
            command += ["--toolsets", ",".join(self.config.toolsets)]
        if skills:
            command += ["--skills", ",".join(skills)]
        command.append(prompt)
        env = os.environ.copy()
        env.setdefault("HERMES_SINGLE_QUERY_SESSION", "1")
        result = self.runner(command, cwd=self.config.working_directory, env=env, text=True, capture_output=True, timeout=self.config.timeout_seconds, check=False)
        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "").strip()
            raise HermesRuntimeError("Hermes exited with code %s%s" % (result.returncode, ": " + detail if detail else ""))
        return result.stdout


class HermesRuntimeAdapter(AgentRuntimeAdapter):
    def __init__(self, client: HermesSubprocessClient | None = None, handler_factory: Callable[[SpecialistTask], AgentHandler] | None = None):
        self.client = client or HermesSubprocessClient()
        self.handler_factory = handler_factory
        super().__init__(handlers={})

    def _handler(self, task: SpecialistTask) -> AgentResult:
        if self.handler_factory is not None:
            return self.handler_factory(task)(task)
        payload = _extract_json(self.client.execute(_build_prompt(task), skills=(task.skill,)))
        if payload.get("task_id") != task.task_id or payload.get("agent") != task.agent:
            raise HermesRuntimeError("Hermes returned the wrong task or agent identity")
        findings = payload.get("findings", [])
        evidence_ids = payload.get("evidence_ids", [])
        if not isinstance(findings, list) or not isinstance(evidence_ids, list):
            raise HermesRuntimeError("Invalid findings/evidence_ids from Hermes")
        return AgentResult(task_id=task.task_id, agent=task.agent, status=_status(payload.get("status")), findings=tuple(x for x in findings if isinstance(x, dict)), evidence_ids=tuple(x for x in evidence_ids if isinstance(x, str)), message=str(payload.get("message")) if payload.get("message") is not None else None)

    def execute(self, planned):
        return [self._handler(task) for task in planned]


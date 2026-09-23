from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from typing import Any

from .contracts import AgentResult, AgentStatus, SpecialistTask
from .engineer_core import AgentRuntimeAdapter


@dataclass(frozen=True)
class CodexServerConfig:
    command: tuple[str, ...] = ("codex-app-server",)
    cwd: str | None = None
    model: str | None = None
    sandbox: str = "read-only"
    approval_policy: str = "never"
    timeout_seconds: float = 900.0


class CodexAppServerClient:
    """Minimal JSONL client for the Codex app-server stdio transport.

    This intentionally depends only on the public app-server JSON protocol.
    The Codex repository is not copied into ENGINEER OS.
    """

    def __init__(self, config: CodexServerConfig = CodexServerConfig()) -> None:
        self.config = config
        self.process: subprocess.Popen[str] | None = None
        self._request_id = 0

    def start(self) -> None:
        if self.process is not None:
            return
        self.process = subprocess.Popen(
            [*self.config.command, "--listen", "stdio://"],
            cwd=self.config.cwd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            env=os.environ.copy(),
        )
        self.request(
            "initialize",
            {
                "clientInfo": {
                    "name": "engineer-os",
                    "version": "0.1.0",
                },
                "capabilities": {"experimentalApi": False},
            },
        )

    def close(self) -> None:
        if self.process is not None:
            self.process.terminate()
            self.process = None

    def request(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        if self.process is None or self.process.stdin is None or self.process.stdout is None:
            raise RuntimeError("Codex app-server is not running")
        self._request_id += 1
        request_id = self._request_id
        self.process.stdin.write(
            json.dumps({"id": request_id, "method": method, "params": params or {}}, ensure_ascii=False)
            + "\n"
        )
        self.process.stdin.flush()

        while True:
            line = self.process.stdout.readline()
            if not line:
                raise RuntimeError("Codex app-server closed its stdio stream")
            message = json.loads(line)
            if message.get("id") != request_id:
                continue
            if "error" in message:
                raise RuntimeError(str(message["error"]))
            return message.get("result", {})

    def execute_specialist(self, task: SpecialistTask) -> AgentResult:
        self.start()
        thread = self.request(
            "thread/start",
            {
                "cwd": self.config.cwd,
                "model": self.config.model,
                "sandbox": self.config.sandbox,
                "approvalPolicy": self.config.approval_policy,
                "baseInstructions": (
                    "You are a specialist inside ENGINEER OS. "
                    "Follow the assigned skill exactly. Do not invent facts, measurements, "
                    "calculations, normative clauses or evidence. Return uncertainty when evidence is insufficient."
                ),
            },
        )
        thread_id = thread.get("thread", {}).get("id") or thread.get("threadId")
        if not thread_id:
            return AgentResult(task.task_id, task.agent, AgentStatus.ERROR, message="Codex did not return a thread id.")

        prompt = (
            f"ENGINEER OS specialist task. Agent: {task.agent}. Skill: {task.skill}. "
            f"Purpose: {task.purpose}. Task ID: {task.task_id}. "
            "Execute only this specialist responsibility and report evidence-linked findings. "
            "If the supplied materials are insufficient, use UNCERTAINTY or BLOCK; never invent missing data."
        )
        turn = self.request(
            "turn/start",
            {
                "threadId": thread_id,
                "input": [{"type": "text", "text": prompt}],
                "sandboxPolicy": {"type": "readOnly"},
            },
        )
        return AgentResult(
            task.task_id,
            task.agent,
            AgentStatus.ACCEPTED,
            findings=({"codex_thread_id": thread_id, "turn": turn},),
            message="Codex turn started; specialist execution is delegated to app-server.",
        )


class CodexRuntimeAdapter(AgentRuntimeAdapter):
    """ENGINEER OS adapter backed by a real Codex app-server process."""

    def __init__(self, client: CodexAppServerClient) -> None:
        super().__init__()
        self.client = client

    def execute(self, planned):
        results = []
        for task in planned:
            try:
                results.append(self.client.execute_specialist(task))
            except Exception as exc:
                results.append(
                    AgentResult(
                        task.task_id,
                        task.agent,
                        AgentStatus.ERROR,
                        message=f"Codex runtime error: {exc}",
                    )
                )
        return results

from __future__ import annotations

import json
from typing import Any

from .contracts import AgentResult, AgentStatus, SpecialistTask


class CodexResultParser:
    """Validates strict JSON specialist output without inventing engineering data."""

    REQUIRED_KEYS = {"status", "findings", "evidence_ids", "message"}

    @classmethod
    def parse(
        cls,
        task: SpecialistTask,
        raw_text: str,
        *,
        thread_id: str | None = None,
        turn_id: str | None = None,
    ) -> AgentResult:
        try:
            payload = json.loads(raw_text)
        except (json.JSONDecodeError, TypeError):
            return cls._uncertainty(task, "Codex returned non-JSON specialist output.", raw_text, thread_id, turn_id)

        if not isinstance(payload, dict):
            return cls._uncertainty(task, "Codex result must be a JSON object.", raw_text, thread_id, turn_id)

        missing = cls.REQUIRED_KEYS - payload.keys()
        if missing:
            return cls._uncertainty(task, f"Codex result is missing fields: {sorted(missing)}.", raw_text, thread_id, turn_id)

        try:
            status = AgentStatus(payload["status"])
        except (ValueError, TypeError):
            return cls._uncertainty(task, "Codex returned an invalid agent status.", raw_text, thread_id, turn_id)

        findings = payload["findings"]
        evidence_ids = payload["evidence_ids"]
        message = payload["message"]

        if not isinstance(findings, list) or not all(isinstance(item, dict) for item in findings):
            return cls._uncertainty(task, "findings must be a JSON array of objects.", raw_text, thread_id, turn_id)
        if not isinstance(evidence_ids, list) or not all(isinstance(item, str) for item in evidence_ids):
            return cls._uncertainty(task, "evidence_ids must be a JSON array of strings.", raw_text, thread_id, turn_id)
        if message is not None and not isinstance(message, str):
            return cls._uncertainty(task, "message must be a string or null.", raw_text, thread_id, turn_id)

        return AgentResult(
            task.task_id,
            task.agent,
            status,
            findings=tuple(findings),
            evidence_ids=tuple(evidence_ids),
            message=message,
        )

    @staticmethod
    def _uncertainty(
        task: SpecialistTask,
        reason: str,
        raw_text: str,
        thread_id: str | None,
        turn_id: str | None,
    ) -> AgentResult:
        metadata: dict[str, Any] = {"parser_reason": reason, "raw_text": raw_text}
        if thread_id:
            metadata["codex_thread_id"] = thread_id
        if turn_id:
            metadata["codex_turn_id"] = turn_id
        return AgentResult(
            task.task_id,
            task.agent,
            AgentStatus.UNCERTAINTY,
            findings=(metadata,),
            message=reason,
        )

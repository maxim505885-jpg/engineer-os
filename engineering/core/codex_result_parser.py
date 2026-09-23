from __future__ import annotations

import json
from typing import Any

from .contracts import AgentResult, AgentStatus, SpecialistTask


class CodexResultParser:
    """Validates strict JSON specialist output without inventing engineering data."""

    REQUIRED_KEYS = {"status", "findings", "evidence_ids", "message"}
    FINDING_REQUIRED_KEYS = {"observation", "evidence_ids", "basis", "certainty", "conclusion"}

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
        if not isinstance(evidence_ids, list) or not all(isinstance(item, str) and item.strip() for item in evidence_ids):
            return cls._uncertainty(task, "evidence_ids must be a JSON array of non-empty strings.", raw_text, thread_id, turn_id)
        if len(set(evidence_ids)) != len(evidence_ids):
            return cls._uncertainty(task, "evidence_ids must not contain duplicates.", raw_text, thread_id, turn_id)
        supplied_ids = {material.id for material in task.inputs}
        unknown_evidence = sorted(set(evidence_ids) - supplied_ids)
        if unknown_evidence:
            return cls._uncertainty(
                task,
                f"evidence_ids reference materials not supplied to this specialist: {unknown_evidence}.",
                raw_text,
                thread_id,
                turn_id,
            )
        if findings and not evidence_ids:
            return cls._uncertainty(task, "Findings require at least one evidence_id.", raw_text, thread_id, turn_id)

        for index, finding in enumerate(findings):
            missing_finding = cls.FINDING_REQUIRED_KEYS - finding.keys()
            if missing_finding:
                return cls._uncertainty(
                    task,
                    f"finding[{index}] is missing fields: {sorted(missing_finding)}.",
                    raw_text,
                    thread_id,
                    turn_id,
                )
            for key in ("observation", "basis", "certainty", "conclusion"):
                if not isinstance(finding[key], str) or not finding[key].strip():
                    return cls._uncertainty(
                        task,
                        f"finding[{index}].{key} must be a non-empty string.",
                        raw_text,
                        thread_id,
                        turn_id,
                    )
            finding_evidence = finding["evidence_ids"]
            if (
                not isinstance(finding_evidence, list)
                or not all(isinstance(item, str) and item.strip() for item in finding_evidence)
                or not finding_evidence
            ):
                return cls._uncertainty(
                    task,
                    f"finding[{index}].evidence_ids must be a non-empty array of strings.",
                    raw_text,
                    thread_id,
                    turn_id,
                )
            if len(set(finding_evidence)) != len(finding_evidence):
                return cls._uncertainty(
                    task,
                    f"finding[{index}].evidence_ids must not contain duplicates.",
                    raw_text,
                    thread_id,
                    turn_id,
                )
            unknown_finding_evidence = sorted(set(finding_evidence) - supplied_ids)
            if unknown_finding_evidence:
                return cls._uncertainty(
                    task,
                    f"finding[{index}].evidence_ids reference materials not supplied to this specialist: {unknown_finding_evidence}.",
                    raw_text,
                    thread_id,
                    turn_id,
                )
            if not set(finding_evidence).issubset(set(evidence_ids)):
                return cls._uncertainty(
                    task,
                    f"finding[{index}].evidence_ids must be included in top-level evidence_ids.",
                    raw_text,
                    thread_id,
                    turn_id,
                )

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

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .contracts import AgentResult, AgentStatus, EngineerTask, MaterialRef
from .task_engine import TaskRecord, TaskStatus


class TaskStore:
    """Small durable JSON store for Task Engine state.

    This is intentionally a file-backed metadata store. Large engineering
    materials remain external; the store keeps task metadata, references and
    audit/runtime state only.
    """

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def save(self, records: tuple[TaskRecord, ...] | list[TaskRecord]) -> None:
        payload = {"version": 1, "tasks": [self._record_to_dict(r) for r in records]}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self.path)

    def load(self) -> list[TaskRecord]:
        if not self.path.exists():
            return []
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        if payload.get("version") != 1:
            raise ValueError("Unsupported task store version")
        return [self._record_from_dict(item) for item in payload.get("tasks", [])]

    @staticmethod
    def _task_to_dict(task: EngineerTask) -> dict[str, Any]:
        return {
            "task_id": task.task_id,
            "tz": task.tz,
            "materials": [
                {"id": m.id, "kind": m.kind, "name": m.name, "uri": m.uri}
                for m in task.materials
            ],
            "requested_checks": list(task.requested_checks),
            "metadata": task.metadata,
        }

    @classmethod
    def _record_to_dict(cls, record: TaskRecord) -> dict[str, Any]:
        return {
            "task": cls._task_to_dict(record.task),
            "status": record.status.value,
            "result_status": record.result_status.value if record.result_status else None,
            "error": record.error,
            "created_at": record.created_at,
            "started_at": record.started_at,
            "finished_at": record.finished_at,
            "state": cls._state_to_dict(record.state),
        }

    @staticmethod
    def _state_to_dict(state: Any) -> dict[str, Any] | None:
        if state is None:
            return None
        return {
            "results": [r.as_dict() for r in state.results],
            "planned": [
                {
                    "task_id": p.task_id,
                    "agent": p.agent,
                    "skill": p.skill,
                    "purpose": p.purpose,
                    "tz": p.tz,
                    "inputs": [
                        {"id": m.id, "kind": m.kind, "name": m.name, "uri": m.uri}
                        for m in p.inputs
                    ],
                }
                for p in state.planned
            ],
        }

    @classmethod
    def _record_from_dict(cls, item: dict[str, Any]) -> TaskRecord:
        raw_task = item["task"]
        materials = tuple(
            MaterialRef(m["id"], m["kind"], m["name"], m.get("uri"))
            for m in raw_task.get("materials", [])
        )
        task = EngineerTask(
            task_id=raw_task["task_id"],
            tz=raw_task["tz"],
            materials=materials,
            requested_checks=tuple(raw_task.get("requested_checks", [])),
            metadata=dict(raw_task.get("metadata", {})),
        )
        result_status = item.get("result_status")
        record = TaskRecord(
            task=task,
            status=TaskStatus(item["status"]),
            result_status=AgentStatus(result_status) if result_status else None,
            error=item.get("error"),
            created_at=item.get("created_at") or "",
            started_at=item.get("started_at"),
            finished_at=item.get("finished_at"),
        )
        # Rehydrate agent results. Planned tasks are rebuilt from the current
        # ENGINEER CORE plan so persisted state remains compatible with code.
        state_raw = item.get("state")
        if state_raw is not None:
            from .engineer_core import CoreState
            core_state = CoreState(task=task, planned=[], results=[])
            for raw in state_raw.get("results", []):
                core_state.results.append(
                    AgentResult(
                        task_id=raw["task_id"],
                        agent=raw["agent"],
                        status=AgentStatus(raw["status"]),
                        findings=tuple(raw.get("findings", [])),
                        evidence_ids=tuple(raw.get("evidence_ids", [])),
                        message=raw.get("message"),
                    )
                )
            # Planned entries are metadata only on reload; TaskEngine can plan
            # again when executing a queued task.
            record.state = core_state
        return record

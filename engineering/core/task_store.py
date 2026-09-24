from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .contracts import AgentResult, AgentStatus, EngineerTask, MaterialRef
from .task_engine import TaskRecord, TaskStatus


@dataclass(frozen=True)
class ProjectRecord:
    project_id: str
    name: str
    metadata: dict[str, Any]


@dataclass(frozen=True)
class MaterialRecord:
    material_id: str
    project_id: str | None
    kind: str
    name: str
    uri: str | None


@dataclass(frozen=True)
class RunRecord:
    run_id: str
    task_id: str
    status: str
    result_status: str | None
    started_at: str | None
    finished_at: str | None
    error: str | None




class TaskStore:
    """Normalized local metadata store.

    The JSON document is split into project/material/task/run collections.
    Engineering files themselves are never embedded; only references are kept.
    The format is intentionally simple so a database adapter can replace it.
    """

    VERSION = 2

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def save(self, records: tuple[TaskRecord, ...] | list[TaskRecord]) -> None:
        projects: dict[str, ProjectRecord] = {}
        materials: dict[str, MaterialRecord] = {}
        tasks: list[dict[str, Any]] = []
        runs: list[dict[str, Any]] = []

        for record in records:
            task = record.task
            project_id = str(task.metadata.get("project_id", "")) or None
            project_name = str(task.metadata.get("project_name", project_id or ""))
            if project_id:
                projects[project_id] = ProjectRecord(
                    project_id=project_id,
                    name=project_name,
                    metadata=dict(task.metadata),
                )

            for material in task.materials:
                materials[material.id] = MaterialRecord(
                    material_id=material.id,
                    project_id=project_id,
                    kind=material.kind,
                    name=material.name,
                    uri=material.uri,
                )

            tasks.append(self._task_to_dict(record))
            runs.append(self._run_to_dict(record))

        payload = {
            "version": self.VERSION,
            "projects": [asdict(v) for v in projects.values()],
            "materials": [asdict(v) for v in materials.values()],
            "tasks": tasks,
            "runs": runs,
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        tmp.replace(self.path)

    def load(self) -> list[TaskRecord]:
        if not self.path.exists():
            return []
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        version = payload.get("version", 1)
        if version == 1:
            return self._load_v1(payload)
        if version != self.VERSION:
            raise ValueError(f"Unsupported task store version: {version}")
        return [self._record_from_dict(item) for item in payload.get("tasks", [])]

    def list_projects(self) -> list[ProjectRecord]:
        payload = self._read()
        if payload.get("version") != self.VERSION:
            return []
        return [ProjectRecord(**item) for item in payload.get("projects", [])]

    def list_materials(self) -> list[MaterialRecord]:
        payload = self._read()
        if payload.get("version") != self.VERSION:
            return []
        return [MaterialRecord(**item) for item in payload.get("materials", [])]

    def list_runs(self) -> list[RunRecord]:
        payload = self._read()
        if payload.get("version") != self.VERSION:
            return []
        return [RunRecord(**item) for item in payload.get("runs", [])]

    def _read(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"version": self.VERSION}
        return json.loads(self.path.read_text(encoding="utf-8"))

    @staticmethod
    def _task_to_dict(record: TaskRecord) -> dict[str, Any]:
        return {
            "task": {
                "task_id": record.task.task_id,
                "tz": record.task.tz,
                "materials": [
                    {
                        "id": m.id,
                        "kind": m.kind,
                        "name": m.name,
                        "uri": m.uri,
                    }
                    for m in record.task.materials
                ],
                "requested_checks": list(record.task.requested_checks),
                "metadata": record.task.metadata,
            },
            "status": record.status.value,
            "result_status": (
                record.result_status.value if record.result_status else None
            ),
            "error": record.error,
            "created_at": record.created_at,
            "started_at": record.started_at,
            "finished_at": record.finished_at,
            "state": TaskStore._state_to_dict(record.state),
        }

    @staticmethod
    def _run_to_dict(record: TaskRecord) -> dict[str, Any]:
        return asdict(
            RunRecord(
                run_id=f"{record.task.task_id}:{record.started_at or 'pending'}",
                task_id=record.task.task_id,
                status=record.status.value,
                result_status=(
                    record.result_status.value if record.result_status else None
                ),
                started_at=record.started_at,
                finished_at=record.finished_at,
                error=record.error,
            )
        )

    @staticmethod
    def _state_to_dict(state: Any) -> dict[str, Any] | None:
        if state is None:
            return None
        return {"results": [r.as_dict() for r in state.results]}

    @staticmethod
    def _load_v1(payload: dict[str, Any]) -> list[TaskRecord]:
        # Backward compatibility with the first JSON prototype.
        return [TaskStore._record_from_dict(item) for item in payload.get("tasks", [])]

    @staticmethod
    def _record_from_dict(item: dict[str, Any]) -> TaskRecord:
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
            record.state = core_state
        return record

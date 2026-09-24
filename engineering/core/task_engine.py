from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from .contracts import AgentStatus, EngineerTask
from .engineer_core import AgentRuntimeAdapter, CoreState, EngineerCore
from .storage_protocol import TaskRepository


class TaskStatus(str, Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"


@dataclass
class TaskRecord:
    task: EngineerTask
    status: TaskStatus = TaskStatus.QUEUED
    state: CoreState | None = None
    result_status: AgentStatus | None = None
    error: str | None = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    started_at: str | None = None
    finished_at: str | None = None


class TaskEngine:
    """Deterministic task queue around ENGINEER CORE.

    The engine owns task lifecycle only. Engineering conclusions remain the
    responsibility of ENGINEER CORE and its runtime; no task state is inferred
    from missing or incomplete evidence.
    """

    def __init__(
        self,
        core: EngineerCore | None = None,
        store: TaskRepository | None = None,
    ) -> None:
        self.core = core or EngineerCore()
        self.store = store
        self._tasks: dict[str, TaskRecord] = {}
        if self.store is not None:
            for record in self.store.load():
                if record.task.task_id in self._tasks:
                    raise ValueError(f"Duplicate persisted task: {record.task.task_id}")
                self._tasks[record.task.task_id] = record

    def _persist(self) -> None:
        if self.store is not None:
            self.store.save(list(self._tasks.values()))

    def submit(self, task: EngineerTask) -> TaskRecord:
        if task.task_id in self._tasks:
            raise ValueError(f"Task already exists: {task.task_id}")
        # Validate before accepting work into the queue.
        self.core.plan(task)
        record = TaskRecord(task=task)
        self._tasks[task.task_id] = record
        self._persist()
        return record

    def get(self, task_id: str) -> TaskRecord:
        try:
            return self._tasks[task_id]
        except KeyError as exc:
            raise KeyError(f"Unknown task: {task_id}") from exc

    def list(self) -> tuple[TaskRecord, ...]:
        return tuple(self._tasks.values())

    def requeue(self, task_id: str, reason: str | None = None) -> TaskRecord:
        record = self.get(task_id)
        if record.status not in {TaskStatus.RUNNING, TaskStatus.FAILED}:
            raise ValueError(f"Task {task_id} cannot be requeued from {record.status.value}")
        record.status = TaskStatus.QUEUED
        if reason:
            record.error = reason
        record.started_at = None
        record.finished_at = None
        self._persist()
        return record

    def run_next(self, runtime: AgentRuntimeAdapter) -> TaskRecord | None:
        queued = next((r for r in self._tasks.values() if r.status == TaskStatus.QUEUED), None)
        if queued is None:
            return None
        return self.run(queued.task.task_id, runtime)

    def run(self, task_id: str, runtime: AgentRuntimeAdapter) -> TaskRecord:
        record = self.get(task_id)
        if record.status != TaskStatus.QUEUED:
            raise ValueError(f"Task {task_id} is not QUEUED: {record.status.value}")

        record.status = TaskStatus.RUNNING
        record.started_at = datetime.now(timezone.utc).isoformat()
        try:
            state = self.core.run(record.task, runtime)
            result_status = self.core.final_status(state)
            record.state = state
            record.result_status = result_status
            record.status = self._lifecycle_status(result_status)
            result = self._finish(record)
            self._persist()
            return result
        except Exception as exc:
            record.error = str(exc)
            record.status = TaskStatus.FAILED
            result = self._finish(record)
            self._persist()
            return result

    @staticmethod
    def _lifecycle_status(status: AgentStatus) -> TaskStatus:
        if status == AgentStatus.ACCEPTED or status == AgentStatus.ACCEPTED_ALTERNATIVE or status == AgentStatus.PASS:
            return TaskStatus.COMPLETED
        if status in {AgentStatus.BLOCK}:
            return TaskStatus.BLOCKED
        if status in {AgentStatus.ERROR}:
            return TaskStatus.FAILED
        # WARNING/UNCERTAINTY require human/runtime follow-up and are not
        # represented as completed engineering work.
        return TaskStatus.BLOCKED

    @staticmethod
    def _finish(record: TaskRecord) -> TaskRecord:
        record.finished_at = datetime.now(timezone.utc).isoformat()
        return record

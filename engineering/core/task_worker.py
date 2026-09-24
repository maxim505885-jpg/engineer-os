from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Protocol

from .engineer_core import AgentRuntimeAdapter
from .task_engine import TaskEngine, TaskStatus


class PersistentQueue(Protocol):
    def claim_queue_item(self, stale_after_seconds: int = 900) -> dict | None: ...

    def finish_queue_item(
        self,
        queue_id: str,
        status: str,
        result: dict | None = None,
        blocking_reasons: list[str] | None = None,
        retry: bool = False,
    ) -> dict: ...


@dataclass(frozen=True)
class WorkerConfig:
    poll_interval_seconds: float = 5.0
    max_tasks_per_cycle: int = 1
    stale_after_seconds: int = 900


class TaskWorker:
    """Persistent ENGINEER OS worker backed by the existing Supabase queue.

    Queue claiming is atomic in Postgres (FOR UPDATE SKIP LOCKED). TaskEngine
    remains the lifecycle authority; the queue only owns durable execution
    leasing and completion state.
    """

    def __init__(
        self,
        engine: TaskEngine,
        runtime_factory: Callable[[], AgentRuntimeAdapter],
        config: WorkerConfig | None = None,
        queue: PersistentQueue | None = None,
    ) -> None:
        self.engine = engine
        self.runtime_factory = runtime_factory
        self.queue = queue
        self.config = config or WorkerConfig()
        self._stop = False

    def stop(self) -> None:
        self._stop = True

    def run_once(self) -> int:
        if self.queue is None:
            return self._run_local_once()
        return self._run_persistent_once()

    def _run_local_once(self) -> int:
        record = self.engine.run_next(self.runtime_factory())
        return 0 if record is None else 1

    def _run_persistent_once(self) -> int:
        item = self.queue.claim_queue_item(self.config.stale_after_seconds)
        if item is None:
            return 0

        queue_id = item.get("id")
        task_id = (item.get("payload") or {}).get("engineer_os_task_id")
        if not queue_id or not task_id:
            if queue_id:
                self.queue.finish_queue_item(
                    str(queue_id),
                    "FAILED",
                    blocking_reasons=["Queue payload lacks task identity"],
                )
            return 1

        try:
            record = self.engine.get(str(task_id))
        except KeyError as exc:
            self.queue.finish_queue_item(
                str(queue_id),
                "FAILED",
                blocking_reasons=[str(exc)],
            )
            return 1

        # Idempotency boundary: if the process died after ENGINEER CORE
        # completed but before queue acknowledgement, never execute the
        # engineering task a second time.
        if record.status == TaskStatus.COMPLETED:
            self.queue.finish_queue_item(
                str(queue_id),
                "COMPLETED",
                result={"engineer_os_task_id": str(task_id)},
            )
            return 1
        if record.status == TaskStatus.BLOCKED:
            self.queue.finish_queue_item(
                str(queue_id),
                "BLOCKED",
                blocking_reasons=([record.error] if record.error else []),
            )
            return 1

        if record.status in {TaskStatus.RUNNING, TaskStatus.FAILED}:
            self.engine.requeue(
                str(task_id),
                "Recovered before execution after a stale queue lease.",
            )

        record = self.engine.run(str(task_id), self.runtime_factory())
        result_status = record.result_status.value if record.result_status else None
        queue_status = {
            TaskStatus.COMPLETED: "COMPLETED",
            TaskStatus.BLOCKED: "BLOCKED",
            TaskStatus.FAILED: "FAILED",
        }[record.status]

        retry = (
            record.status == TaskStatus.FAILED
            and int(item.get("attempt_count", 1)) < int(item.get("max_attempts", 1))
        )
        if retry:
            self.engine.requeue(
                str(task_id),
                "Retry scheduled after a runtime failure.",
            )

        self.queue.finish_queue_item(
            str(queue_id),
            queue_status,
            result={
                "engineer_os_task_id": str(task_id),
                "result_status": result_status,
                "error": record.error,
            },
            blocking_reasons=([record.error] if record.error else []),
            retry=retry,
        )
        return 1

    def run_forever(self) -> None:
        while not self._stop:
            processed = self.run_once()
            if processed == 0:
                time.sleep(max(0.1, self.config.poll_interval_seconds))


def recover_stale_running_tasks(engine: TaskEngine) -> int:
    """Recover in-memory tasks left RUNNING by a process restart."""
    recovered = 0
    for record in engine.list():
        if record.status == TaskStatus.RUNNING:
            engine.requeue(
                record.task.task_id,
                "Recovered after worker restart.",
            )
            recovered += 1
    return recovered

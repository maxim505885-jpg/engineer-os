from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable

from .engineer_core import AgentRuntimeAdapter
from .task_engine import TaskEngine, TaskStatus


@dataclass(frozen=True)
class WorkerConfig:
    poll_interval_seconds: float = 5.0
    max_tasks_per_cycle: int = 1


class TaskWorker:
    """Single-worker persistent queue runner.

    The worker is deliberately small: Supabase remains the durable state
    layer, while TaskEngine remains the only lifecycle authority.
    """

    def __init__(
        self,
        engine: TaskEngine,
        runtime_factory: Callable[[], AgentRuntimeAdapter],
        config: WorkerConfig | None = None,
    ) -> None:
        self.engine = engine
        self.runtime_factory = runtime_factory
        self.config = config or WorkerConfig()
        self._stop = False

    def stop(self) -> None:
        self._stop = True

    def run_once(self) -> int:
        processed = 0
        for _ in range(max(1, self.config.max_tasks_per_cycle)):
            record = self.engine.run_next(self.runtime_factory())
            if record is None:
                break
            processed += 1
        return processed

    def run_forever(self) -> None:
        while not self._stop:
            processed = self.run_once()
            if processed == 0:
                time.sleep(max(0.1, self.config.poll_interval_seconds))


def recover_stale_running_tasks(engine: TaskEngine) -> int:
    """Requeue interrupted RUNNING tasks after a worker restart.

    A restart can leave a durable task in RUNNING even though no process owns
    it anymore. Requeueing is explicit and deterministic; completed tasks are
    never reopened.
    """
    recovered = 0
    for record in engine.list():
        if record.status == TaskStatus.RUNNING:
            record.status = TaskStatus.QUEUED
            record.error = (
                "Recovered after worker restart at "
                + datetime.now(timezone.utc).isoformat()
            )
            record.started_at = None
            record.finished_at = None
            recovered += 1
    if recovered:
        engine._persist()
    return recovered

from __future__ import annotations

import os
import uuid

from engineering.core import EngineerTask, MaterialRef, SupabaseTaskStore
from engineering.core.codex_runtime import CodexAppServerClient, CodexRuntimeAdapter
from engineering.core.task_engine import TaskEngine
from engineering.core.task_worker import TaskWorker, WorkerConfig


def main() -> None:
    required = ("SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY", "ENGINEER_OS_OWNER_ID")
    missing = [name for name in required if not os.environ.get(name)]
    if missing:
        raise SystemExit("Missing live E2E configuration: " + ", ".join(missing))

    task_id = "live-e2e-" + uuid.uuid4().hex
    task = EngineerTask(
        task_id=task_id,
        tz="Проверить только наличие входных материалов и корректность маршрута выполнения. Не делать инженерных выводов.",
        materials=(MaterialRef("e2e-material", "text", "live-e2e.txt", "data:text/plain,ENGINEER OS live E2E"),),
        requested_checks=("report",),
        metadata={"title": "ENGINEER OS live E2E", "priority": "LOW"},
    )

    store = SupabaseTaskStore()
    engine = TaskEngine(store=store)
    engine.submit(task)

    client = CodexAppServerClient(
        skill_loader=None,
        # The CI job supplies the checked-out ENGINEER OS root as cwd.
    )
    worker = TaskWorker(
        engine,
        lambda: CodexRuntimeAdapter(client),
        config=WorkerConfig(max_tasks_per_cycle=1, stale_after_seconds=900),
        queue=store,
    )

    try:
        processed = worker.run_once()
        if processed != 1:
            raise RuntimeError("Persistent queue did not yield the E2E task")
        record = engine.get(task_id)
        print(
            {
                "task_id": task_id,
                "status": record.status.value,
                "result_status": record.result_status.value if record.result_status else None,
                "error": record.error,
            }
        )
        if record.status.value == "FAILED":
            raise RuntimeError(record.error or "ENGINEER OS live E2E failed")
    finally:
        client.close()


if __name__ == "__main__":
    main()

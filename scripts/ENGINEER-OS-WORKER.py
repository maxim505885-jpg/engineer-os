from __future__ import annotations

import os

from engineering.core.engineer_core import EngineerCore
from engineering.core.supabase_task_store import SupabaseTaskStore
from engineering.core.task_engine import TaskEngine
from engineering.core.task_worker import TaskWorker, WorkerConfig
from engineering.runtime.factory import build_openwebui_runtime_from_env


def main() -> int:
    required = (
        "SUPABASE_URL",
        "SUPABASE_SERVICE_ROLE_KEY",
        "ENGINEER_OS_OWNER_ID",
        "ENGINEER_OS_OPEN_WEBUI_API_KEY",
    )
    missing = [name for name in required if not os.getenv(name)]
    if missing:
        print("ENGINEER OS persistent worker is not started.")
        print("Missing environment variables: " + ", ".join(missing))
        return 2

    store = SupabaseTaskStore()
    engine = TaskEngine(core=EngineerCore(), store=store)
    worker = TaskWorker(
        engine=engine,
        runtime_factory=build_openwebui_runtime_from_env,
        config=WorkerConfig(poll_interval_seconds=5.0, max_tasks_per_cycle=1),
        queue=store,
    )

    print("ENGINEER OS persistent worker started.")
    print("Queue: Supabase")
    print("Runtime: Open WebUI -> configured model gateway")
    print("Waiting for QUEUED tasks...")

    try:
        worker.run_forever()
    except KeyboardInterrupt:
        worker.stop()
        print("ENGINEER OS persistent worker stopped.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

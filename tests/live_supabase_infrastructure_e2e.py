from __future__ import annotations

import os
import uuid

from engineering.core import (
    AgentResult,
    AgentStatus,
    EngineerTask,
    MaterialRef,
    SupabaseTaskStore,
    TaskEngine,
    TaskWorker,
    WorkerConfig,
)
from engineering.core.engineer_core import AgentRuntimeAdapter


def deterministic_runtime() -> AgentRuntimeAdapter:
    """Deterministic runtime: validates persistence/orchestration, not model quality."""

    def handler(payload):
        evidence = [m.id for m in payload.inputs]
        if payload.agent == "final-audit-agent":
            return AgentResult(
                task_id=payload.task_id,
                agent=payload.agent,
                status=AgentStatus.ACCEPTED,
                findings=(),
                evidence_ids=tuple(evidence),
                message="Deterministic FINAL AUDIT infrastructure check passed.",
            )
        return AgentResult(
            task_id=payload.task_id,
            agent=payload.agent,
            status=AgentStatus.ACCEPTED,
            findings=(),
            evidence_ids=tuple(evidence),
            message=f"Deterministic {payload.agent} infrastructure check passed.",
        )

    return AgentRuntimeAdapter({
        "report-audit-agent": handler,
        "normative-agent": handler,
        "calculation-agent": handler,
        "final-audit-agent": handler,
    })


def main() -> None:
    required = ("SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY", "ENGINEER_OS_OWNER_ID")
    missing = [name for name in required if not os.environ.get(name)]
    if missing:
        raise SystemExit(f"Missing required environment: {', '.join(missing)}")

    task_id = f"live-infra-e2e-{uuid.uuid4().hex}"
    task = EngineerTask(
        task_id=task_id,
        tz="Проверить инженерный отчет по ТЗ и провести FINAL AUDIT.",
        materials=(MaterialRef("live-e2e-material", "report", "synthetic-report.txt"),),
        requested_checks=("report", "normative", "calculation"),
        metadata={"title": "ENGINEER OS live infrastructure E2E"},
    )

    store = SupabaseTaskStore()
    engine = TaskEngine(store=store)
    engine.submit(task)

    worker = TaskWorker(
        engine,
        deterministic_runtime,
        config=WorkerConfig(max_tasks_per_cycle=1),
        queue=store,
    )

    processed = worker.run_once()
    if processed != 1:
        raise AssertionError(f"Expected one processed queue item, got {processed}")

    record = engine.get(task_id)
    if record is None:
        raise AssertionError("Task disappeared from TaskEngine")

    if record.status.value != "COMPLETED":
        raise AssertionError(
            f"Live infrastructure E2E did not complete: "
            f"status={record.status.value}, result={record.result_status}"
        )

    persisted = {r.task.task_id: r for r in store.load()}
    db_record = persisted.get(task_id)
    if db_record is None:
        raise AssertionError("Completed task was not persisted in Supabase")

    if db_record.status.value != "COMPLETED":
        raise AssertionError(
            f"Supabase task status mismatch: {db_record.status.value}"
        )

    print(
        "LIVE SUPABASE INFRASTRUCTURE E2E PASSED: "
        f"{task_id} -> queue -> worker -> task engine -> FINAL AUDIT -> Supabase"
    )


if __name__ == "__main__":
    main()

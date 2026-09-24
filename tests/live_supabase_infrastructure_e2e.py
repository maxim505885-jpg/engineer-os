from __future__ import annotations

import os
import urllib.parse
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

    processed = worker.run_once(task_id=task_id)
    if processed != 1:
        raise AssertionError(f"Expected target queue item to be processed, got {processed}")

    record = engine.get(task_id)
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

    # Verify the exact task's durable execution records, not merely the
    # engineering_tasks lifecycle row.
    task_rows = store._request(
        "GET",
        "/rest/v1/engineering_tasks"
        f"?select=id,provenance,status"
        f"&provenance->>engineer_os_task_id=eq.{urllib.parse.quote(task_id, safe='')}",
    )
    if len(task_rows) != 1:
        raise AssertionError(
            f"Expected exactly one persisted task row for {task_id}, got {len(task_rows)}"
        )

    task_uuid = str(task_rows[0]["id"])

    run_rows = store._request(
        "GET",
        "/rest/v1/engineering_task_runs"
        f"?select=id,status,output_snapshot,validation"
        f"&task_id=eq.{urllib.parse.quote(task_uuid, safe='')}"
        "&order=created_at.desc&limit=1",
    )
    if len(run_rows) != 1:
        raise AssertionError(
            f"Expected exactly one latest task_run for {task_id}, got {len(run_rows)}"
        )

    run_row = run_rows[0]
    if run_row.get("status") != "COMPLETED":
        raise AssertionError(
            f"Task run did not finish COMPLETED: {run_row.get('status')}"
        )

    output = run_row.get("output_snapshot") or {}
    if output.get("engineer_os_task_id") != task_id:
        raise AssertionError("Task run output belongs to a different ENGINEER OS task")
    if output.get("result_status") != AgentStatus.ACCEPTED.value:
        raise AssertionError(
            f"Task run result mismatch: {output.get('result_status')}"
        )

    queue_rows = store._request(
        "GET",
        "/rest/v1/engineering_execution_queue"
        f"?select=id,status,payload,attempt_count"
        f"&task_id=eq.{urllib.parse.quote(task_uuid, safe='')}"
        "&order=created_at.desc&limit=1",
    )
    if len(queue_rows) != 1:
        raise AssertionError(
            f"Expected exactly one latest queue item for {task_id}, got {len(queue_rows)}"
        )

    queue_row = queue_rows[0]
    if queue_row.get("status") != "COMPLETED":
        raise AssertionError(
            f"Queue item did not finish COMPLETED: {queue_row.get('status')}"
        )
    if (queue_row.get("payload") or {}).get("engineer_os_task_id") != task_id:
        raise AssertionError("Queue payload belongs to a different ENGINEER OS task")

    print(
        "LIVE SUPABASE INFRASTRUCTURE E2E PASSED: "
        f"{task_id} -> queue -> worker -> task engine -> FINAL AUDIT -> "
        "task_runs -> queue completion -> Supabase"
    )


if __name__ == "__main__":
    main()

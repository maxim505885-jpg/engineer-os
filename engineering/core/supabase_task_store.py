from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
from datetime import datetime, timezone
import urllib.request
from typing import Any
from uuid import UUID

from .contracts import AgentStatus, EngineerTask, MaterialRef
from .task_engine import TaskRecord, TaskStatus
from .storage_protocol import TaskRepository


class SupabaseTaskStore(TaskRepository):
    """Supabase REST adapter for the ENGINEER OS TaskRepository contract.

    The database is the metadata/state layer. Source engineering files remain
    in their external storage and are represented by MaterialRef URIs.

    Required environment:
      SUPABASE_URL
      SUPABASE_SERVICE_ROLE_KEY
      ENGINEER_OS_OWNER_ID

    The service-role key is read only from the environment and is never stored
    in repository files.
    """

    def __init__(
        self,
        url: str | None = None,
        service_role_key: str | None = None,
        owner_id: str | None = None,
        timeout: float = 20.0,
    ) -> None:
        self.url = (url or os.environ.get("SUPABASE_URL", "")).rstrip("/")
        self.key = service_role_key or os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
        self.owner_id = owner_id or os.environ.get("ENGINEER_OS_OWNER_ID", "")
        self.timeout = timeout
        if not self.url or not self.key or not self.owner_id:
            raise ValueError(
                "SupabaseTaskStore requires SUPABASE_URL, "
                "SUPABASE_SERVICE_ROLE_KEY and ENGINEER_OS_OWNER_ID."
            )

    def save(self, records: tuple[TaskRecord, ...] | list[TaskRecord]) -> None:
        existing = self._request("GET", "/rest/v1/engineering_tasks?select=*")
        by_external_id = {
            row.get("provenance", {}).get("engineer_os_task_id"): row
            for row in existing
            if isinstance(row.get("provenance"), dict)
        }

        for record in records:
            payload = self._task_payload(record)
            row = by_external_id.get(record.task.task_id)
            if row:
                updated = self._request(
                    "PATCH",
                    f"/rest/v1/engineering_tasks?id=eq.{urllib.parse.quote(str(row['id']), safe='')}",
                    payload,
                    prefer="return=representation",
                )
                if not updated:
                    raise RuntimeError(
                        f"Supabase engineering task update matched no rows: {row['id']}"
                    )
            else:
                created = self._request(
                    "POST",
                    "/rest/v1/engineering_tasks",
                    payload,
                    prefer="return=representation",
                )
                if created:
                    self._enqueue_task(created[0], record)



    def _enqueue_task(self, row: dict[str, Any], record: TaskRecord) -> None:
        task_uuid = row.get("id")
        if not self._uuid_or_none(task_uuid):
            raise RuntimeError(
                f"Supabase engineering task has invalid UUID: {task_uuid!r}"
            )
        existing = self._request(
            "GET",
            "/rest/v1/engineering_execution_queue"
            f"?select=id&task_id=eq.{urllib.parse.quote(str(task_uuid), safe='')}"
            "&status=in.(QUEUED,RUNNING)",
        )
        if existing:
            return
        self._request(
            "POST",
            "/rest/v1/engineering_execution_queue",
            {
                "owner_id": self.owner_id,
                "project_id": self._uuid_or_none(record.task.metadata.get("project_id")),
                "task_id": str(task_uuid),
                "priority": record.task.metadata.get("priority", "NORMAL"),
                "payload": {
                    "engineer_os_task_id": record.task.task_id,
                    "requested_checks": list(record.task.requested_checks),
                },
            },
            prefer="return=minimal",
        )

    def claim_queue_item(self, stale_after_seconds: int = 900, task_id: str | None = None) -> dict[str, Any] | None:
        rows = self._request(
            "POST",
            "/rest/v1/rpc/claim_engineering_execution_queue",
            {
                "p_owner_id": self.owner_id,
                "p_stale_after_seconds": stale_after_seconds,
                "p_task_id": str(task_id) if task_id else None,
            },
        )
        return rows[0] if rows else None

    def finish_queue_item(
        self,
        queue_id: str,
        status: str,
        result: dict[str, Any] | None = None,
        blocking_reasons: list[str] | None = None,
        retry: bool = False,
    ) -> dict[str, Any]:
        rows = self._request(
            "POST",
            "/rest/v1/rpc/finish_engineering_execution_queue",
            {
                "p_queue_id": queue_id,
                "p_status": status,
                "p_result": result or {},
                "p_blocking_reasons": blocking_reasons or [],
                "p_retry": retry,
            },
        )
        if not rows:
            raise RuntimeError(f"Supabase queue item disappeared: {queue_id}")
        return rows[0]


    def create_task_run(
        self,
        task_uuid: str,
        input_snapshot: dict[str, Any],
        agent_id: str | None = None,
    ) -> dict[str, Any]:
        payload = {
            "owner_id": self.owner_id,
            "task_id": task_uuid,
            "agent_id": self._uuid_or_none(agent_id),
            "status": "RUNNING",
            "input_snapshot": input_snapshot,
            "output_snapshot": {},
            "validation": {},
            "blocking_reasons": [],
        }
        rows = self._request(
            "POST",
            "/rest/v1/engineering_task_runs",
            payload,
            prefer="return=representation",
        )
        if not rows:
            raise RuntimeError("Supabase did not create engineering_task_runs row")
        return rows[0]

    def finish_task_run(
        self,
        run_uuid: str,
        status: str,
        output_snapshot: dict[str, Any],
        validation: dict[str, Any] | None = None,
        blocking_reasons: list[str] | None = None,
    ) -> dict[str, Any]:
        rows = self._request(
            "PATCH",
            "/rest/v1/engineering_task_runs"
            f"?id=eq.{urllib.parse.quote(run_uuid, safe='')}",
            {
                "status": status,
                "output_snapshot": output_snapshot,
                "validation": validation or {},
                "blocking_reasons": blocking_reasons or [],
                "completed_at": datetime.now(timezone.utc).isoformat(),
            },
            prefer="return=representation",
        )
        if not rows:
            raise RuntimeError(f"Supabase task run disappeared: {run_uuid}")
        return rows[0]
    def load(self) -> list[TaskRecord]:
        rows = self._request(
            "GET",
            "/rest/v1/engineering_tasks?select=*"
            "&provenance->>engineer_os_task_id=not.is.null"
        )
        return [self._record_from_row(row) for row in rows]

    def _task_payload(self, record: TaskRecord) -> dict[str, Any]:
        task = record.task
        metadata = dict(task.metadata)
        project_id = metadata.get("project_id")
        valid_project_id = self._uuid_or_none(project_id)

        status = {
            TaskStatus.QUEUED: "PENDING",
            TaskStatus.RUNNING: "RUNNING",
            TaskStatus.COMPLETED: "COMPLETED",
            TaskStatus.BLOCKED: "BLOCKED",
            TaskStatus.FAILED: "FAILED",
        }[record.status]

        payload: dict[str, Any] = {
            "owner_id": self.owner_id,
            "project_id": valid_project_id,
            "task_type": "ENGINEER_OS",
            "title": metadata.get("title", task.task_id),
            "objective": task.tz,
            "priority": metadata.get("priority", "NORMAL"),
            "status": status,
            "input_refs": [
                {
                    "id": m.id,
                    "kind": m.kind,
                    "name": m.name,
                    "uri": m.uri,
                }
                for m in task.materials
            ],
            "output_refs": [],
            "prerequisites": list(task.requested_checks),
            "blocking_reasons": self._blocking_reasons(record),
            "next_actions": [],
            "provenance": {
                **metadata,
                "engineer_os_task_id": task.task_id,
                "engineer_os_result_status": (
                    record.result_status.value if record.result_status else None
                ),
                "engineer_os_error": record.error,
            },
            "created_at": record.created_at,
            "started_at": record.started_at,
            "completed_at": record.finished_at,
        }
        return payload

    @staticmethod
    def _blocking_reasons(record: TaskRecord) -> list[str]:
        if record.error:
            return [record.error]
        if record.result_status in {AgentStatus.UNCERTAINTY, AgentStatus.WARNING}:
            return [record.result_status.value]
        return []

    @staticmethod
    def _record_from_row(row: dict[str, Any]) -> TaskRecord:
        provenance = row.get("provenance") or {}
        inputs = row.get("input_refs") or []
        materials = tuple(
            MaterialRef(
                str(m["id"]),
                str(m.get("kind", "unknown")),
                str(m.get("name", m["id"])),
                m.get("uri"),
            )
            for m in inputs
        )
        result_value = provenance.get("engineer_os_result_status")
        result_status = AgentStatus(result_value) if result_value else None

        status_map = {
            "PENDING": TaskStatus.QUEUED,
            "RUNNING": TaskStatus.RUNNING,
            "COMPLETED": TaskStatus.COMPLETED,
            "BLOCKED": TaskStatus.BLOCKED,
            "FAILED": TaskStatus.FAILED,
        }
        status = status_map.get(row.get("status"), TaskStatus.BLOCKED)

        task = EngineerTask(
            task_id=str(provenance["engineer_os_task_id"]),
            tz=str(row.get("objective") or ""),
            materials=materials,
            requested_checks=tuple(row.get("prerequisites") or []),
            metadata={
                k: v
                for k, v in provenance.items()
                if k not in {
                    "engineer_os_task_id",
                    "engineer_os_result_status",
                    "engineer_os_error",
                }
            },
        )
        return TaskRecord(
            task=task,
            status=status,
            result_status=result_status,
            error=provenance.get("engineer_os_error"),
            created_at=row.get("created_at") or "",
            started_at=row.get("started_at"),
            finished_at=row.get("completed_at"),
        )

    def _request(
        self,
        method: str,
        path: str,
        body: dict[str, Any] | None = None,
        prefer: str | None = None,
    ) -> list[dict[str, Any]]:
        headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
        }
        if prefer:
            headers["Prefer"] = prefer

        data = json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None
        request = urllib.request.Request(
            f"{self.url}{path}",
            data=data,
            headers=headers,
            method=method,
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                raw = response.read().decode("utf-8")
                if not raw:
                    return []
                value = json.loads(raw)
                return value if isinstance(value, list) else [value]
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Supabase request failed ({exc.code}): {detail}") from exc

    @staticmethod
    def _uuid_or_none(value: Any) -> str | None:
        if value in (None, ""):
            return None
        try:
            return str(UUID(str(value)))
        except ValueError:
            return None

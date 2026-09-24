import unittest
from unittest.mock import Mock

from engineering.core import (
    AgentResult,
    AgentStatus,
    EngineerTask,
    MaterialRef,
    TaskWorker,
    WorkerConfig,
    recover_stale_running_tasks,
)
from engineering.core.engineer_core import AgentRuntimeAdapter
from engineering.core.task_engine import TaskEngine, TaskRecord, TaskStatus


class FakeQueue:
    def __init__(self, item):
        self.item = item
        self.finished = []

    def claim_queue_item(self, stale_after_seconds=900):
        item, self.item = self.item, None
        return item

    def finish_queue_item(self, queue_id, status, result=None, blocking_reasons=None, retry=False):
        self.finished.append((queue_id, status, result, blocking_reasons, retry))
        return {"id": queue_id, "status": status}


class WorkerTests(unittest.TestCase):
    def make_task(self, task_id="task-1"):
        return EngineerTask(
            task_id=task_id,
            tz="Проверить отчет по ТЗ.",
            materials=(MaterialRef("report-1", "report", "report.docx"),),
            requested_checks=("report",),
        )

    def accepted_runtime(self):
        handler = lambda p: AgentResult(p.task_id, p.agent, AgentStatus.ACCEPTED)
        return AgentRuntimeAdapter({
            "report-audit-agent": handler,
            "final-audit-agent": handler,
        })

    def test_empty_queue_does_not_execute(self):
        engine = TaskEngine()
        factory = Mock()
        worker = TaskWorker(engine, factory, WorkerConfig(poll_interval_seconds=0.1))
        self.assertEqual(worker.run_once(), 0)
        factory.assert_not_called()

    def test_persistent_queue_executes_and_acks(self):
        engine = TaskEngine()
        engine.submit(self.make_task())
        queue = FakeQueue({
            "id": "queue-1",
            "attempt_count": 1,
            "max_attempts": 3,
            "payload": {"engineer_os_task_id": "task-1"},
        })
        worker = TaskWorker(
            engine,
            self.accepted_runtime,
            config=WorkerConfig(),
            queue=queue,
        )

        self.assertEqual(worker.run_once(), 1)
        self.assertEqual(engine.get("task-1").status, TaskStatus.COMPLETED)
        self.assertEqual(queue.finished[0][0], "queue-1")
        self.assertEqual(queue.finished[0][1], "COMPLETED")
        self.assertFalse(queue.finished[0][4])

    def test_persistent_infrastructure_path_can_finish_without_codex_model(self):
        engine = TaskEngine()
        engine.submit(self.make_task("infra-1"))

        queue = FakeQueue({
            "id": "queue-infra-1",
            "attempt_count": 1,
            "max_attempts": 1,
            "payload": {"engineer_os_task_id": "infra-1"},
        })

        calls = []

        def deterministic_runtime():
            calls.append("runtime")
            return self.accepted_runtime()

        worker = TaskWorker(
            engine,
            deterministic_runtime,
            config=WorkerConfig(),
            queue=queue,
        )

        self.assertEqual(worker.run_once(), 1)
        record = engine.get("infra-1")
        self.assertEqual(record.status, TaskStatus.COMPLETED)
        self.assertEqual(record.result_status, AgentStatus.ACCEPTED)
        self.assertEqual(calls, ["runtime"])
        self.assertEqual(queue.finished[0][1], "COMPLETED")


    def test_worker_accepts_unified_runtime_router(self):
        from engineering.runtime.router import EngineeringRuntimeRouter, RuntimePolicy

        engine = TaskEngine()
        engine.submit(self.make_task("router-1"))
        queue = FakeQueue({
            "id": "queue-router-1",
            "attempt_count": 1,
            "max_attempts": 1,
            "payload": {"engineer_os_task_id": "router-1"},
        })

        runtime = EngineeringRuntimeRouter(RuntimePolicy("hermes"), hermes=self.accepted_runtime())
        worker = TaskWorker(engine, lambda: runtime, config=WorkerConfig(), queue=queue)

        self.assertEqual(worker.run_once(), 1)
        record = engine.get("router-1")
        self.assertEqual(record.status, TaskStatus.COMPLETED)
        self.assertEqual(record.result_status, AgentStatus.ACCEPTED)
        self.assertEqual(queue.finished[0][1], "COMPLETED")

    def test_stale_running_task_is_requeued(self):
        engine = TaskEngine()
        record = TaskRecord(task=self.make_task("stale-1"))
        record.status = TaskStatus.RUNNING
        engine._tasks["stale-1"] = record

        self.assertEqual(recover_stale_running_tasks(engine), 1)
        self.assertEqual(record.status, TaskStatus.QUEUED)
        self.assertIsNotNone(record.error)
        self.assertIsNone(record.started_at)
        self.assertIsNone(record.finished_at)


if __name__ == "__main__":
    unittest.main()

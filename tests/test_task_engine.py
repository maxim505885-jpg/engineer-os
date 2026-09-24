import unittest

from engineering.core import AgentResult, AgentStatus, EngineerTask, MaterialRef
from engineering.core.engineer_core import AgentRuntimeAdapter
from engineering.core.task_engine import TaskEngine, TaskStatus


class TaskEngineTests(unittest.TestCase):
    def make_task(self, task_id="task-1"):
        return EngineerTask(
            task_id=task_id,
            tz="Проверить отчет по ТЗ.",
            materials=(MaterialRef("report-1", "report", "report.docx"),),
            requested_checks=("report",),
        )

    def accepted_runtime(self):
        def handler(planned):
            if planned.agent == "final-audit-agent":
                return AgentResult(planned.task_id, planned.agent, AgentStatus.ACCEPTED)
            return AgentResult(planned.task_id, planned.agent, AgentStatus.ACCEPTED)
        return AgentRuntimeAdapter({
            "report-audit-agent": handler,
            "final-audit-agent": handler,
        })

    def test_submit_queues_task_and_rejects_duplicate(self):
        engine = TaskEngine()
        record = engine.submit(self.make_task())
        self.assertEqual(record.status, TaskStatus.QUEUED)
        with self.assertRaises(ValueError):
            engine.submit(self.make_task())

    def test_run_lifecycle_completes_accepted_task(self):
        engine = TaskEngine()
        engine.submit(self.make_task())
        record = engine.run_next(self.accepted_runtime())
        self.assertEqual(record.status, TaskStatus.COMPLETED)
        self.assertEqual(record.result_status, AgentStatus.ACCEPTED)
        self.assertIsNotNone(record.started_at)
        self.assertIsNotNone(record.finished_at)

    def test_uncertainty_blocks_completion(self):
        engine = TaskEngine()
        engine.submit(self.make_task())
        runtime = AgentRuntimeAdapter({
            "report-audit-agent": lambda p: AgentResult(
                p.task_id, p.agent, AgentStatus.UNCERTAINTY
            ),
            "final-audit-agent": lambda p: AgentResult(
                p.task_id, p.agent, AgentStatus.ACCEPTED
            ),
        })
        record = engine.run_next(runtime)
        self.assertEqual(record.status, TaskStatus.BLOCKED)
        self.assertEqual(record.result_status, AgentStatus.UNCERTAINTY)

    def test_runtime_exception_fails_task(self):
        engine = TaskEngine()
        engine.submit(self.make_task())
        runtime = AgentRuntimeAdapter({
            "report-audit-agent": lambda p: (_ for _ in ()).throw(RuntimeError("runtime failure")),
            "final-audit-agent": lambda p: AgentResult(p.task_id, p.agent, AgentStatus.ACCEPTED),
        })
        record = engine.run_next(runtime)
        self.assertEqual(record.status, TaskStatus.FAILED)
        self.assertEqual(record.error, "runtime failure")


if __name__ == "__main__":
    unittest.main()

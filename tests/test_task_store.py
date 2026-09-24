import tempfile
import unittest
from pathlib import Path

from engineering.core import AgentResult, AgentStatus, EngineerTask, MaterialRef, TaskStore
from engineering.core.task_engine import TaskEngine, TaskStatus
from engineering.core.engineer_core import AgentRuntimeAdapter


class TaskStoreTests(unittest.TestCase):
    def task(self):
        return EngineerTask(
            task_id="persist-1",
            tz="Проверить отчет по ТЗ.",
            materials=(MaterialRef("report-1", "report", "report.docx", "file://report.docx"),),
            requested_checks=("report",),
            metadata={"project": "demo"},
        )

    def test_queued_task_survives_restart(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "tasks.json"
            engine = TaskEngine()
            engine.submit(self.task())
            TaskStore(path).save(list(engine.list()))

            restored = TaskStore(path).load()
            self.assertEqual(len(restored), 1)
            self.assertEqual(restored[0].status, TaskStatus.QUEUED)
            self.assertEqual(restored[0].task.task_id, "persist-1")
            self.assertEqual(restored[0].task.materials[0].uri, "file://report.docx")
            self.assertEqual(restored[0].task.metadata["project"], "demo")

    def test_completed_result_survives_restart(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "tasks.json"
            engine = TaskEngine()
            engine.submit(self.task())
            runtime = AgentRuntimeAdapter({
                "report-audit-agent": lambda p: AgentResult(p.task_id, p.agent, AgentStatus.ACCEPTED),
                "final-audit-agent": lambda p: AgentResult(p.task_id, p.agent, AgentStatus.ACCEPTED),
            })
            record = engine.run_next(runtime)
            TaskStore(path).save(list(engine.list()))

            restored = TaskStore(path).load()[0]
            self.assertEqual(restored.status, TaskStatus.COMPLETED)
            self.assertEqual(restored.result_status, AgentStatus.ACCEPTED)
            self.assertIsNotNone(restored.state)
            self.assertEqual(len(restored.state.results), 2)


if __name__ == "__main__":
    unittest.main()

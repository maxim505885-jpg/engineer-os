import tempfile
import unittest
from pathlib import Path

from engineering.core import (
    AgentResult,
    AgentStatus,
    EngineerTask,
    MaterialRef,
    ProjectRecord,
    RunRecord,
    TaskEngine,
    TaskStatus,
    TaskStore,
)
from engineering.core.engineer_core import AgentRuntimeAdapter


class TaskStoreTests(unittest.TestCase):
    def task(self):
        return EngineerTask(
            task_id="persist-1",
            tz="Проверить отчет по ТЗ.",
            materials=(MaterialRef("report-1", "report", "report.docx", "file://report.docx"),),
            requested_checks=("report",),
            metadata={"project_id": "project-1", "project_name": "Demo"},
        )

    def test_queued_task_survives_restart(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "tasks.json"
            engine = TaskEngine(store=TaskStore(path))
            engine.submit(self.task())

            restored = TaskStore(path).load()
            self.assertEqual(len(restored), 1)
            self.assertEqual(restored[0].status, TaskStatus.QUEUED)
            self.assertEqual(restored[0].task.task_id, "persist-1")

            projects = TaskStore(path).list_projects()
            materials = TaskStore(path).list_materials()
            self.assertEqual(projects, [ProjectRecord("project-1", "Demo", {"project_id": "project-1", "project_name": "Demo"})])
            self.assertEqual(materials[0].material_id, "report-1")
            self.assertEqual(materials[0].project_id, "project-1")

    def test_engine_persists_lifecycle_and_runs(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "tasks.json"
            store = TaskStore(path)
            engine = TaskEngine(store=store)
            engine.submit(self.task())
            runtime = AgentRuntimeAdapter({
                "report-audit-agent": lambda p: AgentResult(p.task_id, p.agent, AgentStatus.ACCEPTED),
                "final-audit-agent": lambda p: AgentResult(p.task_id, p.agent, AgentStatus.ACCEPTED),
            })
            engine.run_next(runtime)

            restored = TaskStore(path).load()[0]
            self.assertEqual(restored.status, TaskStatus.COMPLETED)
            self.assertEqual(restored.result_status, AgentStatus.ACCEPTED)
            self.assertIsNotNone(restored.state)
            self.assertEqual(len(restored.state.results), 2)

            runs = store.list_runs()
            self.assertEqual(len(runs), 1)
            self.assertEqual(runs[0].task_id, "persist-1")
            self.assertEqual(runs[0].status, "COMPLETED")
            self.assertIsInstance(runs[0], RunRecord)


if __name__ == "__main__":
    unittest.main()

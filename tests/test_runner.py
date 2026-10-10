import unittest

from engineering.core import (
    AgentResult,
    AgentStatus,
    EngineerRunner,
    EngineerTask,
    MaterialRef,
)
from engineering.core.engineer_core import AgentRuntimeAdapter, EngineerCore


class EngineerRunnerTests(unittest.TestCase):
    def test_run_is_single_entry_point(self):
        task = EngineerTask(
            task_id="run-001",
            tz="Проверить отчёт по ТЗ",
            materials=(MaterialRef("m1", "report", "report.docx"),),
            requested_checks=("report",),
        )

        def accepted(specialist):
            checked = ("report-audit-agent",) if specialist.agent == "final-audit-agent" else ()
            basis = (
                {"report_quality": ("report-validation-1",)}
                if specialist.agent == "report-audit-agent"
                else {}
            )
            return AgentResult(
                specialist.task_id,
                specialist.agent,
                AgentStatus.ACCEPTED,
                evidence_ids=("m1",),
                checked_agents=checked,
                acceptance_basis=basis,
            )

        runtime = AgentRuntimeAdapter({
            "report-audit-agent": accepted,
            "final-audit-agent": accepted,
        })
        core = EngineerCore(acceptance_gate=lambda _: True)
        summary = EngineerRunner(core).run(task, runtime)

        self.assertEqual(summary.task_id, "run-001")
        self.assertEqual(summary.status, AgentStatus.ACCEPTED)
        self.assertEqual(
            summary.completed_agents,
            ("report-audit-agent", "final-audit-agent"),
        )
        self.assertEqual(summary.blocking_agents, ())

    def test_summary_is_serializable_shape(self):
        summary = EngineerRunner().run(
            EngineerTask(
                "run-002",
                "ТЗ",
                (MaterialRef("m1", "report", "r"),),
                ("report",),
            ),
            AgentRuntimeAdapter(),
        )
        payload = EngineerRunner.summarize(summary)
        self.assertEqual(payload["task_id"], "run-002")
        self.assertEqual(payload["status"], "UNCERTAINTY")
        self.assertIn("results", payload)


if __name__ == "__main__":
    unittest.main()

import unittest

from engineering.core import AgentResult, AgentStatus, EngineerCore, EngineerTask, MaterialRef
from engineering.core.engineer_core import AgentRuntimeAdapter


class EngineerCoreTests(unittest.TestCase):
    def setUp(self):
        self.task = EngineerTask(
            task_id="demo-001",
            tz="Проверить отчет согласно ТЗ",
            materials=(MaterialRef("m1", "report", "report.docx"),),
            requested_checks=("report", "normative", "calculation"),
        )

    def test_plan_adds_final_audit(self):
        state = EngineerCore().plan(self.task)
        self.assertEqual(
            [x.skill for x in state.planned],
            ["report-review", "normative-check", "calculation-review", "final-audit"],
        )

    def test_missing_runtime_handler_is_uncertainty(self):
        state = EngineerCore().run(self.task, AgentRuntimeAdapter())
        self.assertEqual(EngineerCore().final_status(state), AgentStatus.UNCERTAINTY)

    def test_runtime_handler_is_executed(self):
        calls = []

        def accepted(task):
            calls.append(task.agent)
            return AgentResult(task.task_id, task.agent, AgentStatus.ACCEPTED)

        runtime = AgentRuntimeAdapter(
            {agent: accepted for agent, _, _ in {
                "report": ("report-audit-agent", "report-review", ""),
                "normative": ("normative-agent", "normative-check", ""),
                "calculation": ("calculation-agent", "calculation-review", ""),
                "final_audit": ("final-audit-agent", "final-audit", ""),
            }.values()}
        )
        state = EngineerCore().run(self.task, runtime)
        self.assertEqual(EngineerCore().final_status(state), AgentStatus.ACCEPTED)
        self.assertEqual(len(calls), 4)

    def test_wrong_runtime_result_is_rejected(self):
        def wrong_result(task):
            return AgentResult(task.task_id, "other-agent", AgentStatus.ACCEPTED)

        runtime = AgentRuntimeAdapter({"report-audit-agent": wrong_result})
        with self.assertRaises(ValueError):
            EngineerCore().run(self.task, runtime)

    def test_block_result_blocks_final_status(self):
        core = EngineerCore()
        state = core.plan(self.task)
        results = [AgentResult("demo-001", p.agent, AgentStatus.ACCEPTED) for p in state.planned]
        results[-1] = AgentResult("demo-001", state.planned[-1].agent, AgentStatus.BLOCK)
        core.collect(state, results)
        self.assertEqual(core.final_status(state), AgentStatus.BLOCK)

    def test_all_accepted(self):
        core = EngineerCore()
        state = core.plan(self.task)
        results = [AgentResult("demo-001", p.agent, AgentStatus.ACCEPTED) for p in state.planned]
        core.collect(state, results)
        self.assertEqual(core.final_status(state), AgentStatus.ACCEPTED)


if __name__ == "__main__":
    unittest.main()

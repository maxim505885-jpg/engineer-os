import unittest

from engineering.core import AgentResult, AgentStatus, EngineerCore, EngineerTask, MaterialRef


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
        self.assertEqual([x.skill for x in state.planned], ["report-review", "normative-check", "calculation-review", "final-audit"])

    def test_missing_agent_result_is_uncertainty(self):
        core = EngineerCore()
        state = core.plan(self.task)
        core.collect(state, [AgentResult("demo-001", "report-audit-agent", AgentStatus.ACCEPTED)])
        self.assertEqual(core.final_status(state), AgentStatus.UNCERTAINTY)

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

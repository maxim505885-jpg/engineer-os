import unittest

from engineering.core import AgentResult, AgentStatus, EngineerCore, EngineerTask, MaterialRef
from engineering.core.engineer_core import AgentRuntimeAdapter
from engineering.core.codex_runtime import CodexAppServerClient, CodexServerConfig


class EngineerCoreTests(unittest.TestCase):
    def setUp(self):
        self.task = EngineerTask(
            task_id="demo-001",
            tz="Проверить отчет согласно ТЗ",
            materials=(MaterialRef("m1", "report", "report.docx"),),
            requested_checks=("report", "normative", "calculation"),
        )
        self.evidence = ("m1",)

    def test_plan_adds_final_audit(self):
        state = EngineerCore().plan(self.task)
        self.assertEqual(
            [x.skill for x in state.planned],
            ["report-review", "normative-check", "calculation-review", "final-audit"],
        )

    def test_planned_specialists_receive_controlling_tz(self):
        state = EngineerCore().plan(self.task)
        self.assertTrue(all(item.tz == self.task.tz for item in state.planned))

    def test_missing_runtime_handler_is_uncertainty(self):
        state = EngineerCore().run(self.task, AgentRuntimeAdapter())
        self.assertEqual(EngineerCore().final_status(state), AgentStatus.UNCERTAINTY)

    def test_runtime_handler_is_executed(self):
        calls = []

        def accepted(task):
            calls.append(task.agent)
            checked = (
                ("report-audit-agent", "normative-agent", "calculation-agent")
                if task.agent == "final-audit-agent"
                else ()
            )
            return AgentResult(
                task.task_id,
                task.agent,
                AgentStatus.ACCEPTED,
                evidence_ids=self.evidence,
                checked_agents=checked,
            )

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
        results = [AgentResult("demo-001", p.agent, AgentStatus.ACCEPTED, evidence_ids=self.evidence) for p in state.planned]
        results[-1] = AgentResult("demo-001", state.planned[-1].agent, AgentStatus.BLOCK)
        core.collect(state, results)
        self.assertEqual(core.final_status(state), AgentStatus.BLOCK)

    def test_accepted_without_evidence_is_rejected_at_runtime_boundary(self):
        def accepted_without_evidence(task):
            return AgentResult(task.task_id, task.agent, AgentStatus.ACCEPTED)

        runtime = AgentRuntimeAdapter(
            {agent: accepted_without_evidence for agent, _, _ in {
                "report": ("report-audit-agent", "report-review", ""),
                "normative": ("normative-agent", "normative-check", ""),
                "calculation": ("calculation-agent", "calculation-review", ""),
                "final_audit": ("final-audit-agent", "final-audit", ""),
            }.values()}
        )
        with self.assertRaises(ValueError):
            EngineerCore().run(self.task, runtime)

    def test_accepted_without_evidence_is_rejected_at_core_boundary(self):
        core = EngineerCore()
        state = core.plan(self.task)
        with self.assertRaises(ValueError):
            core.collect(
                state,
                [AgentResult("demo-001", p.agent, AgentStatus.ACCEPTED) for p in state.planned],
            )

    def test_pass_without_evidence_is_rejected(self):
        core = EngineerCore()
        state = core.plan(self.task)
        with self.assertRaises(ValueError):
            core.collect(
                state,
                [AgentResult("demo-001", state.planned[0].agent, AgentStatus.PASS)],
            )

    def test_final_audit_without_coverage_is_rejected(self):
        core = EngineerCore()
        state = core.plan(self.task)
        results = [
            AgentResult("demo-001", p.agent, AgentStatus.ACCEPTED, evidence_ids=self.evidence)
            for p in state.planned[:-1]
        ]
        results.append(
            AgentResult(
                "demo-001",
                state.planned[-1].agent,
                AgentStatus.ACCEPTED,
                evidence_ids=self.evidence,
            )
        )
        with self.assertRaises(ValueError):
            core.collect(state, results)

    def test_final_audit_incomplete_coverage_cannot_accept(self):
        core = EngineerCore()
        state = core.plan(self.task)
        results = [
            AgentResult("demo-001", p.agent, AgentStatus.ACCEPTED, evidence_ids=self.evidence)
            for p in state.planned[:-1]
        ]
        results.append(
            AgentResult(
                "demo-001",
                state.planned[-1].agent,
                AgentStatus.ACCEPTED,
                evidence_ids=self.evidence,
                checked_agents=("report-audit-agent",),
            )
        )
        core.collect(state, results)
        self.assertEqual(core.final_status(state), AgentStatus.UNCERTAINTY)

    def test_duplicate_agent_result_cannot_hide_missing_coverage(self):
        core = EngineerCore()
        state = core.plan(self.task)
        duplicate = AgentResult(
            "demo-001",
            "report-audit-agent",
            AgentStatus.ACCEPTED,
            evidence_ids=self.evidence,
        )
        with self.assertRaises(ValueError):
            core.collect(state, [duplicate, duplicate])

    def test_codex_extracts_final_agent_message_item(self):
        message = {"params": {"item": {"type": "agentMessage", "text": "FINAL RESULT"}}}
        self.assertEqual(CodexAppServerClient._extract_agent_message(message), "FINAL RESULT")

    def test_codex_extracts_empty_for_non_agent_item(self):
        message = {"params": {"item": {"type": "commandExecution", "command": "pytest"}}}
        self.assertEqual(CodexAppServerClient._extract_agent_message(message), "")

    def test_codex_config_has_safe_read_only_defaults(self):
        config = CodexServerConfig()
        self.assertEqual(config.sandbox, "read-only")
        self.assertEqual(config.approval_policy, "never")


if __name__ == "__main__":
    unittest.main()

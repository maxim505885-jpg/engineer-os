import unittest

from engineering.core import AgentResult, AgentStatus, EngineerCore, EngineerTask, MaterialRef
from engineering.core.engineer_core import AgentRuntimeAdapter
from engineering.core.codex_runtime import CodexAppServerClient, CodexServerConfig
from engineering.core.codex_result_parser import CodexResultParser


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

    def test_planned_specialists_receive_controlling_tz(self):
        state = EngineerCore().plan(self.task)
        self.assertTrue(all(item.tz == self.task.tz for item in state.planned))

    def test_final_audit_is_always_last_even_when_requested_early(self):
        task = EngineerTask(
            task_id="audit-order",
            tz="Проверить отчет по ТЗ",
            materials=(MaterialRef("m1", "report", "report.docx"),),
            requested_checks=("final_audit", "report", "normative"),
        )
        state = EngineerCore().plan(task)
        self.assertEqual(
            [item.skill for item in state.planned],
            ["report-review", "normative-check", "final-audit"],
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

    def test_duplicate_runtime_result_is_rejected(self):
        core = EngineerCore()
        state = core.plan(self.task)
        first = AgentResult("demo-001", "report-audit-agent", AgentStatus.ACCEPTED)
        with self.assertRaises(ValueError):
            core.collect(state, [first, first])

    def test_final_audit_must_be_terminal_result(self):
        core = EngineerCore()
        state = core.plan(self.task)
        results = [AgentResult("demo-001", p.agent, AgentStatus.ACCEPTED) for p in state.planned]
        state.results = [results[-1], results[0], results[1], results[2]]
        self.assertEqual(core.final_status(state), AgentStatus.UNCERTAINTY)

    def test_block_result_blocks_final_status(self):
        core = EngineerCore()
        state = core.plan(self.task)
        results = [AgentResult("demo-001", p.agent, AgentStatus.ACCEPTED) for p in state.planned]
        results[-1] = AgentResult("demo-001", state.planned[-1].agent, AgentStatus.BLOCK)
        core.collect(state, results)
        self.assertEqual(core.final_status(state), AgentStatus.BLOCK)

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

    def test_all_accepted(self):
        core = EngineerCore()
        state = core.plan(self.task)
        results = [AgentResult("demo-001", p.agent, AgentStatus.ACCEPTED) for p in state.planned]
        core.collect(state, results)
        self.assertEqual(core.final_status(state), AgentStatus.ACCEPTED)


class CodexResultParserTests(unittest.TestCase):
    def setUp(self):
        self.task = EngineerTask(
            task_id="parser-001",
            tz="Проверить отчет по ТЗ",
            materials=(MaterialRef("m1", "report", "report.docx"),),
            requested_checks=("report",),
        )
        self.specialist = EngineerCore().plan(self.task).planned[0]

    def test_findings_require_evidence(self):
        result = CodexResultParser.parse(
            self.specialist,
            '{"status":"WARNING","findings":[{"issue":"x"}],"evidence_ids":[],"message":"x"}',
        )
        self.assertEqual(result.status, AgentStatus.UNCERTAINTY)

    def test_evidence_ids_must_reference_supplied_materials(self):
        result = CodexResultParser.parse(
            self.specialist,
            '{"status":"ACCEPTED","findings":[],"evidence_ids":["missing-material"],"message":"ok"}',
        )
        self.assertEqual(result.status, AgentStatus.UNCERTAINTY)

    def test_uncertain_finding_cannot_be_accepted(self):
        raw = '{"status":"ACCEPTED","findings":[{"observation":"признак","evidence_ids":["m1"],"basis":"осмотр","certainty":"UNCERTAIN","conclusion":"данных недостаточно"}],"evidence_ids":["m1"],"message":"x"}'
        result = CodexResultParser.parse(self.specialist, raw)
        self.assertEqual(result.status, AgentStatus.UNCERTAINTY)

    def test_pass_cannot_contain_findings(self):
        raw = '{"status":"PASS","findings":[{"observation":"признак","evidence_ids":["m1"],"basis":"осмотр","certainty":"CONFIRMED","conclusion":"вывод"}],"evidence_ids":["m1"],"message":"x"}'
        result = CodexResultParser.parse(self.specialist, raw)
        self.assertEqual(result.status, AgentStatus.UNCERTAINTY)

    def test_finding_certainty_is_enum(self):
        raw = '{"status":"WARNING","findings":[{"observation":"признак","evidence_ids":["m1"],"basis":"осмотр","certainty":"maybe","conclusion":"вывод"}],"evidence_ids":["m1"],"message":"x"}'
        result = CodexResultParser.parse(self.specialist, raw)
        self.assertEqual(result.status, AgentStatus.UNCERTAINTY)

    def test_findings_require_structured_engineering_fields(self):
        raw = '{"status":"WARNING","findings":[{"observation":"трещина","evidence_ids":["m1"],"basis":"осмотр","certainty":"measured","conclusion":"требуется проверка"}],"evidence_ids":["m1"],"message":"x"}'
        result = CodexResultParser.parse(self.specialist, raw)
        self.assertEqual(result.status, AgentStatus.ACCEPTED)

    def test_findings_without_structured_fields_are_uncertainty(self):
        raw = '{"status":"WARNING","findings":[{"issue":"трещина","evidence_ids":["m1"]}],"evidence_ids":["m1"],"message":"x"}'
        result = CodexResultParser.parse(self.specialist, raw)
        self.assertEqual(result.status, AgentStatus.UNCERTAINTY)

    def test_evidence_ids_must_be_non_empty_and_unique(self):
        result = CodexResultParser.parse(
            self.specialist,
            '{"status":"ACCEPTED","findings":[],"evidence_ids":["m1","m1"],"message":"ok"}',
        )
        self.assertEqual(result.status, AgentStatus.UNCERTAINTY)


if __name__ == "__main__":
    unittest.main()

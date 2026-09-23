import unittest

from engineering.core.codex_result_parser import CodexResultParser
from engineering.core.contracts import AgentStatus, SpecialistTask


class CodexResultParserTests(unittest.TestCase):
    def setUp(self):
        self.task = SpecialistTask(
            "task-1",
            "report-audit-agent",
            "report-review",
            (),
            "Audit report",
            "Проверить отчёт согласно ТЗ.",
        )

    def test_valid_result(self):
        result = CodexResultParser.parse(
            self.task,
            '{"status":"ACCEPTED","findings":[],"evidence_ids":["e1"],"message":"ok"}',
        )
        self.assertEqual(result.status, AgentStatus.ACCEPTED)
        self.assertEqual(result.evidence_ids, ("e1",))

    def test_invalid_json_becomes_uncertainty(self):
        result = CodexResultParser.parse(self.task, "not json")
        self.assertEqual(result.status, AgentStatus.UNCERTAINTY)

    def test_invalid_status_becomes_uncertainty(self):
        result = CodexResultParser.parse(
            self.task,
            '{"status":"DONE","findings":[],"evidence_ids":[],"message":null}',
        )
        self.assertEqual(result.status, AgentStatus.UNCERTAINTY)

    def test_invalid_findings_becomes_uncertainty(self):
        result = CodexResultParser.parse(
            self.task,
            '{"status":"PASS","findings":"bad","evidence_ids":[],"message":null}',
        )
        self.assertEqual(result.status, AgentStatus.UNCERTAINTY)


if __name__ == "__main__":
    unittest.main()

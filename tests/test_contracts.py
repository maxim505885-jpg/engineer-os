import json
import unittest

from engineering.core import AgentResult, AgentStatus


class AgentResultContractTests(unittest.TestCase):
    def test_as_dict_is_json_serializable(self):
        result = AgentResult(
            "task-1",
            "report-audit-agent",
            AgentStatus.ACCEPTED,
            findings=({"finding": "ok"},),
            evidence_ids=("e1",),
            message="done",
        )
        payload = result.as_dict()
        self.assertEqual(payload["status"], "ACCEPTED")
        self.assertEqual(payload["evidence_ids"], ["e1"])
        json.dumps(payload, ensure_ascii=False)

    def test_has_findings(self):
        self.assertFalse(AgentResult("t", "a", AgentStatus.PASS).has_findings)
        self.assertTrue(AgentResult("t", "a", AgentStatus.PASS, findings=({"x": 1},)).has_findings)


if __name__ == "__main__":
    unittest.main()

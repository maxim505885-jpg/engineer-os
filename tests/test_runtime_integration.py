import unittest
from unittest.mock import patch

from engineering.core.codex_runtime import CodexAppServerClient, CodexServerConfig
from engineering.core.contracts import MaterialRef, SpecialistTask


class FakeProcess:
    def __init__(self):
        self.stdin = None
        self.stdout = None

    def terminate(self):
        return None


class CodexRuntimeUnitTests(unittest.TestCase):
    def test_specialist_prompt_contains_tz_and_prior_results(self):
        task = SpecialistTask(
            "t-1", "report-audit-agent", "report-review",
            (MaterialRef("m1", "report", "report.docx"),),
            "Review report", "Проверить отчет по ТЗ"
        )
        client = CodexAppServerClient(CodexServerConfig())
        captured = {}

        def fake_start():
            return None

        def fake_request(method, params=None):
            captured[method] = params or {}
            if method == "thread/start":
                return {"thread": {"id": "thread-1"}}
            if method == "turn/start":
                return {"turn": {"id": "turn-1"}}
            return {}

        with patch.object(client, "start", fake_start),              patch.object(client, "request", side_effect=fake_request),              patch.object(client, "_collect_turn", return_value=(
                 '{"status":"ACCEPTED","findings":[],"evidence_ids":[],"message":"ok"}',
                 {"status":"completed"},
             )):
            client.execute_specialist(
                task,
                prior_results=(),
            )

        prompt = captured["turn/start"]["input"][0]["text"]
        self.assertIn("Проверить отчет по ТЗ", prompt)
        self.assertIn("report-review", prompt)

    def test_safe_defaults_remain_read_only(self):
        config = CodexServerConfig()
        self.assertEqual(config.sandbox, "read-only")
        self.assertEqual(config.approval_policy, "never")


if __name__ == "__main__":
    unittest.main()

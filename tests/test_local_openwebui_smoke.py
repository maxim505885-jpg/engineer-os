import unittest
from types import SimpleNamespace

from engineering.core import AgentResult, AgentStatus
from scripts.local_openwebui_smoke import evaluate_smoke


class LocalSmokeTests(unittest.TestCase):
    def runtime(self, status):
        return SimpleNamespace(execute=lambda planned: [AgentResult(p.task_id, p.agent, status) for p in planned])

    def test_uncertainty_is_valid_transport_but_not_engineering_acceptance(self):
        result = evaluate_smoke(self.runtime(AgentStatus.UNCERTAINTY))
        self.assertEqual(result['runtime_health'], 'PASSED')
        self.assertEqual(result['engineering_status'], 'UNCERTAINTY')

    def test_errors_and_no_material_acceptance_do_not_pass_smoke(self):
        for status in (AgentStatus.ERROR, AgentStatus.ACCEPTED, AgentStatus.PASS):
            self.assertEqual(evaluate_smoke(self.runtime(status))['runtime_health'], 'FAILED')

    def test_missing_result_fails(self):
        runtime = SimpleNamespace(execute=lambda planned: [])
        self.assertEqual(evaluate_smoke(runtime)['runtime_health'], 'FAILED')


if __name__ == '__main__': unittest.main()

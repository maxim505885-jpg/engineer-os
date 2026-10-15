import unittest

from engineering.core.external_orchestrator import (
    ExternalGraphOrchestrator,
    OrchestrationBoundaryError,
    OrchestrationStep,
)


class ExternalGraphOrchestratorTests(unittest.TestCase):
    def test_known_pending_agent_can_be_scheduled(self):
        o = ExternalGraphOrchestrator(lambda planned, completed: OrchestrationStep("normative-agent"))
        self.assertEqual(
            o.next_step(("report-audit-agent", "normative-agent", "final-audit-agent"), ("report-audit-agent",)).agent,
            "normative-agent",
        )

    def test_unplanned_agent_is_blocked(self):
        o = ExternalGraphOrchestrator(lambda planned, completed: OrchestrationStep("external-acceptance-agent"))
        with self.assertRaises(OrchestrationBoundaryError):
            o.next_step(("report-audit-agent", "final-audit-agent"), ())

    def test_completed_agent_cannot_be_replayed_as_next_step(self):
        o = ExternalGraphOrchestrator(lambda planned, completed: OrchestrationStep("report-audit-agent"))
        with self.assertRaises(OrchestrationBoundaryError):
            o.next_step(("report-audit-agent", "final-audit-agent"), ("report-audit-agent",))

    def test_external_orchestrator_has_no_status_or_acceptance_field(self):
        step = OrchestrationStep("final-audit-agent")
        self.assertFalse(hasattr(step, "status"))
        self.assertFalse(hasattr(step, "accepted"))


if __name__ == "__main__":
    unittest.main()

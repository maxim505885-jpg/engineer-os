from __future__ import annotations

import unittest

from engineering.core.contracts import AgentResult, AgentStatus, EngineerTask
from engineering.core.engineer_core import AgentRuntimeAdapter, EngineerCore
from engineering.core.supabase_acceptance_gate import SupabaseAcceptanceGate


class FakeGate(SupabaseAcceptanceGate):
    def __init__(self, payload):
        self.payload = payload

    def _rpc(self, function_name, payload):
        return self.payload


class SupabaseAcceptanceGateTests(unittest.TestCase):
    def _task(self):
        return EngineerTask(
            task_id="gate-task",
            tz="test tz",
            materials=("material",),
            requested_checks=("inspection",),
        )

    def _accepted_state(self):
        task = self._task()
        core = EngineerCore(acceptance_gate=lambda _: True)
        state = core.plan(task)
        results = [
            AgentResult(
                task_id="gate-task",
                agent="inspection-agent",
                status=AgentStatus.ACCEPTED,
                evidence_ids=("e1",),
            ),
            AgentResult(
                task_id="gate-task",
                agent="final-audit-agent",
                status=AgentStatus.ACCEPTED,
                evidence_ids=("e2",),
                checked_agents=("inspection-agent",),
            ),
        ]
        return core.collect(state, results)

    def test_gate_accepts_only_explicit_pass(self):
        state = self._accepted_state()
        self.assertTrue(FakeGate({"status": "PASS", "task_id": "gate-task"})(state))

    def test_gate_blocks_non_pass(self):
        state = self._accepted_state()
        self.assertFalse(FakeGate({"status": "BLOCK", "task_id": "gate-task"})(state))

    def test_gate_blocks_wrong_task(self):
        state = self._accepted_state()
        self.assertFalse(FakeGate({"status": "PASS", "task_id": "other"})(state))


if __name__ == "__main__":
    unittest.main()

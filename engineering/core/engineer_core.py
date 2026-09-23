from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .contracts import AgentResult, AgentStatus, EngineerTask, SpecialistTask


CHECK_REGISTRY: dict[str, tuple[str, str, str]] = {
    "inspection": ("inspection-agent", "inspection-audit", "Structure inspection evidence and facts."),
    "report": ("report-audit-agent", "report-review", "Audit the report against the ТЗ and source evidence."),
    "normative": ("normative-agent", "normative-check", "Verify applicability and traceability of normative requirements."),
    "calculation": ("calculation-agent", "calculation-review", "Verify calculation model, inputs, solver output and interpretation."),
    "final_audit": ("final-audit-agent", "final-audit", "Perform the final evidence, consistency and status audit."),
}


@dataclass
class CoreState:
    task: EngineerTask
    planned: list[SpecialistTask]
    results: list[AgentResult]


class EngineerCore:
    """Deterministic orchestration layer; it does not invent engineering results."""

    def plan(self, task: EngineerTask) -> CoreState:
        self._validate(task)
        planned: list[SpecialistTask] = []
        for check in task.requested_checks:
            key = check.strip().lower()
            if key not in CHECK_REGISTRY:
                raise ValueError(f"Unknown requested check: {check}")
            agent, skill, purpose = CHECK_REGISTRY[key]
            planned.append(SpecialistTask(task.task_id, agent, skill, task.materials, purpose))
        if "final_audit" not in {x.strip().lower() for x in task.requested_checks}:
            agent, skill, purpose = CHECK_REGISTRY["final_audit"]
            planned.append(SpecialistTask(task.task_id, agent, skill, task.materials, purpose))
        return CoreState(task=task, planned=planned, results=[])

    def collect(self, state: CoreState, results: Iterable[AgentResult]) -> CoreState:
        allowed = {p.agent for p in state.planned}
        for result in results:
            if result.agent not in allowed:
                raise ValueError(f"Result from unplanned agent: {result.agent}")
            if result.task_id != state.task.task_id:
                raise ValueError("Result task_id does not match core task")
            state.results.append(result)
        return state

    def final_status(self, state: CoreState) -> AgentStatus:
        if not state.task.tz.strip():
            return AgentStatus.BLOCK
        if not state.task.materials:
            return AgentStatus.BLOCK
        if any(r.status == AgentStatus.ERROR for r in state.results):
            return AgentStatus.ERROR
        if any(r.status == AgentStatus.BLOCK for r in state.results):
            return AgentStatus.BLOCK
        if any(r.status == AgentStatus.UNCERTAINTY for r in state.results):
            return AgentStatus.UNCERTAINTY
        if any(r.status == AgentStatus.WARNING for r in state.results):
            return AgentStatus.WARNING
        expected = {p.agent for p in state.planned}
        actual = {r.agent for r in state.results}
        if expected - actual:
            return AgentStatus.UNCERTAINTY
        return AgentStatus.ACCEPTED

    @staticmethod
    def _validate(task: EngineerTask) -> None:
        if not task.task_id.strip():
            raise ValueError("task_id is required")
        if not task.tz.strip():
            raise ValueError("ТЗ is required")
        if not task.materials:
            raise ValueError("At least one material is required")
        if not task.requested_checks:
            raise ValueError("At least one requested check is required")

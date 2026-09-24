from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable

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


AgentHandler = Callable[[SpecialistTask], AgentResult]


class AgentRuntimeAdapter:
    """Small runtime boundary.

    A real Codex/runtime integration can implement this interface without
    changing ENGINEER CORE contracts. Missing handlers are never treated as
    successful engineering work.
    """

    def __init__(self, handlers: dict[str, AgentHandler] | None = None) -> None:
        self.handlers = handlers or {}

    def execute(self, planned: Iterable[SpecialistTask]) -> list[AgentResult]:
        results: list[AgentResult] = []
        for task in planned:
            handler = self.handlers.get(task.agent)
            if handler is None:
                results.append(
                    AgentResult(
                        task_id=task.task_id,
                        agent=task.agent,
                        status=AgentStatus.UNCERTAINTY,
                        message=f"No runtime handler registered for {task.agent}.",
                    )
                )
                continue
            result = handler(task)
            if result.task_id != task.task_id or result.agent != task.agent:
                raise ValueError("Runtime handler returned a result for the wrong task or agent")
            EngineerCore._validate_result_contract(result)
            results.append(result)
        return results


class EngineerCore:
    """Deterministic orchestration layer; it does not invent engineering results."""

    def plan(self, task: EngineerTask) -> CoreState:
        self._validate(task)
        planned: list[SpecialistTask] = []
        seen: set[str] = set()
        for check in task.requested_checks:
            key = check.strip().lower()
            if key not in CHECK_REGISTRY:
                raise ValueError(f"Unknown requested check: {check}")
            if key in seen:
                continue
            seen.add(key)
            agent, skill, purpose = CHECK_REGISTRY[key]
            planned.append(SpecialistTask(task.task_id, agent, skill, task.materials, purpose, task.tz))
        if "final_audit" not in seen:
            agent, skill, purpose = CHECK_REGISTRY["final_audit"]
            planned.append(SpecialistTask(task.task_id, agent, skill, task.materials, purpose, task.tz))
        return CoreState(task=task, planned=planned, results=[])

    def run(self, task: EngineerTask, runtime: AgentRuntimeAdapter) -> CoreState:
        state = self.plan(task)
        return self.collect(state, runtime.execute(state.planned))

    def collect(self, state: CoreState, results: Iterable[AgentResult]) -> CoreState:
        allowed = {p.agent for p in state.planned}
        seen: set[str] = set()
        for result in results:
            if result.agent not in allowed:
                raise ValueError(f"Result from unplanned agent: {result.agent}")
            if result.task_id != state.task.task_id:
                raise ValueError("Result task_id does not match core task")
            if result.agent in seen:
                raise ValueError(f"Duplicate result from agent: {result.agent}")
            self._validate_result_contract(result)
            seen.add(result.agent)
            state.results.append(result)
        return state

    def final_status(self, state: CoreState) -> AgentStatus:
        if not state.task.tz.strip() or not state.task.materials:
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

        final_audit = next(
            (r for r in state.results if r.agent == CHECK_REGISTRY["final_audit"][0]),
            None,
        )
        if final_audit is None:
            return AgentStatus.UNCERTAINTY

        if final_audit.status not in {
            AgentStatus.PASS,
            AgentStatus.ACCEPTED,
            AgentStatus.ACCEPTED_ALTERNATIVE,
        }:
            return AgentStatus.UNCERTAINTY

        expected_coverage = expected - {CHECK_REGISTRY["final_audit"][0]}
        covered = set(final_audit.checked_agents)
        if covered != expected_coverage:
            return AgentStatus.UNCERTAINTY

        return AgentStatus.ACCEPTED

    @staticmethod
    def _validate_result_contract(result: AgentResult) -> None:
        """Fail closed for statuses that claim an accepted engineering conclusion.

        A PASS/ACCEPTED result without traceable evidence is not an acceptable
        engineering result. The check is deliberately performed both at the
        runtime boundary and at Core.collect() so alternate runtimes cannot
        bypass the invariant.
        """
        if result.status in {
            AgentStatus.PASS,
            AgentStatus.ACCEPTED,
            AgentStatus.ACCEPTED_ALTERNATIVE,
        } and not result.evidence_ids:
            raise ValueError(
                f"{result.agent} returned {result.status.value} without evidence_ids"
            )

        if result.agent == CHECK_REGISTRY["final_audit"][0] and result.status in {
            AgentStatus.PASS,
            AgentStatus.ACCEPTED,
            AgentStatus.ACCEPTED_ALTERNATIVE,
        } and not result.checked_agents:
            raise ValueError(
                "final-audit-agent returned an accepting status without checked_agents"
            )

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

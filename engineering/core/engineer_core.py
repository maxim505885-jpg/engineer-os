from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Iterable

from .contracts import AgentResult, AgentStatus, EngineerTask, MaterialRef, SpecialistTask


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
    _origin_task: tuple = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._origin_task = self.task_binding(self.task)

    @staticmethod
    def task_binding(task: EngineerTask) -> tuple:
        # Immutable values, not aliases to mutable task lists. Metadata is
        # informational; the controlling execution scope is these fields.
        return (task.task_id, task.tz,
                tuple((m.id, m.kind, m.name, m.uri) for m in task.materials),
                tuple(task.requested_checks))


AgentHandler = Callable[[SpecialistTask], AgentResult]
AcceptanceGate = Callable[[CoreState], bool]


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
            EngineerCore._validate_result_contract(result)
            if result.task_id != task.task_id or result.agent != task.agent:
                raise ValueError("Runtime handler returned a result for the wrong task or agent")
            results.append(result)
        return results


class EngineerCore:
    """Deterministic orchestration layer; it does not invent engineering results."""

    def __init__(self, acceptance_gate: AcceptanceGate | None = None) -> None:
        # Final acceptance is fail-closed until an external, auditable gate
        # (for example the Supabase traceability/domain gate) explicitly passes.
        self.acceptance_gate = acceptance_gate

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
            if key == "final_audit":
                continue
            agent, skill, purpose = CHECK_REGISTRY[key]
            planned.append(SpecialistTask(task.task_id, agent, skill, task.materials, purpose, task.tz))
        agent, skill, purpose = CHECK_REGISTRY["final_audit"]
        planned.append(SpecialistTask(task.task_id, agent, skill, task.materials, purpose, task.tz))
        return CoreState(task=task, planned=planned, results=[])

    def run(self, task: EngineerTask, runtime: AgentRuntimeAdapter) -> CoreState:
        state = self.plan(task)
        return self.collect(state, runtime.execute(state.planned))

    def collect(self, state: CoreState, results: Iterable[AgentResult]) -> CoreState:
        self._validate_state(state)
        incoming = tuple(results)
        # Validate the whole proposed batch before changing the live state.
        self._validate_state(CoreState(state.task, state.planned, [*state.results, *incoming]))
        state.results.extend(incoming)
        return state

    def final_status(self, state: CoreState) -> AgentStatus:
        # CoreState is deliberately mutable during collection. Never trust a
        # caller's old validation when computing the authoritative status.
        try:
            self._validate_state(state)
        except ValueError:
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
        if (covered != expected_coverage
                or len(final_audit.checked_agents) != len(expected_coverage)):
            return AgentStatus.UNCERTAINTY

        if self.acceptance_gate is None:
            return AgentStatus.UNCERTAINTY
        try:
            if self.acceptance_gate(state) is not True:
                return AgentStatus.UNCERTAINTY
        except Exception:
            return AgentStatus.BLOCK

        return AgentStatus.ACCEPTED

    def _validate_state(self, state: CoreState) -> None:
        if not isinstance(state, CoreState):
            raise ValueError("CoreState is required")
        canonical = self.plan(state.task).planned
        if state.task_binding(state.task) != state._origin_task:
            raise ValueError("Core task scope changed; generate a new state and rerun specialists")
        if not isinstance(state.planned, list) or state.planned != canonical:
            raise ValueError("Core plan does not match the controlling task")
        if not isinstance(state.results, list):
            raise ValueError("Core results must be a list")
        allowed = {p.agent for p in canonical}
        seen: set[str] = set()
        for result in state.results:
            self._validate_result_contract(result)
            if result.task_id != state.task.task_id or result.agent not in allowed:
                raise ValueError("Stored result does not match the core task and plan")
            if result.agent in seen:
                raise ValueError("Duplicate stored agent result")
            if (result.agent == CHECK_REGISTRY["final_audit"][0]
                    and result.status in {AgentStatus.PASS, AgentStatus.ACCEPTED,
                                          AgentStatus.ACCEPTED_ALTERNATIVE}
                    and seen != allowed - {result.agent}):
                raise ValueError("An accepting FINAL AUDIT must follow all specialist results")
            seen.add(result.agent)

    @staticmethod
    def _validate_result_contract(result: AgentResult) -> None:
        """Fail closed for statuses that claim an accepted engineering conclusion.

        A PASS/ACCEPTED result without traceable evidence is not an acceptable
        engineering result. The check is deliberately performed both at the
        runtime boundary and at Core.collect() so alternate runtimes cannot
        bypass the invariant.
        """
        if not isinstance(result, AgentResult) or not isinstance(result.status, AgentStatus):
            raise ValueError("A typed AgentResult with a valid AgentStatus is required")
        if any(not isinstance(value, str) or not value.strip()
               for value in (result.task_id, result.agent)):
            raise ValueError("Result task_id and agent are required")
        for name in ("evidence_ids", "checked_agents"):
            values = getattr(result, name)
            if not isinstance(values, (tuple, list)) or any(
                not isinstance(item, str) or not item.strip() for item in values
            ):
                raise ValueError(f"{name} must be an array of nonblank strings")
        if not isinstance(result.acceptance_basis, dict):
            raise ValueError("acceptance_basis must be an object")
        for key, values in result.acceptance_basis.items():
            if (not isinstance(key, str) or not key.strip()
                    or not isinstance(values, (tuple, list))
                    or any(not isinstance(item, str) or not item.strip() for item in values)):
                raise ValueError("acceptance_basis must map domain names to arrays of IDs")
        if not isinstance(result.findings, (tuple, list)) or any(
            not isinstance(item, dict) for item in result.findings
        ):
            raise ValueError("findings must be an array of objects")
        if result.message is not None and not isinstance(result.message, str):
            raise ValueError("message must be a string or null")
        if result.status in {
            AgentStatus.PASS,
            AgentStatus.ACCEPTED,
            AgentStatus.ACCEPTED_ALTERNATIVE,
        } and (not result.evidence_ids or any(
            not isinstance(item, str) or not item.strip() for item in result.evidence_ids
        )):
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

        required_basis = {
            CHECK_REGISTRY["report"][0]: "report_quality",
            CHECK_REGISTRY["normative"][0]: "normative_verification",
            CHECK_REGISTRY["calculation"][0]: "calculation_verification",
        }.get(result.agent)
        if result.status in {
            AgentStatus.PASS,
            AgentStatus.ACCEPTED,
            AgentStatus.ACCEPTED_ALTERNATIVE,
        } and required_basis and (
            not result.acceptance_basis.get(required_basis)
            or any(not isinstance(item, str) or not item.strip()
                   for item in result.acceptance_basis[required_basis])
        ):
            raise ValueError(
                f"{result.agent} returned an accepting status without {required_basis} proof"
            )

    @staticmethod
    def _validate(task: EngineerTask) -> None:
        if not isinstance(task, EngineerTask):
            raise ValueError("EngineerTask is required")
        if not isinstance(task.task_id, str) or not task.task_id.strip():
            raise ValueError("task_id is required")
        if not isinstance(task.tz, str) or not task.tz.strip():
            raise ValueError("ТЗ is required")
        if not isinstance(task.materials, (tuple, list)) or not task.materials:
            raise ValueError("At least one material is required")
        seen: set[str] = set()
        for material in task.materials:
            if not isinstance(material, MaterialRef) or any(
                not isinstance(value, str) or not value.strip()
                for value in (material.id, material.kind, material.name)
            ):
                raise ValueError("Each material requires a nonblank id, kind and name")
            if material.id in seen:
                raise ValueError("Material IDs must be unique")
            seen.add(material.id)
            if material.uri is not None and not isinstance(material.uri, str):
                raise ValueError("Material URI must be a string or null")
        if (not isinstance(task.requested_checks, (tuple, list)) or not task.requested_checks
                or any(not isinstance(check, str) or not check.strip()
                       for check in task.requested_checks)):
            raise ValueError("At least one requested check is required")

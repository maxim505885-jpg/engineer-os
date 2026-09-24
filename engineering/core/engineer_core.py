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
            if key == "final_audit":
                continue
            if key in seen:
                continue
            seen.add(key)
            agent, skill, purpose = CHECK_REGISTRY[key]
            planned.append(SpecialistTask(task.task_id, agent, skill, task.materials, purpose, task.tz))

        agent, skill, purpose = CHECK_REGISTRY["final_audit"]
        planned.append(SpecialistTask(task.task_id, agent, skill, task.materials, purpose, task.tz))
        return CoreState(task=task, planned=planned, results=[])

    def run(self, task: EngineerTask, runtime: AgentRuntimeAdapter) -> CoreState:
        state = self.plan(task)
        return self.collect(state, runtime.execute(state.planned))

    def collect(self, state: CoreState, results: Iterable[AgentResult]) -> CoreState:
        planned_agents = [p.agent for p in state.planned]
        allowed = set(planned_agents)
        seen = {r.agent for r in state.results}
        for result in results:
            if result.agent not in allowed:
                raise ValueError(f"Result from unplanned agent: {result.agent}")
            if result.task_id != state.task.task_id:
                raise ValueError("Result task_id does not match core task")
            if result.agent in seen:
                raise ValueError(f"Duplicate result from agent: {result.agent}")
            state.results.append(result)
            seen.add(result.agent)
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
        conflicts = self.cross_agent_conflicts(state.results)
        if conflicts:
            resolution = self.final_audit_conflict_resolution(state.results[-1], conflicts) if state.results else {"complete": False}
            if not resolution["complete"]:
                return AgentStatus.UNCERTAINTY
        if any(r.status == AgentStatus.WARNING for r in state.results):
            return AgentStatus.WARNING

        expected = {p.agent for p in state.planned}
        actual = {r.agent for r in state.results}
        if expected - actual:
            return AgentStatus.UNCERTAINTY

        if not state.results or state.results[-1].agent != "final-audit-agent":
            return AgentStatus.UNCERTAINTY

        return AgentStatus.ACCEPTED

    @staticmethod
    def cross_agent_conflicts(results: list[AgentResult]) -> tuple[dict[str, object], ...]:
        """Return deterministic conflict records tied to the same evidence."""
        evidence_claims: dict[frozenset[str], dict[str, set[str]]] = {}
        for result in results:
            for finding in result.findings:
                if not isinstance(finding, dict):
                    continue
                evidence = finding.get("evidence_ids")
                certainty = finding.get("certainty")
                if not isinstance(evidence, list) or not evidence or not isinstance(certainty, str):
                    continue
                key = frozenset(item for item in evidence if isinstance(item, str) and item)
                if not key:
                    continue
                claims = evidence_claims.setdefault(key, {})
                claims.setdefault(certainty, set()).add(result.agent)

        conflicts: list[dict[str, object]] = []
        for index, evidence in enumerate(sorted(evidence_claims, key=lambda item: tuple(sorted(item))), start=1):
            claims = evidence_claims[evidence]
            if "CONFIRMED" not in claims or "UNCERTAIN" not in claims:
                continue
            conflicts.append({
                "id": f"conflict-{index:03d}",
                "evidence_ids": tuple(sorted(evidence)),
                "agents": {certainty: tuple(sorted(agents)) for certainty, agents in sorted(claims.items())},
            })
        return tuple(conflicts)

    @classmethod
    def _has_cross_agent_conflict(cls, results: list[AgentResult]) -> bool:
        return bool(cls.cross_agent_conflicts(results))

    @staticmethod
    def final_audit_covers_conflicts(final_audit: AgentResult, conflicts: tuple[dict[str, object], ...]) -> bool:
        """Require every detected conflict's evidence set to be explicitly audited."""
        if final_audit.agent != "final-audit-agent":
            return False
        for conflict in conflicts:
            conflict_evidence = set(conflict["evidence_ids"])
            covered = any(
                isinstance(finding, dict)
                and conflict_evidence.issubset(
                    set(item for item in finding.get("evidence_ids", []) if isinstance(item, str))
                )
                for finding in final_audit.findings
            )
            if not covered:
                return False
        return True

    @staticmethod
    def final_audit_conflict_resolution(
        final_audit: AgentResult,
        conflicts: tuple[dict[str, object], ...],
    ) -> dict[str, object]:
        """Evaluate whether FINAL_AUDIT explicitly resolves every detected conflict."""
        unresolved: list[str] = []
        if final_audit.agent != "final-audit-agent":
            return {"complete": False, "unresolved": [str(c["id"]) for c in conflicts]}

        for conflict in conflicts:
            conflict_id = str(conflict["id"])
            evidence = set(conflict["evidence_ids"])
            addressed = False
            resolved = False
            for finding in final_audit.findings:
                if not isinstance(finding, dict):
                    continue
                finding_evidence = set(
                    item for item in finding.get("evidence_ids", [])
                    if isinstance(item, str)
                )
                if not evidence.issubset(finding_evidence):
                    continue
                addressed = True
                if finding.get("conflict_ids") != [conflict_id]:
                    continue
                resolution_status = finding.get("resolution_status")
                resolution_basis = finding.get("resolution_basis")
                if resolution_status not in {"RESOLVED", "UNRESOLVED", "INSUFFICIENT_EVIDENCE"}:
                    continue
                if not isinstance(resolution_basis, str) or not resolution_basis.strip():
                    continue
                if resolution_status == "RESOLVED":
                    resolved = True
                    break
                # Explicit unresolved/insufficient-evidence states are accountable,
                # but they cannot produce an accepting final status.
                addressed = True
            if not addressed or not resolved:
                unresolved.append(conflict_id)

        return {
            "complete": not unresolved,
            "unresolved": tuple(unresolved),
        }

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

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from engineering.core.contracts import AgentResult, AgentStatus, SpecialistTask
from engineering.runtime.result_validator import RuntimeContractError, validate_agent_result


@dataclass(frozen=True)
class AgentQualityCase:
    """Deterministic regression contract for one agent scenario."""

    case_id: str
    expected_statuses: frozenset[AgentStatus]
    forbidden_statuses: frozenset[AgentStatus] = frozenset()
    required_certainties: frozenset[str] = frozenset()
    required_evidence_ids: frozenset[str] = frozenset()


@dataclass(frozen=True)
class AgentQualityResult:
    case_id: str
    passed: bool
    checks: tuple[str, ...]
    failures: tuple[str, ...]


class AgentHarness:
    """Run non-LLM quality gates around an ENGINEER OS agent result.

    The harness checks contracts and explicit scenario expectations only. It
    never infers engineering facts and never converts UNCERTAINTY into
    acceptance.
    """

    def evaluate(
        self,
        task: SpecialistTask,
        result: AgentResult,
        case: AgentQualityCase,
    ) -> AgentQualityResult:
        checks: list[str] = []
        failures: list[str] = []

        try:
            validate_agent_result(task, result)
            checks.append("result_contract")
        except RuntimeContractError as exc:
            failures.append(f"result_contract: {exc}")
            return AgentQualityResult(case.case_id, False, tuple(checks), tuple(failures))

        if case.expected_statuses and result.status not in case.expected_statuses:
            failures.append(
                f"status: expected one of "
                f"{sorted(status.value for status in case.expected_statuses)}, "
                f"got {result.status.value}"
            )
        else:
            checks.append("expected_status")

        if result.status in case.forbidden_statuses:
            failures.append(f"status: forbidden {result.status.value}")

        findings = tuple(f for f in result.findings if isinstance(f, dict))
        certainties = {
            str(finding.get("certainty"))
            for finding in findings
            if finding.get("certainty") is not None
        }
        missing_certainties = case.required_certainties - certainties
        if missing_certainties:
            failures.append("certainty: missing " + ", ".join(sorted(missing_certainties)))
        elif case.required_certainties:
            checks.append("required_certainties")

        evidence = {
            item
            for finding in findings
            for item in finding.get("evidence_ids", [])
            if isinstance(item, str)
        }
        evidence.update(item for item in result.evidence_ids if isinstance(item, str))
        missing_evidence = case.required_evidence_ids - evidence
        if missing_evidence:
            failures.append("evidence: missing " + ", ".join(sorted(missing_evidence)))
        elif case.required_evidence_ids:
            checks.append("required_evidence")

        if result.status not in case.forbidden_statuses and not (
            case.expected_statuses and result.status not in case.expected_statuses
        ):
            checks.append("status_gate")

        return AgentQualityResult(
            case_id=case.case_id,
            passed=not failures,
            checks=tuple(checks),
            failures=tuple(failures),
        )


def run_cases(
    harness: AgentHarness,
    cases: Iterable[tuple[SpecialistTask, AgentResult, AgentQualityCase]],
) -> tuple[AgentQualityResult, ...]:
    """Evaluate a finite regression set without changing agent results."""

    return tuple(harness.evaluate(task, result, case) for task, result, case in cases)

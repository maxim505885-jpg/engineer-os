from engineering.agent_quality import AgentHarness, AgentQualityCase
from engineering.core.contracts import AgentResult, AgentStatus, MaterialRef, SpecialistTask


def _task() -> SpecialistTask:
    return SpecialistTask(
        task_id="task-1",
        agent="inspection-agent",
        skill="inspection-audit",
        inputs=(MaterialRef("doc-1", "document", "Report"),),
        purpose="Inspect evidence",
    )


def test_harness_accepts_expected_uncertainty_without_inventing_acceptance() -> None:
    task = _task()
    result = AgentResult(
        task_id="task-1",
        agent="inspection-agent",
        status=AgentStatus.UNCERTAINTY,
        findings=(
            {
                "observation": "Observed text",
                "basis": "Document evidence",
                "certainty": "UNCERTAIN",
                "conclusion": "Insufficient evidence",
                "evidence_ids": ["doc-1:paragraph:0001"],
            },
        ),
        evidence_ids=("doc-1:paragraph:0001",),
    )
    case = AgentQualityCase(
        case_id="insufficient-data",
        expected_statuses=frozenset({AgentStatus.UNCERTAINTY}),
        forbidden_statuses=frozenset(
            {AgentStatus.ACCEPTED, AgentStatus.ACCEPTED_ALTERNATIVE}
        ),
        required_certainties=frozenset({"UNCERTAIN"}),
        required_evidence_ids=frozenset({"doc-1:paragraph:0001"}),
    )

    outcome = AgentHarness().evaluate(task, result, case)

    assert outcome.passed
    assert "result_contract" in outcome.checks


def test_harness_rejects_unexpected_acceptance() -> None:
    task = _task()
    result = AgentResult(
        task_id="task-1",
        agent="inspection-agent",
        status=AgentStatus.ACCEPTED,
        evidence_ids=("doc-1:paragraph:0001",),
    )
    case = AgentQualityCase(
        case_id="must-remain-uncertain",
        expected_statuses=frozenset({AgentStatus.UNCERTAINTY}),
        forbidden_statuses=frozenset({AgentStatus.ACCEPTED}),
    )

    outcome = AgentHarness().evaluate(task, result, case)

    assert not outcome.passed
    assert any("status:" in failure for failure in outcome.failures)

from engineering.core.contracts import AgentResult, AgentStatus, MaterialRef, SpecialistTask
from engineering.runtime.result_validator import RuntimeContractError, validate_agent_result


def _task() -> SpecialistTask:
    return SpecialistTask(
        task_id="task-1",
        agent="inspection-agent",
        skill="inspection-audit",
        inputs=(MaterialRef("doc-1", "document", "Report"),),
        purpose="Inspect evidence",
    )


def test_validator_accepts_evidence_nested_under_supplied_material() -> None:
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

    assert validate_agent_result(_task(), result) == result


def test_validator_rejects_evidence_from_other_material() -> None:
    result = AgentResult(
        task_id="task-1",
        agent="inspection-agent",
        status=AgentStatus.UNCERTAINTY,
        evidence_ids=("other-doc:paragraph:0001",),
    )

    try:
        validate_agent_result(_task(), result)
    except RuntimeContractError as exc:
        assert "not supplied" in str(exc)
    else:
        raise AssertionError("Expected RuntimeContractError")

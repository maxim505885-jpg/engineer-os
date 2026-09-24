from __future__ import annotations

from engineering.core.contracts import AgentResult, AgentStatus, SpecialistTask


class RuntimeContractError(ValueError):
    """The execution backend violated the ENGINEER OS result contract."""


def validate_agent_result(task: SpecialistTask, result: AgentResult) -> AgentResult:
    if result.task_id != task.task_id:
        raise RuntimeContractError("Runtime result task_id does not match SpecialistTask")
    if result.agent != task.agent:
        raise RuntimeContractError("Runtime result agent does not match SpecialistTask")
    if not isinstance(result.status, AgentStatus):
        raise RuntimeContractError("Runtime result status is not an AgentStatus")

    supplied = {m.id for m in task.inputs}
    top_evidence = {item for item in result.evidence_ids if isinstance(item, str) and item}
    if len(top_evidence) != len(result.evidence_ids):
        raise RuntimeContractError("Runtime result evidence_ids must contain non-empty strings")
    def evidence_is_supplied(evidence_id: str) -> bool:
        return any(evidence_id == material_id or evidence_id.startswith(f"{material_id}:") for material_id in supplied)

    if not all(evidence_is_supplied(item) for item in top_evidence):
        raise RuntimeContractError("Runtime result references evidence not supplied to the specialist")

    if result.status == AgentStatus.PASS and result.findings:
        raise RuntimeContractError("PASS result cannot contain findings")

    for index, finding in enumerate(result.findings):
        if not isinstance(finding, dict):
            raise RuntimeContractError(f"Finding {index} must be an object")
        for field in ("observation", "basis", "certainty", "conclusion"):
            if not isinstance(finding.get(field), str) or not finding[field].strip():
                raise RuntimeContractError(f"Finding {index} missing non-empty {field}")
        certainty = finding["certainty"]
        if certainty not in {"CONFIRMED", "PROBABLE", "UNCERTAIN"}:
            raise RuntimeContractError(f"Finding {index} has invalid certainty")
        finding_evidence = finding.get("evidence_ids")
        if not isinstance(finding_evidence, list) or not finding_evidence or not all(isinstance(x, str) and x for x in finding_evidence):
            raise RuntimeContractError(f"Finding {index} must contain non-empty evidence_ids")
        if not all(evidence_is_supplied(item) for item in finding_evidence):
            raise RuntimeContractError(f"Finding {index} references evidence not supplied to the specialist")
        if not set(finding_evidence).issubset(top_evidence):
            raise RuntimeContractError(f"Finding {index} evidence_ids must be present in top-level evidence_ids")
        if certainty == "UNCERTAIN" and result.status in {AgentStatus.PASS, AgentStatus.ACCEPTED, AgentStatus.ACCEPTED_ALTERNATIVE}:
            raise RuntimeContractError("UNCERTAIN finding cannot be returned with an accepting status")

    if result.agent == "final-audit-agent":
        for index, finding in enumerate(result.findings):
            conflict_ids = finding.get("conflict_ids")
            resolution_status = finding.get("resolution_status")
            resolution_basis = finding.get("resolution_basis")
            if conflict_ids is not None:
                if not isinstance(conflict_ids, list) or not all(isinstance(x, str) and x for x in conflict_ids):
                    raise RuntimeContractError(f"Final audit finding {index} has invalid conflict_ids")
                if resolution_status not in {"RESOLVED", "UNRESOLVED", "INSUFFICIENT_EVIDENCE"}:
                    raise RuntimeContractError(f"Final audit finding {index} has invalid resolution_status")
                if not isinstance(resolution_basis, str) or not resolution_basis.strip():
                    raise RuntimeContractError(f"Final audit finding {index} requires resolution_basis")
                if resolution_status == "RESOLVED" and not set(finding["evidence_ids"]).issubset(top_evidence):
                    raise RuntimeContractError(f"Resolved final-audit finding {index} lacks top-level evidence coverage")

    return result

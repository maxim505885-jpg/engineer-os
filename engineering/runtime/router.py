from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from engineering.core.contracts import AgentResult, AgentStatus, SpecialistTask
from engineering.core.engineer_core import AgentRuntimeAdapter
from .result_validator import RuntimeContractError, validate_agent_result

RuntimeBackend = Literal["hermes", "codex"]


@dataclass(frozen=True)
class RuntimePolicy:
    """Selects the execution backend without moving engineering rules out of ENGINEER CORE."""

    backend: RuntimeBackend = "hermes"


class EngineeringRuntimeRouter(AgentRuntimeAdapter):
    """Routes specialist execution and enforces one result contract."""

    def __init__(
        self,
        policy: RuntimePolicy,
        *,
        hermes: AgentRuntimeAdapter | None = None,
        codex: AgentRuntimeAdapter | None = None,
    ) -> None:
        self.policy = policy
        self.hermes = hermes
        self.codex = codex
        super().__init__()

    def execute(self, planned: list[SpecialistTask]) -> list[AgentResult]:
        runtime = self.hermes if self.policy.backend == "hermes" else self.codex
        if runtime is None:
            return [
                AgentResult(
                    task.task_id,
                    task.agent,
                    AgentStatus.UNCERTAINTY,
                    message=f"Runtime backend '{self.policy.backend}' is not configured.",
                )
                for task in planned
            ]

        raw_results = runtime.execute(planned)
        if len(raw_results) != len(planned):
            raise RuntimeContractError("Runtime returned a different number of results than planned tasks")

        validated: list[AgentResult] = []
        for task, result in zip(planned, raw_results):
            try:
                validated.append(validate_agent_result(task, result))
            except RuntimeContractError as exc:
                validated.append(
                    AgentResult(
                        task.task_id,
                        task.agent,
                        AgentStatus.ERROR,
                        message=f"Runtime contract violation: {exc}",
                    )
                )
        return validated

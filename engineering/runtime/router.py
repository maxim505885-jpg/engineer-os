from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from engineering.core.contracts import AgentResult, AgentStatus, SpecialistTask
from engineering.core.engineer_core import AgentRuntimeAdapter

from .hermes_adapter import HermesRuntimeAdapter

RuntimeBackend = Literal["hermes", "codex"]


@dataclass(frozen=True)
class RuntimePolicy:
    """Selects the execution backend without moving engineering rules out of ENGINEER CORE."""

    backend: RuntimeBackend = "hermes"


class EngineeringRuntimeRouter(AgentRuntimeAdapter):
    """Routes specialist execution to Hermes or Codex behind one ENGINEER OS boundary."""

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
        return runtime.execute(planned)

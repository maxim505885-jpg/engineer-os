"""Optional orchestration boundary for graph runtimes such as LangGraph.

External orchestrators may schedule known ENGINEER OS agents, but cannot
manufacture engineering acceptance or bypass EngineerCore.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


class OrchestrationBoundaryError(RuntimeError):
    pass


@dataclass(frozen=True)
class OrchestrationStep:
    agent: str
    reason: str | None = None


class ExternalGraphOrchestrator:
    def __init__(self, propose_next: Callable[[tuple[str, ...], tuple[str, ...]], OrchestrationStep]):
        self._propose_next = propose_next

    def next_step(self, planned_agents: tuple[str, ...], completed_agents: tuple[str, ...]) -> OrchestrationStep:
        if not planned_agents:
            raise OrchestrationBoundaryError("planned agents are required")
        step = self._propose_next(planned_agents, completed_agents)
        if not isinstance(step, OrchestrationStep):
            raise OrchestrationBoundaryError("orchestrator returned invalid step")
        if step.agent not in planned_agents:
            raise OrchestrationBoundaryError("orchestrator selected an unplanned agent")
        if step.agent in completed_agents:
            raise OrchestrationBoundaryError("orchestrator selected an already completed agent")
        return step

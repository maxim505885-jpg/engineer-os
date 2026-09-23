from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .contracts import AgentResult, AgentStatus, EngineerTask
from .engineer_core import AgentRuntimeAdapter, EngineerCore


@dataclass(frozen=True)
class RunSummary:
    task_id: str
    status: AgentStatus
    results: tuple[AgentResult, ...]
    completed_agents: tuple[str, ...]
    blocking_agents: tuple[str, ...]


class EngineerRunner:
    """Single entry point for running one complete ENGINEER OS task."""

    def __init__(self, core: EngineerCore | None = None) -> None:
        self.core = core or EngineerCore()

    def run(self, task: EngineerTask, runtime: AgentRuntimeAdapter) -> RunSummary:
        state = self.core.run(task, runtime)
        results = tuple(state.results)
        expected = {item.agent for item in state.planned}
        completed = tuple(result.agent for result in results if result.agent in expected)
        blocking = tuple(
            result.agent
            for result in results
            if result.status in {AgentStatus.ERROR, AgentStatus.BLOCK}
        )
        return RunSummary(
            task_id=task.task_id,
            status=self.core.final_status(state),
            results=results,
            completed_agents=completed,
            blocking_agents=blocking,
        )

    @staticmethod
    def summarize(summary: RunSummary) -> dict:
        return {
            "task_id": summary.task_id,
            "status": summary.status.value,
            "completed_agents": list(summary.completed_agents),
            "blocking_agents": list(summary.blocking_agents),
            "results": [result.as_dict() for result in summary.results],
        }

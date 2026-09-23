from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class AgentStatus(str, Enum):
    PASS = "PASS"
    ACCEPTED = "ACCEPTED"
    ACCEPTED_ALTERNATIVE = "ACCEPTED_ALTERNATIVE"
    WARNING = "WARNING"
    UNCERTAINTY = "UNCERTAINTY"
    ERROR = "ERROR"
    BLOCK = "BLOCK"


@dataclass(frozen=True)
class MaterialRef:
    id: str
    kind: str
    name: str
    uri: str | None = None


@dataclass(frozen=True)
class EngineerTask:
    task_id: str
    tz: str
    materials: tuple[MaterialRef, ...] = ()
    requested_checks: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SpecialistTask:
    task_id: str
    agent: str
    skill: str
    inputs: tuple[MaterialRef, ...]
    purpose: str


@dataclass(frozen=True)
class AgentResult:
    task_id: str
    agent: str
    status: AgentStatus
    findings: tuple[dict[str, Any], ...] = ()
    evidence_ids: tuple[str, ...] = ()
    message: str | None = None

    @property
    def blocks_progress(self) -> bool:
        return self.status in {AgentStatus.ERROR, AgentStatus.BLOCK}

    @property
    def has_findings(self) -> bool:
        return bool(self.findings)

    def as_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "agent": self.agent,
            "status": self.status.value,
            "findings": list(self.findings),
            "evidence_ids": list(self.evidence_ids),
            "message": self.message,
        }

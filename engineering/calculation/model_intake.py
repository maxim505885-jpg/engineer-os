"""Fail-closed intake gate for LIRA/SCAD structural model review.

This module proves only that the minimum review artifacts are present and
source-hashed. READY_FOR_SEMANTIC_REVIEW is never engineering acceptance.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re


_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class CalculationArtifactRole(str, Enum):
    MODEL = "MODEL"
    GEOMETRY = "GEOMETRY"
    MATERIALS_SECTIONS = "MATERIALS_SECTIONS"
    LOADS_COMBINATIONS = "LOADS_COMBINATIONS"
    SUPPORTS_RELEASES = "SUPPORTS_RELEASES"
    UNITS = "UNITS"
    SOLVER_LOG = "SOLVER_LOG"
    RESULTS = "RESULTS"
    ACTUAL_STRUCTURE_REFERENCE = "ACTUAL_STRUCTURE_REFERENCE"


@dataclass(frozen=True)
class CalculationArtifact:
    artifact_id: str
    role: CalculationArtifactRole
    source_sha256: str
    source_ref: str

    def __post_init__(self) -> None:
        if not self.artifact_id.strip() or not self.source_ref.strip():
            raise ValueError("calculation artifact identity and source_ref are required")
        if not _SHA256.fullmatch(self.source_sha256):
            raise ValueError("calculation artifact SHA-256 must be 64 lowercase hex characters")


@dataclass(frozen=True)
class CalculationIntakeResult:
    status: str
    missing_roles: tuple[CalculationArtifactRole, ...]
    artifact_ids: tuple[str, ...]


_REQUIRED = tuple(CalculationArtifactRole)


def audit_calculation_model_intake(
    artifacts: tuple[CalculationArtifact, ...],
) -> CalculationIntakeResult:
    if not artifacts:
        return CalculationIntakeResult("BLOCK", _REQUIRED, ())

    ids = tuple(item.artifact_id for item in artifacts)
    if len(set(ids)) != len(ids):
        raise ValueError("calculation artifact IDs must be unique")

    present = {item.role for item in artifacts}
    missing = tuple(role for role in _REQUIRED if role not in present)
    return CalculationIntakeResult(
        "BLOCK" if missing else "READY_FOR_SEMANTIC_REVIEW",
        missing,
        ids,
    )

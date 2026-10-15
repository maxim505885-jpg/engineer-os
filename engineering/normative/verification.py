"""Structured normative verification gate.

A citation is not proof. This boundary only marks a record ready for expert
verification when the full normative comparison chain is explicit.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NormativeVerificationRecord:
    document: str
    edition: str
    scope: str
    clause: str
    requirement: str
    actual_condition: str
    evidence_ids: tuple[str, ...]
    comparison: str
    conclusion: str

    def missing_fields(self) -> tuple[str, ...]:
        values = {
            "document": self.document,
            "edition": self.edition,
            "scope": self.scope,
            "clause": self.clause,
            "requirement": self.requirement,
            "actual_condition": self.actual_condition,
            "comparison": self.comparison,
            "conclusion": self.conclusion,
        }
        missing = [name for name, value in values.items() if not isinstance(value,str) or not value.strip() or len(value)>10000]
        valid_ids=isinstance(self.evidence_ids,(tuple,list)) and 0<len(self.evidence_ids)<=100 and all(isinstance(item,str) and item.strip() and len(item)<=200 for item in self.evidence_ids)
        if not valid_ids:
            missing.append("evidence_ids")
        if valid_ids and len(set(self.evidence_ids)) != len(self.evidence_ids):
            missing.append("evidence_ids_unique")
        return tuple(missing)


@dataclass(frozen=True)
class NormativeGateResult:
    status: str
    missing_fields: tuple[str, ...]
    evidence_ids: tuple[str, ...]


def gate_normative_verification(record: NormativeVerificationRecord) -> NormativeGateResult:
    if not isinstance(record,NormativeVerificationRecord):
        raise ValueError('typed normative record required')
    missing = record.missing_fields()
    return NormativeGateResult(
        status="BLOCK" if missing else "READY_FOR_EXPERT_VERIFICATION",
        missing_fields=missing,
        evidence_ids=tuple(record.evidence_ids) if 'evidence_ids' not in missing else (),
    )

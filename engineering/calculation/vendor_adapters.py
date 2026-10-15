"""Adapters for documented LIRA-FEM/SCAD text-export boundaries.

These adapters never infer proprietary binary semantics. They normalize only
explicit, source-bound data supplied by a documented API/text-export bridge.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re

_SHA256=re.compile(r"^[0-9a-f]{64}$")
_REQUIRED=("GEOMETRY","MATERIALS_SECTIONS","LOADS_COMBINATIONS","SUPPORTS_RELEASES","UNITS")

@dataclass(frozen=True)
class SolverSourceSnapshot:
    source_kind:str
    source_version:str
    source_sha256:str
    sections:dict[str,list[dict]]

    def __post_init__(self):
        if self.source_kind not in {"LIRA_FEM_API","LIRA_PROCESSOR_TEXT","SCAD_TEXT_ARCHIVE"}:
            raise ValueError("unsupported documented calculation source")
        if not isinstance(self.source_version,str) or not self.source_version.strip() or len(self.source_version)>200:
            raise ValueError("source version required")
        if not isinstance(self.source_sha256,str) or not _SHA256.fullmatch(self.source_sha256):
            raise ValueError("source sha256 required")
        if not isinstance(self.sections,dict) or len(self.sections)>32:
            raise ValueError("bounded sections required")
        for name,records in self.sections.items():
            if not isinstance(name,str) or not name.strip() or len(name)>100:
                raise ValueError("invalid section name")
            if not isinstance(records,list) or len(records)>100_000 or any(not isinstance(r,dict) for r in records):
                raise ValueError("bounded section records required")

def _section_sha(records)->str:
    raw=json.dumps(records,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode()
    return hashlib.sha256(raw).hexdigest()

def to_exchange_manifest(snapshot:SolverSourceSnapshot)->dict:
    if not isinstance(snapshot,SolverSourceSnapshot):
        raise ValueError("typed solver source snapshot required")
    sections=[]
    for name in _REQUIRED:
        if name in snapshot.sections:
            records=snapshot.sections[name]
            sections.append(dict(name=name,source_sha256=_section_sha(records),records=records))
    return dict(format="ENGINEER_OS_CALC_EXCHANGE",version=1,
                source_sha256=snapshot.source_sha256,sections=sections)

def audit_documented_source(snapshot:SolverSourceSnapshot)->dict:
    present=set(snapshot.sections)
    missing=[name for name in _REQUIRED if name not in present]
    extras=sorted(present-set(_REQUIRED)-{"RESULTS","SOLVER_LOG","META"})
    empty=[name for name in _REQUIRED if name in snapshot.sections and not snapshot.sections[name]]
    reasons=[]
    if missing: reasons.append("DOCUMENTED_SOURCE_SECTIONS_MISSING")
    if empty: reasons.append("DOCUMENTED_SOURCE_SECTION_EMPTY")
    if extras: reasons.append("UNRECOGNIZED_SOURCE_SECTIONS")
    if reasons:
        return dict(status="BLOCK",missing_sections=missing,empty_sections=empty,
                    extra_sections=extras,reasons=reasons,acceptance_granted=False)
    return dict(status="READY_FOR_EXCHANGE_NORMALIZATION",missing_sections=[],
                empty_sections=[],extra_sections=[],
                reasons=["SOURCE_ADAPTER_DOES_NOT_PROVE_ENGINEERING_TRUTH"],
                acceptance_granted=False)

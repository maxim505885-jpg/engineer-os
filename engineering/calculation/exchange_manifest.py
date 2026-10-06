"""Deterministic parser for ENGINEER OS calculation exchange manifests.

This is an ENGINEER OS interchange format, not a native LIR/SCAD decoder.
It exists so a concrete solver/export adapter can hand off source-bound,
hash-addressed semantic sections without guessing proprietary binary payloads.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re

_SHA256=re.compile(r"^[0-9a-f]{64}$")
_SECTIONS=("GEOMETRY","MATERIALS_SECTIONS","LOADS_COMBINATIONS","SUPPORTS_RELEASES","UNITS")
_MAX_BYTES=2_000_000

@dataclass(frozen=True)
class ExchangeSection:
    name:str
    source_sha256:str
    records:tuple[dict,...]

    def __post_init__(self):
        if self.name not in _SECTIONS: raise ValueError("unsupported exchange section")
        if not isinstance(self.source_sha256,str) or not _SHA256.fullmatch(self.source_sha256):
            raise ValueError("section source sha256 required")
        if not isinstance(self.records,(tuple,list)) or len(self.records)>100_000 or any(not isinstance(r,dict) for r in self.records):
            raise ValueError("bounded exchange records required")

@dataclass(frozen=True)
class CalculationExchangeManifest:
    format:str
    version:int
    source_sha256:str
    sections:tuple[ExchangeSection,...]

def canonical_sha256(payload)->str:
    raw=json.dumps(payload,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode()
    return hashlib.sha256(raw).hexdigest()

def parse_exchange_manifest(raw:bytes|str)->CalculationExchangeManifest:
    if isinstance(raw,str): raw=raw.encode()
    if not isinstance(raw,(bytes,bytearray)) or not raw or len(raw)>_MAX_BYTES:
        raise ValueError("bounded UTF-8 exchange manifest required")
    try:
        body=json.loads(bytes(raw).decode("utf-8"))
    except Exception as exc:
        raise ValueError("invalid UTF-8 JSON exchange manifest") from exc
    if not isinstance(body,dict) or set(body)!={"format","version","source_sha256","sections"}:
        raise ValueError("invalid exchange manifest fields")
    if body["format"]!="ENGINEER_OS_CALC_EXCHANGE" or body["version"]!=1:
        raise ValueError("unsupported exchange manifest format/version")
    if not isinstance(body["source_sha256"],str) or not _SHA256.fullmatch(body["source_sha256"]):
        raise ValueError("manifest source sha256 required")
    if not isinstance(body["sections"],list) or len(body["sections"])>len(_SECTIONS):
        raise ValueError("bounded sections required")
    seen=set();sections=[]
    for item in body["sections"]:
        if not isinstance(item,dict) or set(item)!={"name","source_sha256","records"}:
            raise ValueError("invalid exchange section fields")
        section=ExchangeSection(item["name"],item["source_sha256"],tuple(item["records"]))
        if section.name in seen: raise ValueError("duplicate exchange section")
        seen.add(section.name);sections.append(section)
    return CalculationExchangeManifest(body["format"],body["version"],body["source_sha256"],tuple(sections))

def audit_exchange_manifest(manifest:CalculationExchangeManifest)->dict:
    if not isinstance(manifest,CalculationExchangeManifest):
        raise ValueError("typed exchange manifest required")
    present={s.name for s in manifest.sections}
    missing=[name for name in _SECTIONS if name not in present]
    empty=[s.name for s in manifest.sections if not s.records]
    reasons=[]
    if missing: reasons.append("EXCHANGE_SECTIONS_MISSING")
    if empty: reasons.append("EXCHANGE_SECTION_EMPTY")
    status="BLOCK" if reasons else "READY_FOR_SEMANTIC_CROSSCHECK"
    return dict(status=status,missing_sections=missing,empty_sections=empty,
                reasons=reasons or ["NATIVE_SOLVER_INPUT_NOT_PROVEN","ACTUAL_STRUCTURE_NOT_VERIFIED"],
                acceptance_granted=False)

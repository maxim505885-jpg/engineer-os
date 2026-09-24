from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

@dataclass(frozen=True)
class ModelRequest:
    prompt: str
    system: str = ""
    model: str | None = None
    temperature: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class ModelResponse:
    text: str
    provider: str
    model: str
    raw: dict[str, Any] = field(default_factory=dict)

class ModelProvider(Protocol):
    name: str
    def available(self) -> bool: ...
    def generate(self, request: ModelRequest) -> ModelResponse: ...

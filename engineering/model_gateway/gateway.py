from __future__ import annotations

from .contracts import ModelProvider, ModelRequest, ModelResponse

class NoAvailableModelProvider(RuntimeError):
    pass

class ModelGateway:
    """Route model work without coupling ENGINEER OS to one vendor."""
    def __init__(self, providers: list[ModelProvider]):
        self.providers = providers

    def generate(self, request: ModelRequest) -> ModelResponse:
        failures: list[str] = []
        for provider in self.providers:
            try:
                if not provider.available():
                    failures.append(f"{provider.name}: unavailable")
                    continue
                return provider.generate(request)
            except Exception as exc:
                failures.append(f"{provider.name}: {type(exc).__name__}: {exc}")
        raise NoAvailableModelProvider("No model provider available: " + "; ".join(failures))

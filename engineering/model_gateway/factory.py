from __future__ import annotations

import os

from .freellmapi import FreeLLMAPIProvider
from .gateway import ModelGateway
from .ollama import OllamaProvider


def build_model_gateway_from_env() -> ModelGateway:
    """Build the local/free model gateway from environment policy.

    Default order is FreeLLMAPI first, then local Ollama. Provider fallback is
    model transport only; ENGINEER OS engineering validation remains unchanged.
    Set ENGINEER_OS_MODEL_PROVIDERS=ollama to force local-only operation.
    """
    raw = os.getenv("ENGINEER_OS_MODEL_PROVIDERS", "freellmapi,ollama")
    names = [name.strip().lower() for name in raw.split(",") if name.strip()]

    providers = []
    for name in names:
        if name == "freellmapi":
            providers.append(FreeLLMAPIProvider())
        elif name == "ollama":
            providers.append(OllamaProvider())
        else:
            raise ValueError(f"Unknown ENGINEER OS model provider: {name}")

    if not providers:
        raise ValueError("ENGINEER_OS_MODEL_PROVIDERS must contain at least one provider")

    return ModelGateway(providers)

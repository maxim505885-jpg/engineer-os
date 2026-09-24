from __future__ import annotations

from unittest.mock import patch

from engineering.model_gateway.factory import build_model_gateway_from_env


def test_factory_defaults_to_freellmapi_then_ollama():
    with patch.dict("os.environ", {}, clear=True):
        gateway = build_model_gateway_from_env()
    assert [provider.name for provider in gateway.providers] == ["freellmapi", "ollama"]


def test_factory_can_force_ollama_only():
    with patch.dict("os.environ", {"ENGINEER_OS_MODEL_PROVIDERS": "ollama"}, clear=True):
        gateway = build_model_gateway_from_env()
    assert [provider.name for provider in gateway.providers] == ["ollama"]


def test_factory_rejects_unknown_provider():
    with patch.dict("os.environ", {"ENGINEER_OS_MODEL_PROVIDERS": "freellmapi,unknown"}, clear=True):
        try:
            build_model_gateway_from_env()
        except ValueError as exc:
            assert "Unknown ENGINEER OS model provider" in str(exc)
        else:
            raise AssertionError("Expected unknown provider to fail")

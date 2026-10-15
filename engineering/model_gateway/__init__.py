"""Model gateway boundaries for local and remote OpenAI-compatible runtimes."""

from .openai_compatible import ModelGatewayError, OpenAICompatibleGateway

__all__ = ["ModelGatewayError", "OpenAICompatibleGateway"]

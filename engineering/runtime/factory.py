from __future__ import annotations

import os

from .open_webui_adapter import (
    OpenWebUIClient,
    OpenWebUIExecutionConfig,
    OpenWebUIRuntimeAdapter,
)
from .router import EngineeringRuntimeRouter, RuntimePolicy


def build_openwebui_runtime_from_env() -> EngineeringRuntimeRouter:
    """Build the free/local Open WebUI runtime boundary from environment variables.

    Open WebUI remains the transport/model gateway; ENGINEER OS retains
    engineering result validation and truth semantics. No paid provider is
    selected here.
    """
    config = OpenWebUIExecutionConfig.from_env()
    if not config.model.strip():
        raise RuntimeError(
            "ENGINEER_OS_OPEN_WEBUI_MODEL is required for the Open WebUI runtime"
        )

    if int(os.getenv("ENGINEER_OS_OPEN_WEBUI_TIMEOUT", "1800")) <= 0:
        raise RuntimeError("ENGINEER_OS_OPEN_WEBUI_TIMEOUT must be positive")

    runtime = OpenWebUIRuntimeAdapter(OpenWebUIClient(config))
    return EngineeringRuntimeRouter(
        RuntimePolicy(backend="openwebui"),
        openwebui=runtime,
    )

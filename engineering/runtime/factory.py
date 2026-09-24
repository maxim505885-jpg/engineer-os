from __future__ import annotations

import os

from .open_webui_adapter import OpenWebUIExecutionConfig, OpenWebUIRuntimeAdapter
from .router import EngineeringRuntimeRouter, RuntimePolicy


def build_openwebui_runtime_from_env() -> EngineeringRuntimeRouter:
    """Build the free/local Open WebUI runtime boundary from environment variables.

    ENGINEER_OS_OPEN_WEB_UI_MODEL is required because Open WebUI may expose
    multiple local models. No paid provider or API key is introduced here.
    """
    model = os.getenv("ENGINEER_OS_OPEN_WEBUI_MODEL", "").strip()
    if not model:
        raise RuntimeError(
            "ENGINEER_OS_OPEN_WEBUI_MODEL is required for the Open WebUI runtime"
        )

    config = OpenWebUIExecutionConfig(
        base_url=os.getenv("ENGINEER_OS_OPEN_WEBUI_URL", "http://127.0.0.1:8080"),
        api_key=os.getenv("ENGINEER_OS_OPEN_WEBUI_API_KEY") or None,
        model=model,
        timeout_seconds=float(
            os.getenv("ENGINEER_OS_OPEN_WEBUI_TIMEOUT", "1800")
        ),
    )
    runtime = OpenWebUIRuntimeAdapter.from_config(config)
    return EngineeringRuntimeRouter(
        RuntimePolicy(backend="openwebui"),
        openwebui=runtime,
    )

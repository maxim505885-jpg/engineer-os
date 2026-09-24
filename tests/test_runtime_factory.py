import os
import unittest
from unittest.mock import patch

from engineering.runtime.factory import build_openwebui_runtime_from_env
from engineering.runtime.open_webui_adapter import OpenWebUIRuntimeAdapter
from engineering.runtime.router import EngineeringRuntimeRouter


class OpenWebUIRuntimeFactoryTests(unittest.TestCase):
    def test_factory_requires_model(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(RuntimeError):
                build_openwebui_runtime_from_env()

    def test_factory_builds_router_from_environment(self):
        env = {
            "ENGINEER_OS_OPEN_WEBUI_MODEL": "qwen3:8b",
            "ENGINEER_OS_OPEN_WEBUI_URL": "http://127.0.0.1:8080",
            "ENGINEER_OS_OPEN_WEBUI_TIMEOUT": "600",
        }
        with patch.dict(os.environ, env, clear=True):
            runtime = build_openwebui_runtime_from_env()

        self.assertIsInstance(runtime, EngineeringRuntimeRouter)
        self.assertEqual(runtime.policy.backend, "openwebui")
        self.assertIsInstance(runtime.openwebui, OpenWebUIRuntimeAdapter)
        self.assertEqual(runtime.openwebui.client.config.model, "qwen3:8b")
        self.assertEqual(runtime.openwebui.client.config.timeout_seconds, 600)

if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from .contracts import ModelRequest, ModelResponse

class OllamaProvider:
    name = "ollama"

    def __init__(self, base_url: str | None = None, default_model: str | None = None, timeout: float = 120.0):
        self.base_url = (base_url or os.getenv("ENGINEER_OS_OLLAMA_URL", "http://127.0.0.1:11434")).rstrip("/")
        self.default_model = default_model or os.getenv("ENGINEER_OS_OLLAMA_MODEL", "")
        self.timeout = timeout

    def available(self) -> bool:
        try:
            with urllib.request.urlopen(f"{self.base_url}/api/tags", timeout=3) as response:
                return response.status == 200
        except (OSError, urllib.error.URLError):
            return False

    def generate(self, request: ModelRequest) -> ModelResponse:
        model = request.model or self.default_model
        if not model:
            raise ValueError("Ollama model is required")
        prompt = request.prompt if not request.system else request.system + "\n\n" + request.prompt
        payload = json.dumps({"model": model, "prompt": prompt, "stream": False, "options": {"temperature": request.temperature}}).encode("utf-8")
        req = urllib.request.Request(f"{self.base_url}/api/generate", data=payload, headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                raw = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Ollama HTTP {exc.code}: {body}") from exc
        return ModelResponse(str(raw.get("response", "")), self.name, model, raw)

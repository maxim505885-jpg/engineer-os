from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from .contracts import ModelRequest, ModelResponse


class FreeLLMAPIProvider:
    name = "freellmapi"

    def __init__(self, base_url=None, api_key=None, default_model=None, timeout=180.0):
        self.base_url = (base_url or os.getenv("ENGINEER_OS_FREELLMAPI_URL", "http://127.0.0.1:3001/v1")).rstrip("/")
        self.api_key = api_key or os.getenv("ENGINEER_OS_FREELLMAPI_API_KEY", "")
        self.default_model = default_model or os.getenv("ENGINEER_OS_FREELLMAPI_MODEL", "auto")
        self.timeout = timeout

    def available(self):
        try:
            request = urllib.request.Request(f"{self.base_url}/models", headers=self._headers(), method="GET")
            with urllib.request.urlopen(request, timeout=3) as response:
                return response.status == 200
        except (OSError, urllib.error.URLError):
            return False

    def generate(self, request):
        model = request.model or self.default_model
        if not model:
            raise ValueError("FreeLLMAPI model is required")
        messages = []
        if request.system:
            messages.append({"role": "system", "content": request.system})
        messages.append({"role": "user", "content": request.prompt})
        payload = json.dumps({"model": model, "messages": messages, "temperature": request.temperature, "stream": False}).encode("utf-8")
        http_request = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=payload,
            headers={**self._headers(), "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(http_request, timeout=self.timeout) as response:
                raw = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"FreeLLMAPI HTTP {exc.code}: {body}") from exc
        try:
            response_text = str(raw["choices"][0]["message"]["content"])
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError("FreeLLMAPI returned an invalid chat completion") from exc
        response_model = str(raw.get("model") or model)
        return ModelResponse(text=response_text, provider=self.name, model=response_model, raw=raw)

    def _headers(self):
        headers = {"Accept": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

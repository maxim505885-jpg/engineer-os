"""Minimal OpenAI-compatible gateway for local ENGINEER OS models."""

from __future__ import annotations

import json
from urllib import error, request


class ModelGatewayError(RuntimeError):
    pass


class OpenAICompatibleGateway:
    def __init__(self, base_url: str, *, api_key: str | None = None, opener=None) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._opener = opener or request.urlopen
        local = self._base_url.startswith(("http://127.0.0.1", "http://localhost"))
        private = ".railway.internal" in self._base_url
        if not (self._base_url.startswith("https://") or local or private):
            raise ValueError("model gateway requires https or an explicitly local/private HTTP endpoint")

    def chat(self, *, model: str, messages: tuple[dict[str, str], ...], temperature: float = 0.0) -> str:
        if not model.strip():
            raise ValueError("model is required")
        if not messages:
            raise ValueError("messages are required")
        for message in messages:
            if message.get("role") not in {"system", "user", "assistant"} or not str(message.get("content", "")).strip():
                raise ValueError("invalid chat message")

        payload = json.dumps(
            {"model": model, "messages": list(messages), "temperature": temperature, "stream": False},
            ensure_ascii=False,
        ).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = "Bearer " + self._api_key
        req = request.Request(
            self._base_url + "/v1/chat/completions",
            data=payload,
            method="POST",
            headers=headers,
        )
        try:
            with self._opener(req, timeout=180) as response:
                body = json.loads(response.read().decode("utf-8"))
        except (error.HTTPError, error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise ModelGatewayError("model gateway request failed") from exc
        try:
            content = body["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ModelGatewayError("model gateway returned an invalid response") from exc
        if not isinstance(content, str) or not content.strip():
            raise ModelGatewayError("model gateway returned empty content")
        return content

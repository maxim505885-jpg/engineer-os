"""Minimal OpenAI-compatible gateway for local ENGINEER OS models."""

from __future__ import annotations

import json
from urllib import error, request
from urllib.parse import urlsplit

MAX_RESPONSE_BYTES = 2 * 1024 * 1024
MAX_REPLY_CHARS = 32000


class ModelGatewayError(RuntimeError):
    pass


class _NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class OpenAICompatibleGateway:
    def __init__(self, base_url: str, *, api_key: str | None = None, opener=None) -> None:
        try:
            parts = urlsplit(base_url)
            port = parts.port
            local = parts.hostname in {"127.0.0.1", "localhost", "::1"}
            private = bool(parts.hostname and parts.hostname.endswith(".railway.internal"))
            if (parts.scheme not in {"http", "https"} or not parts.hostname
                    or parts.username is not None or parts.password is not None
                    or parts.query or parts.fragment or port == 0
                    or any(ch.isspace() or ord(ch) < 32 for ch in base_url)
                    or (parts.scheme == "http" and not (local or private))):
                raise ValueError
        except (ValueError, TypeError, AttributeError):
            raise ValueError("model gateway requires https or an explicitly local/private HTTP endpoint without credentials, query or fragment") from None
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._opener = opener or request.build_opener(_NoRedirect()).open

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
                raw = response.read(MAX_RESPONSE_BYTES + 1)
                if len(raw) > MAX_RESPONSE_BYTES:
                    raise ModelGatewayError("model gateway response exceeds 2 MiB")
                body = json.loads(raw.decode("utf-8"))
        except (error.HTTPError, error.URLError, TimeoutError, ValueError) as exc:
            raise ModelGatewayError("model gateway request failed") from exc
        try:
            choice = body["choices"][0]
            content = choice["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ModelGatewayError("model gateway returned an invalid response") from exc
        if not isinstance(content, str) or not content.strip():
            raise ModelGatewayError("model gateway returned empty content")
        if "finish_reason" in choice and choice["finish_reason"] != "stop":
            raise ModelGatewayError("model gateway returned an incomplete completion")
        if len(content) > MAX_REPLY_CHARS:
            raise ModelGatewayError("model gateway reply exceeds 32,000 characters")
        return content

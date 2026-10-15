"""Bounded local JSON transport with no proxy or redirect forwarding."""
from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener


class IntegrationError(RuntimeError):
    pass


def local_url(value: str) -> str:
    try:
        parts = urlsplit(value)
        port = parts.port
        if (parts.scheme != "http" or parts.hostname not in {"127.0.0.1", "::1", "localhost"}
                or parts.username is not None or parts.password is not None
                or parts.path not in {"", "/"} or parts.query or parts.fragment
                or port == 0):
            raise ValueError
    except (ValueError, TypeError):
        raise IntegrationError("A loopback HTTP origin without credentials or path is required") from None
    return value.rstrip("/")


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def get_local_json(origin: str, path: str, *, secret: str = "", timeout: float = 10) -> dict:
    origin = local_url(origin)
    if not path.startswith("/") or path.startswith("//"):
        raise IntegrationError("Invalid local API path")
    headers = {"Accept": "application/json"}
    if secret:
        headers["Authorization"] = "Bearer " + secret
    opener = build_opener(ProxyHandler({}), _NoRedirect())
    try:
        with opener.open(Request(origin + path, headers=headers), timeout=timeout) as response:
            raw = response.read(1_048_577)
        if len(raw) > 1_048_576:
            raise IntegrationError("Local response exceeds 1 MiB")
        result = json.loads(raw)
    except (HTTPError, URLError, OSError, ValueError):
        raise IntegrationError("Local service unavailable or returned invalid JSON/HTTP response") from None
    if not isinstance(result, dict):
        raise IntegrationError("Local response must be a JSON object")
    return result

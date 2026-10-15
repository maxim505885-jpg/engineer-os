"""HTTP client for the official OSS DeepDoc DLA/OCR/TSR service.

DeepDoc output is untrusted document-analysis data. It is not Evidence and it
cannot create engineering conclusions or AgentResult acceptance.
"""

from __future__ import annotations

import json
from urllib import error, request
from uuid import uuid4


class DeepDocServiceError(RuntimeError):
    pass


class DeepDocServiceClient:
    _MODES = {"dla", "ocr", "tsr"}

    def __init__(self, base_url: str, opener=None) -> None:
        self._base_url = base_url.rstrip("/")
        self._opener = opener or request.urlopen
        if not (
            self._base_url.startswith("https://")
            or self._base_url.startswith("http://127.0.0.1")
            or self._base_url.startswith("http://localhost")
            or ".railway.internal" in self._base_url
        ):
            raise ValueError("DeepDoc URL must use https or an explicitly local/private HTTP endpoint")

    def health(self) -> bool:
        req = request.Request(self._base_url + "/health", method="GET")
        try:
            with self._opener(req, timeout=10) as response:
                return response.read().decode("utf-8").strip().lower() == "ok"
        except (error.HTTPError, error.URLError, TimeoutError) as exc:
            raise DeepDocServiceError("DeepDoc health check failed") from exc

    def predict(self, mode: str, jpeg_bytes: bytes) -> object:
        if mode not in self._MODES:
            raise ValueError("DeepDoc mode must be dla, ocr, or tsr")
        if not jpeg_bytes or not jpeg_bytes.startswith(b"\xff\xd8"):
            raise ValueError("DeepDoc prediction requires JPEG bytes")

        boundary = "engineeros-" + uuid4().hex
        body = (
            f"--{boundary}\r\n"
            'Content-Disposition: form-data; name="request"; filename="page.jpg"\r\n'
            "Content-Type: image/jpeg\r\n\r\n"
        ).encode("ascii") + jpeg_bytes + f"\r\n--{boundary}--\r\n".encode("ascii")
        req = request.Request(
            self._base_url + "/predict/" + mode,
            data=body,
            method="POST",
            headers={"Content-Type": "multipart/form-data; boundary=" + boundary},
        )
        try:
            with self._opener(req, timeout=120) as response:
                raw = response.read().decode("utf-8")
        except (error.HTTPError, error.URLError, TimeoutError) as exc:
            raise DeepDocServiceError("DeepDoc prediction failed") from exc
        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            raise DeepDocServiceError("DeepDoc returned invalid JSON") from exc

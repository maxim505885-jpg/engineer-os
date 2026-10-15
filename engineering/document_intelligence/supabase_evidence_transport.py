"""Service-role transport for the validated document-evidence RPC."""

from __future__ import annotations

import json
import os
from urllib import error, request


class SupabaseEvidenceTransportError(RuntimeError):
    pass


class SupabaseEvidenceTransport:
    def __init__(self, base_url: str, service_role_key: str, opener=None) -> None:
        self._base_url = base_url.rstrip("/")
        self._key = service_role_key
        self._opener = opener or request.urlopen
        if not self._base_url.startswith("https://"):
            raise ValueError("Supabase URL must use https")
        if not self._key.strip():
            raise ValueError("service role key is required")

    def __call__(self, table: str, row: dict[str, str], conflict: tuple[str, ...]):
        if table != "evidence":
            raise SupabaseEvidenceTransportError("only evidence persistence is allowed")
        if conflict != ("document_id", "evidence_code"):
            raise SupabaseEvidenceTransportError("unexpected evidence conflict key")

        sha = _source_sha(row["source_ref"])
        payload = {
            "p_project_id": row["project_id"],
            "p_document_id": row["document_id"],
            "p_source_sha256": sha,
            "p_evidence_code": row["evidence_code"],
            "p_data_class": row["data_class"],
            "p_description": row["description"],
            "p_source_ref": row["source_ref"],
            "p_confidence": row["confidence"],
        }
        req = request.Request(
            self._base_url + "/rest/v1/rpc/persist_validated_document_evidence",
            data=json.dumps(payload).encode("utf-8"),
            method="POST",
            headers={
                "apikey": self._key,
                "Authorization": "Bearer " + self._key,
                "Content-Type": "application/json",
            },
        )
        try:
            with self._opener(req, timeout=30) as response:
                body = response.read().decode("utf-8")
        except (error.HTTPError, error.URLError, TimeoutError) as exc:
            raise SupabaseEvidenceTransportError("validated evidence RPC failed") from exc
        try:
            evidence_id = json.loads(body)
        except json.JSONDecodeError as exc:
            raise SupabaseEvidenceTransportError("validated evidence RPC returned invalid JSON") from exc
        if not isinstance(evidence_id, str) or not evidence_id:
            raise SupabaseEvidenceTransportError("validated evidence RPC returned invalid id")
        return evidence_id


def _source_sha(source_ref: str) -> str:
    for part in source_ref.split(";"):
        if part.startswith("sha256:"):
            value = part.removeprefix("sha256:")
            if len(value) == 64 and all(ch in "0123456789abcdef" for ch in value):
                return value
    raise SupabaseEvidenceTransportError("source_ref has no valid sha256")


def production_evidence_transport() -> SupabaseEvidenceTransport:
    url = os.environ.get("SUPABASE_URL", "")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
    return SupabaseEvidenceTransport(url, key)

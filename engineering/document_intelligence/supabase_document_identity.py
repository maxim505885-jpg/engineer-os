"""Fail-closed Supabase lookup for registered document identity."""

from __future__ import annotations

import json
import os
from urllib import error, request

from .document_registration import SourceDocumentIdentity


class SupabaseDocumentIdentityError(RuntimeError):
    pass


class SupabaseDocumentIdentityVerifier:
    def __init__(self, base_url: str, service_role_key: str, opener=None) -> None:
        self._base_url = base_url.rstrip("/")
        self._key = service_role_key
        self._opener = opener or request.urlopen
        if not self._base_url.startswith("https://"):
            raise ValueError("Supabase URL must use https")
        if not self._key.strip():
            raise ValueError("service role key is required")

    def verify(self, identity: SourceDocumentIdentity) -> None:
        payload = {
            "p_project_id": identity.project_id,
            "p_document_id": identity.document_id,
            "p_source_sha256": identity.source_sha256,
        }
        req = request.Request(
            self._base_url + "/rest/v1/rpc/assert_registered_document_identity",
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
            raise SupabaseDocumentIdentityError("document identity RPC failed") from exc
        try:
            verified = json.loads(body)
        except json.JSONDecodeError as exc:
            raise SupabaseDocumentIdentityError("document identity RPC returned invalid JSON") from exc
        if verified is not True:
            raise SupabaseDocumentIdentityError("registered document identity was not verified")


def production_document_identity_verifier() -> SupabaseDocumentIdentityVerifier:
    return SupabaseDocumentIdentityVerifier(
        os.environ.get("SUPABASE_URL", ""),
        os.environ.get("SUPABASE_SERVICE_ROLE_KEY", ""),
    )

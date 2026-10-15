import io
import json
import unittest
from urllib import error

from engineering.document_intelligence.document_registration import SourceDocumentIdentity
from engineering.document_intelligence.supabase_document_identity import (
    SupabaseDocumentIdentityError,
    SupabaseDocumentIdentityVerifier,
)


class _Response:
    def __init__(self, payload):
        self._body = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self._body


class SupabaseDocumentIdentityTests(unittest.TestCase):
    def setUp(self):
        self.identity = SourceDocumentIdentity(
            project_id="11111111-1111-1111-1111-111111111111",
            document_id="22222222-2222-2222-2222-222222222222",
            source_sha256="a" * 64,
        )

    def test_verified_identity_passes(self):
        requests = []
        def opener(req, timeout):
            requests.append((req, timeout))
            return _Response(True)

        verifier = SupabaseDocumentIdentityVerifier("https://example.supabase.co", "secret", opener)
        verifier.verify(self.identity)

        self.assertEqual(len(requests), 1)
        req, timeout = requests[0]
        self.assertTrue(req.full_url.endswith("/rest/v1/rpc/assert_registered_document_identity"))
        self.assertEqual(timeout, 30)
        body = json.loads(req.data.decode("utf-8"))
        self.assertEqual(body["p_document_id"], self.identity.document_id)
        self.assertEqual(body["p_source_sha256"], self.identity.source_sha256)

    def test_false_rpc_result_blocks(self):
        verifier = SupabaseDocumentIdentityVerifier(
            "https://example.supabase.co", "secret", lambda req, timeout: _Response(False)
        )
        with self.assertRaises(SupabaseDocumentIdentityError):
            verifier.verify(self.identity)

    def test_transport_failure_blocks(self):
        def opener(req, timeout):
            raise error.URLError("offline")
        verifier = SupabaseDocumentIdentityVerifier("https://example.supabase.co", "secret", opener)
        with self.assertRaises(SupabaseDocumentIdentityError):
            verifier.verify(self.identity)

    def test_invalid_json_blocks(self):
        class BadResponse(_Response):
            def read(self):
                return b"not-json"
        verifier = SupabaseDocumentIdentityVerifier(
            "https://example.supabase.co", "secret", lambda req, timeout: BadResponse(True)
        )
        with self.assertRaises(SupabaseDocumentIdentityError):
            verifier.verify(self.identity)


if __name__ == "__main__":
    unittest.main()

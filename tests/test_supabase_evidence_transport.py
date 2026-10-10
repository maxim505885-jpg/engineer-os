import io
import json
import unittest

from engineering.document_intelligence.supabase_evidence_transport import (
    SupabaseEvidenceTransport,
    SupabaseEvidenceTransportError,
)


class Response:
    def __init__(self, body):
        self._body = body
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def read(self): return self._body


class SupabaseEvidenceTransportTests(unittest.TestCase):
    def setUp(self):
        self.row = {
            "project_id": "11111111-1111-1111-1111-111111111111",
            "document_id": "22222222-2222-2222-2222-222222222222",
            "evidence_code": "doc-evidence:" + "a" * 64,
            "data_class": "UNKNOWN",
            "description": "Факт",
            "source_ref": "document:222;sha256:" + "b" * 64 + ";block:x;pages:1",
            "confidence": "PROVENANCE_VALIDATED",
        }

    def test_calls_only_validated_rpc(self):
        captured = {}
        def opener(req, timeout):
            captured["url"] = req.full_url
            captured["payload"] = json.loads(req.data)
            return Response(b'"33333333-3333-3333-3333-333333333333"')
        t = SupabaseEvidenceTransport("https://example.supabase.co", "secret", opener)
        result = t("evidence", self.row, ("document_id", "evidence_code"))
        self.assertEqual(result, "33333333-3333-3333-3333-333333333333")
        self.assertTrue(captured["url"].endswith("/rpc/persist_validated_document_evidence"))
        self.assertEqual(captured["payload"]["p_source_sha256"], "b" * 64)

    def test_wrong_table_is_blocked_before_network(self):
        t = SupabaseEvidenceTransport("https://example.supabase.co", "secret", lambda *a, **k: self.fail("network"))
        with self.assertRaises(SupabaseEvidenceTransportError):
            t("other", self.row, ("document_id", "evidence_code"))

    def test_invalid_source_hash_is_blocked(self):
        row = dict(self.row, source_ref="document:222;sha256:nope")
        t = SupabaseEvidenceTransport("https://example.supabase.co", "secret", lambda *a, **k: self.fail("network"))
        with self.assertRaises(SupabaseEvidenceTransportError):
            t("evidence", row, ("document_id", "evidence_code"))


if __name__ == "__main__":
    unittest.main()

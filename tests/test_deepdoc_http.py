import json
import unittest

from engineering.document_intelligence.deepdoc_http import DeepDocServiceClient, DeepDocServiceError


class _Response:
    def __init__(self, body):
        self.body = body
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def read(self):
        return self.body


class DeepDocServiceClientTests(unittest.TestCase):
    def test_health_requires_ok(self):
        client = DeepDocServiceClient("https://deepdoc.example", lambda req, timeout: _Response(b"ok"))
        self.assertTrue(client.health())

    def test_predict_uses_official_mode_endpoint_and_request_field(self):
        seen = []
        def opener(req, timeout):
            seen.append((req, timeout))
            return _Response(json.dumps({"result": []}).encode())
        client = DeepDocServiceClient("https://deepdoc.example", opener)
        result = client.predict("dla", b"\xff\xd8jpeg")
        self.assertEqual(result, {"result": []})
        req, timeout = seen[0]
        self.assertTrue(req.full_url.endswith("/predict/dla"))
        self.assertIn(b'name="request"', req.data)
        self.assertEqual(timeout, 120)

    def test_non_jpeg_and_unknown_mode_fail_closed(self):
        client = DeepDocServiceClient("https://deepdoc.example", lambda req, timeout: _Response(b"{}"))
        with self.assertRaises(ValueError):
            client.predict("dla", b"pdf")
        with self.assertRaises(ValueError):
            client.predict("unknown", b"\xff\xd8jpeg")

    def test_public_plain_http_is_rejected(self):
        with self.assertRaises(ValueError):
            DeepDocServiceClient("http://example.com")


if __name__ == "__main__":
    unittest.main()

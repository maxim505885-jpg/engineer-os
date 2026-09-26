import json
import unittest

from engineering.model_gateway.openai_compatible import OpenAICompatibleGateway, ModelGatewayError


class _Response:
    def __init__(self, payload):
        self.payload = payload
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def read(self):
        return json.dumps(self.payload).encode()


class ModelGatewayTests(unittest.TestCase):
    def test_local_ollama_compatible_request(self):
        seen = []
        def opener(req, timeout):
            seen.append((req, timeout))
            return _Response({"choices": [{"message": {"content": "ok"}}]})
        gateway = OpenAICompatibleGateway("http://127.0.0.1:11434", opener=opener)
        result = gateway.chat(model="qwen3:8b", messages=({"role": "user", "content": "test"},))
        self.assertEqual(result, "ok")
        req, timeout = seen[0]
        self.assertTrue(req.full_url.endswith("/v1/chat/completions"))
        self.assertEqual(timeout, 180)
        self.assertNotIn("Authorization", req.headers)

    def test_remote_plain_http_is_rejected(self):
        with self.assertRaises(ValueError):
            OpenAICompatibleGateway("http://example.com")

    def test_invalid_response_fails_closed(self):
        gateway = OpenAICompatibleGateway(
            "https://models.example",
            opener=lambda req, timeout: _Response({"unexpected": True}),
        )
        with self.assertRaises(ModelGatewayError):
            gateway.chat(model="model", messages=({"role": "user", "content": "x"},))


if __name__ == "__main__":
    unittest.main()

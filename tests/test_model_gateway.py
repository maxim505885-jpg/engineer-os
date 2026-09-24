import unittest
from unittest.mock import patch

from engineering.model_gateway.contracts import ModelRequest, ModelResponse
from engineering.model_gateway.freellmapi import FreeLLMAPIProvider
from engineering.model_gateway.gateway import ModelGateway, NoAvailableModelProvider


class FakeProvider:
    def __init__(self, name, available=True, fail=False):
        self.name = name
        self._available = available
        self._fail = fail

    def available(self):
        return self._available

    def generate(self, request):
        if self._fail:
            raise RuntimeError("boom")
        return ModelResponse("ok", self.name, request.model or "fake")


class ModelGatewayTests(unittest.TestCase):
    def test_uses_first_available_provider(self):
        result = ModelGateway([FakeProvider("offline", False), FakeProvider("ollama")]).generate(ModelRequest("hello"))
        self.assertEqual(result.provider, "ollama")

    def test_falls_back_after_provider_failure(self):
        result = ModelGateway([FakeProvider("broken", fail=True), FakeProvider("ollama")]).generate(ModelRequest("hello"))
        self.assertEqual(result.provider, "ollama")

    def test_no_provider_is_explicit_failure(self):
        with self.assertRaises(NoAvailableModelProvider):
            ModelGateway([FakeProvider("offline", False)]).generate(ModelRequest("hello"))

    @patch("engineering.model_gateway.freellmapi.urllib.request.urlopen")
    def test_freellmapi_parses_openai_compatible_response(self, urlopen):
        class Response:
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self):
                return b'{"id":"x","model":"auto","choices":[{"message":{"content":"hello"}}]}'

        urlopen.return_value = Response()
        provider = FreeLLMAPIProvider(base_url="http://127.0.0.1:3001/v1", api_key="test-key")
        result = provider.generate(ModelRequest("hello"))
        self.assertEqual(result.text, "hello")
        self.assertEqual(result.provider, "freellmapi")
        self.assertEqual(result.model, "auto")
        request = urlopen.call_args.args[0]
        self.assertEqual(request.full_url, "http://127.0.0.1:3001/v1/chat/completions")
        self.assertEqual(request.headers["Authorization"], "Bearer test-key")

    def test_freellmapi_can_be_used_before_ollama(self):
        class FreeProvider(FakeProvider):
            pass

        result = ModelGateway([FreeProvider("freellmapi"), FakeProvider("ollama")]).generate(ModelRequest("hello"))
        self.assertEqual(result.provider, "freellmapi")


if __name__ == "__main__":
    unittest.main()

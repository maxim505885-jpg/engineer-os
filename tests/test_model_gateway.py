import unittest

from engineering.model_gateway.contracts import ModelRequest, ModelResponse
from engineering.model_gateway.gateway import ModelGateway, NoAvailableModelProvider

class FakeProvider:
    def __init__(self, name, available=True, fail=False):
        self.name = name
        self._available = available
        self._fail = fail
    def available(self): return self._available
    def generate(self, request):
        if self._fail: raise RuntimeError("boom")
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

if __name__ == "__main__": unittest.main()

import json
import unittest
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from engineering.model_gateway.openai_compatible import OpenAICompatibleGateway, ModelGatewayError


class _Response:
    def __init__(self, payload):
        self.payload = payload
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def read(self, size=-1):
        raw = json.dumps(self.payload).encode()
        return raw if size < 0 else raw[:size]


class ModelGatewayTests(unittest.TestCase):
    def test_default_transport_does_not_follow_redirects(self):
        redirected=[]
        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*args):pass
            def do_POST(self):
                self.send_response(302)
                self.send_header('Location','/target')
                self.end_headers()
            def do_GET(self):
                redirected.append(self.path)
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'{"choices":[{"message":{"content":"redirected"}}]}')
        server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        thread=threading.Thread(target=server.serve_forever,daemon=True)
        thread.start()
        try:
            gateway=OpenAICompatibleGateway(f'http://127.0.0.1:{server.server_port}',api_key='test-secret')
            with self.assertRaises(ModelGatewayError):
                gateway.chat(model='test',messages=({'role':'user','content':'x'},))
            self.assertEqual(redirected,[])
        finally:
            server.shutdown();server.server_close();thread.join()

    def test_http_endpoint_trust_uses_hostname_not_prefix_or_path(self):
        for url in ('http://localhost.attacker', 'http://127.0.0.1.attacker',
                    'http://public.example/path.railway.internal',
                    'http://service.railway.internal.attacker', 'http://user:secret@localhost',
                    'https://models.example?api_key=secret', 'https://models.example#fragment',
                    'http://localhost:invalid'):
            with self.subTest(url=url), self.assertRaises(ValueError):
                OpenAICompatibleGateway(url)

    def test_supported_local_private_and_https_endpoints_remain_available(self):
        for url in ('http://localhost:11434', 'http://127.0.0.1:11434',
                    'http://[::1]:11434', 'http://models.railway.internal:8080',
                    'https://models.example/api'):
            with self.subTest(url=url):
                OpenAICompatibleGateway(url)

    def test_incomplete_completion_cannot_become_a_reply(self):
        for reason in ('length', 'content_filter', 'tool_calls', 'unknown', None):
            body = {'choices': [{'finish_reason': reason, 'message': {'content': 'partial'}}]}
            gateway = OpenAICompatibleGateway('http://localhost', opener=lambda *a, **k: _Response(body))
            with self.subTest(reason=reason), self.assertRaises(ModelGatewayError):
                gateway.chat(model='test', messages=({'role':'user','content':'x'},))

    def test_completed_and_legacy_completion_are_supported(self):
        for choice in ({'finish_reason':'stop','message':{'content':'ok'}},
                       {'message':{'content':'ok'}}):
            gateway = OpenAICompatibleGateway('http://localhost', opener=lambda *a, **k: _Response({'choices':[choice]}))
            self.assertEqual(gateway.chat(model='test', messages=({'role':'user','content':'x'},)), 'ok')

    def test_oversized_response_is_rejected(self):
        gateway = OpenAICompatibleGateway('http://localhost', opener=lambda *a, **k: _Response({'choices':[{'message':{'content':'x'*(2*1024*1024)}}]}))
        with self.assertRaises(ModelGatewayError):
            gateway.chat(model='test', messages=({'role':'user','content':'x'},))

    def test_oversized_reply_is_rejected(self):
        gateway = OpenAICompatibleGateway('http://localhost', opener=lambda *a, **k: _Response({'choices':[{'message':{'content':'x'*32001}}]}))
        with self.assertRaises(ModelGatewayError):
            gateway.chat(model='test', messages=({'role':'user','content':'x'},))

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

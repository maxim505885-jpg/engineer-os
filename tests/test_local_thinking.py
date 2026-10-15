import json
import threading
import unittest
import io
import os
from contextlib import redirect_stderr
from unittest.mock import patch
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from engineering.local_app.model import LocalModel


class LocalThinkingTests(unittest.TestCase):
    def setUp(self):
        self.seen=[]
        self.response={'done': True, 'message': {'content': 'Результат', 'thinking': 'hidden'}}
        self.redirect=False
        owner=self
        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*args):pass
            def do_POST(self):
                owner.seen.append((self.path,json.loads(self.rfile.read(int(self.headers['Content-Length']))),self.headers.get('Authorization')))
                if owner.redirect:
                    self.send_response(307);self.send_header('Location','http://127.0.0.1:1/leak');self.end_headers();return
                self.send_response(200);self.end_headers()
                self.wfile.write(json.dumps(owner.response,ensure_ascii=False).encode())
        self.server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        self.origin=f'http://127.0.0.1:{self.server.server_port}'
        self.addCleanup(self.close)

    def close(self):
        self.server.shutdown();self.server.server_close();self.thread.join()

    def model(self,thinking=False):
        try:return LocalModel(self.origin,'qwen3:8b','secret',thinking=thinking)
        except TypeError:self.fail('Explicit thinking control is missing')

    def test_thinking_false_uses_native_ollama_protocol(self):
        self.assertEqual(self.model().chat([{'role':'user','content':'Проверь'}]),'Результат')
        path,payload,authorization=self.seen[-1]
        self.assertEqual(path,'/api/chat')
        self.assertIs(payload['think'],False)
        self.assertIs(payload['stream'],False)
        self.assertEqual(payload['options'],{'temperature':0.0})
        self.assertEqual(payload['messages'],[{'role':'user','content':'Проверь'}])
        self.assertEqual(authorization,'Bearer secret')

    def test_thinking_true_is_forwarded_without_exposing_thinking_text(self):
        self.assertEqual(self.model(True).chat([{'role':'user','content':'x'}]),'Результат')
        self.assertIs(self.seen[-1][1]['think'],True)

    def test_incomplete_or_malformed_native_response_is_rejected(self):
        model=self.model()
        for body in [{'done':False,'message':{'content':'partial'}},
                     {'done':True,'done_reason':'length','message':{'content':'truncated'}},
                     {'message':{'content':'missing completion'}},
                     {'done':True,'message':{'content':''}},
                     {'done':True,'message':{'content':['invalid']}},
                     {'done':True},[]]:
            with self.subTest(body=body):
                self.response=body
                with self.assertRaises(RuntimeError):model.chat([{'role':'user','content':'x'}])

    def test_native_redirect_is_not_followed(self):
        self.redirect=True
        with self.assertRaises(RuntimeError):self.model().chat([{'role':'user','content':'x'}])
        self.assertEqual(len(self.seen),1)

    def test_invalid_thinking_values_and_openwebui_profile_are_rejected(self):
        for value in ['false',0,1,[],{}]:
            with self.subTest(value=value):
                with self.assertRaises(ValueError):LocalModel(self.origin,thinking=value)
        with self.assertRaises(ValueError):LocalModel(self.origin,provider='openwebui',thinking=False)


class ThinkingStartupTests(unittest.TestCase):
    def test_environment_false_reaches_real_model_constructor(self):
        from scripts import run_local_app as launcher
        with patch.dict(os.environ,{'ENGINEER_OS_LOCAL_THINK':'false','ENGINEER_OS_LOCAL_PROVIDER':'ollama'}), \
                patch.object(launcher,'LocalModel',wraps=LocalModel) as constructor, \
                patch.object(launcher,'DataLock',side_effect=RuntimeError('test stop before server')), \
                redirect_stderr(io.StringIO()):
            self.assertEqual(launcher.main(['--no-browser']),2)
        self.assertIs(constructor.call_args.kwargs.get('thinking'),False)

    def test_invalid_environment_is_reported_before_data_lock(self):
        from scripts import run_local_app as launcher
        output=io.StringIO()
        with patch.dict(os.environ,{'ENGINEER_OS_LOCAL_THINK':'typo'}), \
                patch.object(launcher,'DataLock',side_effect=RuntimeError('test stop before server')) as lock, \
                redirect_stderr(output):
            self.assertEqual(launcher.main(['--no-browser']),2)
        self.assertIn('ENGINEER_OS_LOCAL_THINK',output.getvalue())
        lock.assert_not_called()


if __name__=='__main__':unittest.main()

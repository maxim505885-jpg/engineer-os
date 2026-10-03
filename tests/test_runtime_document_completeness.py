import hashlib
import io
import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from e2e.server import Handler


class RuntimeCompletenessTests(unittest.TestCase):
    def test_whole_document_request_does_not_claim_complete_extraction(self):
        payload = b'%PDF-test'
        sha = hashlib.sha256(payload).hexdigest()
        handler = object.__new__(Handler)
        handler.client_address = ('127.0.0.1', 1)
        outputs = []
        handler._json = lambda code,body: outputs.append((code,body))
        doc = SimpleNamespace(source_sha256=sha, parser='docling', blocks=[
            SimpleNamespace(provenance=[SimpleNamespace(page_no=1)])])
        env = dict(ENGINEER_OS_DOCUMENT_REMOTE_PARSE_ENABLED='true',
                   ENGINEER_OS_DOCUMENT_REMOTE_URL='https://test.r2.cloudflarestorage.com/a.pdf',
                   ENGINEER_OS_DOCUMENT_REMOTE_PROJECT_ID='p', ENGINEER_OS_DOCUMENT_REMOTE_DOCUMENT_ID='d',
                   ENGINEER_OS_DOCUMENT_REMOTE_SHA256=sha)
        with patch.dict(os.environ, env, clear=True), \
             patch('e2e.server.production_document_identity_verifier'), \
             patch('e2e.server.urlrequest.urlopen', return_value=io.BytesIO(payload)), \
             patch('e2e.server.DoclingDocumentParser') as parser:
            parser.return_value.parse.return_value = doc
            handler._run_remote_document_parse()
        self.assertEqual(outputs[0][0], 200)
        response = outputs[0][1]
        self.assertFalse(response['complete_document'])
        self.assertTrue(response['requested_full_document'])
        self.assertFalse(response['acceptance_granted'])
        self.assertEqual(response['verification_status'], 'UNCERTAINTY')

    def test_upload_response_preserves_uncertainty(self):
        from email.message import Message
        payload = b'%PDF-test'
        sha = hashlib.sha256(payload).hexdigest()
        handler = object.__new__(Handler)
        handler.rfile = io.BytesIO(payload)
        handler.headers = Message()
        for name,value in {'Authorization':'Bearer token','Content-Type':'application/pdf',
                           'Content-Length':str(len(payload)),'X-Project-ID':'p',
                           'X-Document-ID':'d','X-Source-SHA256':sha}.items():
            handler.headers[name] = value
        outputs = []
        handler._json = lambda code,body: outputs.append((code,body))
        doc = SimpleNamespace(source_sha256=sha, parser='docling', blocks=[
            SimpleNamespace(provenance=[SimpleNamespace(page_no=1)])])
        env = dict(ENGINEER_OS_DOCUMENT_INGEST_ENABLED='true', ENGINEER_OS_DOCUMENT_INGEST_TOKEN='token')
        with patch.dict(os.environ,env,clear=True), patch('e2e.server.production_document_identity_verifier'), patch('e2e.server.DoclingDocumentParser') as parser:
            parser.return_value.parse.return_value = doc
            handler._run_document_parse()
        code,body = outputs[0]
        self.assertEqual(code,200)
        self.assertFalse(body['complete_document'])
        self.assertFalse(body['acceptance_granted'])
        self.assertEqual(body['verification_status'],'UNCERTAINTY')

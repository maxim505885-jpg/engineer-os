import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts import windows_poststart_smoke as smoke


class WindowsPoststartSmokeTests(unittest.TestCase):
    def run_smoke(self, names):
        with tempfile.TemporaryDirectory() as root:
            output=Path(root)/'receipt.json'
            def response(url):
                return json.dumps({'models':[{'name':name} for name in names]}) if url.endswith('/api/tags') else 'ENGINEER OS'
            with patch.object(smoke,'get_text',side_effect=response), contextlib.redirect_stdout(io.StringIO()):
                code=smoke.main(['--app-url','http://localhost:8765','--ollama-url','http://localhost:11434',
                    '--model','qwen3:8b','--data-dir',root,'--out',str(output)])
            return code,json.loads(output.read_text())

    def test_similarly_named_model_does_not_satisfy_selected_model(self):
        code,receipt=self.run_smoke(['qwen3:8b-extra'])
        self.assertEqual(code,2)
        self.assertIn('OLLAMA_MODEL_MISSING',receipt['blocker_codes'])

    def test_exact_model_startup_receipt_does_not_claim_inference_or_windows(self):
        code,receipt=self.run_smoke(['qwen3:8b'])
        self.assertEqual(code,0)
        self.assertEqual(receipt.get('scope'),'STARTUP_ONLY')
        self.assertIs(receipt['inference_verified'],False)
        self.assertIs(receipt['physical_windows_verified'],False)
        self.assertTrue(receipt['platform'])

    def test_supervisor_does_not_accept_model_prefixes(self):
        supervisor=(Path(__file__).resolve().parents[1]/'scripts/windows_supervisor.ps1').read_text()
        self.assertNotIn('$_ -like "$Model*"',supervisor)

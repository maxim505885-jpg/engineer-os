import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from engineering.memory.ecc_cli_transport import ECCCLITransport, SUPPORTED_ECC_COMMIT
from engineering.memory.external_memory import MemoryBoundaryError


class ECCCLITransportTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name); self.ecc = self.root / 'ecc'
        (self.ecc / 'scripts').mkdir(parents=True)
        (self.ecc / 'scripts/memory.js').write_text('// fake')
        self.project = self.root / 'project'; self.project.mkdir()
        self.calls = []
        def runner(command, **kwargs):
            self.calls.append((command, kwargs))
            output = SUPPORTED_ECC_COMMIT if 'rev-parse' in command else ''
            if 'search' in command: output = json.dumps({'results': [], 'diagnostics': {
                'invalidFileCount': 0, 'skippedSymlinkCount': 0, 'truncated': False,
                'diagnosticsTruncated': False}})
            return subprocess.CompletedProcess(command, 0, output, '')
        self.runner = runner

    def transport(self, **kwargs):
        return ECCCLITransport(self.ecc, self.project, node=sys.executable, git=sys.executable,
                               runner=kwargs.pop('runner', self.runner), **kwargs)

    def test_search_is_explicit_scoped_and_no_shell_or_ambient_credentials(self):
        transport = self.transport()
        self.assertEqual(transport.adapter().search('checkpoint'), ())
        command, options = self.calls[-1]
        self.assertIn('--scope', command); self.assertIn('--target-harness', command)
        self.assertEqual(options['cwd'], str(self.project))
        self.assertFalse(options['shell'])
        self.assertEqual(options['encoding'], 'utf-8')
        self.assertEqual(options['env']['ECC_MEMORY_PROJECT_ROOT'], str(self.project / '.engineer-os/ecc-memory'))
        self.assertNotIn('HOME', options['env'])
        self.assertNotIn('NODE_OPTIONS', options['env'])
        self.assertNotIn('OPENAI_API_KEY', options['env'])

    def test_other_commit_and_dirty_checkout_rejected(self):
        for output in ('b' * 40, SUPPORTED_ECC_COMMIT + '\n M scripts/memory.js'):
            def runner(command, **kwargs):
                value = output.split('\n')[0] if 'rev-parse' in command else output.split('\n')[-1]
                return subprocess.CompletedProcess(command, 0, value, '')
            with self.subTest(output=output), self.assertRaises(MemoryBoundaryError):
                self.transport(runner=runner)

    def test_vault_outside_project_rejected(self):
        with self.assertRaises(ValueError): self.transport(vault=self.root / 'other')

    def test_user_scope_and_path_id_read_rejected_before_process(self):
        transport = self.transport(); count = len(self.calls)
        for memory_id, scope in (('../file', 'project'), ('mem_valid', 'user')):
            with self.assertRaises(MemoryBoundaryError): transport.read(memory_id, scope)
        self.assertEqual(len(self.calls), count)

    def test_invalid_json_nonzero_and_timeout_fail_without_raw_output(self):
        transport = self.transport()
        for failure in ('json', 'exit', 'timeout'):
            def runner(command, **kwargs):
                if failure == 'timeout': raise subprocess.TimeoutExpired(command, 10)
                return subprocess.CompletedProcess(command, 1 if failure == 'exit' else 0,
                                                   'PRIVATE-SYNTHETIC-MARKER', '')
            transport._runner = runner
            with self.subTest(failure=failure), self.assertRaises(MemoryBoundaryError) as caught:
                transport.search('checkpoint')
            self.assertNotIn('PRIVATE-SYNTHETIC-MARKER', str(caught.exception))


if __name__ == '__main__': unittest.main()

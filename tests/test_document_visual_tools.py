"""Receipts must distinguish visual equality, differences and failed execution."""
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

class VisualToolTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.a = self.root / 'source.pdf'
        self.b = self.root / 'reference.pdf'
        self.a.write_bytes(b'%PDF-1.7\nsource')
        self.b.write_bytes(b'%PDF-1.7\nreference')
        self.exe = self.root / 'diff-pdf.exe'
        self.exe.write_bytes(b'controlled external executable')

    def compare(self, code, *, mutate=False):
        from scripts.compare_document_visuals import compare_files
        def external(command, **kwargs):
            output = next(x.split('=', 1)[1] for x in command if x.startswith('--output-diff='))
            Path(output).write_bytes(b'%PDF-1.7\nvisual diff')
            if mutate:
                self.a.write_bytes(b'%PDF-1.7\nchanged during render')
            return type('Result', (), {'returncode': code})()
        with patch('scripts.compare_document_visuals.subprocess.run', side_effect=external):
            return compare_files(self.a, self.b, self.root / 'result', executable=self.exe)

    def test_equal_pixels_do_not_grant_semantic_or_engineering_acceptance(self):
        result = self.compare(0)
        self.assertEqual(result.get('comparison_status'), 'PASS')
        self.assertFalse(result['acceptance_granted'])
        self.assertFalse(result['reference_authority_verified'])
        self.assertFalse(result['engineering_verified'])
        self.assertEqual(result['source_sha256'], hashlib.sha256(self.a.read_bytes()).hexdigest())
        self.assertEqual(json.loads((self.root/'result'/'manifest.json').read_text())['comparison_status'], 'PASS')

    def test_difference_is_review_required_not_a_proven_engineering_error(self):
        result = self.compare(1)
        self.assertEqual(result.get('comparison_status'), 'DIFFERENCES_FOUND')
        self.assertEqual(result.get('status'), 'REVIEW_REQUIRED')
        self.assertEqual(result['diff_sha256'], hashlib.sha256(b'%PDF-1.7\nvisual diff').hexdigest())

    def test_tool_failure_is_not_reported_as_difference(self):
        self.assertEqual(self.compare(2).get('status'), 'BLOCK')

    def test_changed_input_invalidates_render(self):
        result = self.compare(0, mutate=True)
        self.assertEqual(result.get('status'), 'BLOCK')
        self.assertIn('INPUT_CHANGED', result['reasons'])

    def test_existing_output_cannot_be_overwritten(self):
        from scripts.compare_document_visuals import compare_files
        (self.root/'result').mkdir()
        with self.assertRaises(ValueError):
            compare_files(self.a, self.b, self.root/'result', executable=self.exe)

    def test_non_pdf_is_rejected_before_tool_execution(self):
        from scripts.compare_document_visuals import compare_files
        self.a.write_bytes(b'not a PDF')
        with self.assertRaises(ValueError):
            compare_files(self.a, self.b, self.root/'result', executable=self.exe)

class VisualFailureTests(unittest.TestCase):
    setUp = VisualToolTests.setUp

    def test_timeout_blocks(self):
        import subprocess
        from scripts.compare_document_visuals import compare_files
        with patch('scripts.compare_document_visuals.subprocess.run', side_effect=subprocess.TimeoutExpired('diff-pdf', 1)):
            result = compare_files(self.a, self.b, self.root/'timeout', executable=self.exe)
        self.assertEqual(result['status'], 'BLOCK')
        self.assertIn('ENGINE_TIMEOUT', result['reasons'])

    def test_missing_or_invalid_difference_artifact_blocks(self):
        from scripts.compare_document_visuals import compare_files
        for case in ('missing', 'malformed'):
            def external(command, **kwargs):
                if case == 'malformed':
                    target=next(x.split('=',1)[1] for x in command if x.startswith('--output-diff='))
                    Path(target).write_bytes(b'not a PDF')
                return type('Result', (), {'returncode': 1})()
            with patch('scripts.compare_document_visuals.subprocess.run', side_effect=external):
                result=compare_files(self.a,self.b,self.root/case,executable=self.exe)
            self.assertEqual(result['status'],'BLOCK')
            self.assertEqual(result['comparison_status'],'NOT_COMPLETED')

class ContainerCommandTests(unittest.TestCase):
    def test_image_must_be_pinned_official_digest(self):
        from scripts.render_document_gotenberg import container_command
        for image in ('gotenberg/gotenberg:latest', 'attacker/image@sha256:'+'a'*64):
            with self.assertRaises(ValueError):
                container_command('docker', image, 'engineer-office-test')

    def test_offline_container_exposes_no_host_folder_or_port(self):
        from scripts.render_document_gotenberg import container_command
        command = container_command('docker', 'gotenberg/gotenberg@sha256:'+'a'*64, 'engineer-office-test')
        self.assertIn('--network=none', command)
        self.assertIn('--user=1001:1001', command)
        self.assertIn('--env=HOME=/tmp', command)
        self.assertIn('--host', command)
        self.assertIn('--read-only', command)
        self.assertIn('--pull=never', command)
        self.assertIn('--cap-drop=ALL', command)
        self.assertFalse(any(x in command for x in ('--volume', '-v', '--publish', '-p', '--privileged')))

class RenderLifecycleTests(unittest.TestCase):
    setUp = VisualToolTests.setUp
    def test_no_runtime_never_opens_or_uploads_source(self):
        from scripts.render_document_gotenberg import render
        with patch('scripts.render_document_gotenberg.shutil.which', return_value=None):
            with self.assertRaisesRegex(ValueError, 'CONTAINER_RUNTIME_UNAVAILABLE'):
                render(self.root/'missing.docx', self.root/'never-created', image='gotenberg/gotenberg@sha256:'+'a'*64)
        self.assertFalse((self.root/'never-created').exists())

    def test_conversion_failure_still_removes_its_container(self):
        import subprocess
        from scripts.render_document_gotenberg import render
        source = self.root/'source.docx'
        source.write_bytes(b'PK control package')
        calls = []
        def external(command, **kwargs):
            calls.append(command)
            if 'start' in command:
                raise subprocess.CalledProcessError(1, command)
            return type('Result', (), {'returncode': 0})()
        with patch('scripts.render_document_gotenberg.shutil.which', return_value=str(self.exe)), patch('scripts.render_document_gotenberg.subprocess.run', side_effect=external):
            result = render(source, self.root/'render', image='gotenberg/gotenberg@sha256:'+'a'*64)
        self.assertEqual(result['status'], 'BLOCK')
        self.assertTrue(result['cleanup_completed'])
        self.assertTrue(any('rm' in call and '--force' in call for call in calls))
        self.assertEqual(source.read_bytes(), b'PK control package')

    def test_success_is_unqualified_and_cleanup_failure_overrides_it(self):
        import subprocess
        from scripts.render_document_gotenberg import render
        source=self.root/'source.docx'
        source.write_bytes(b'PK control package')
        for cleanup in ('success','failed','timeout'):
            calls=[]
            def external(command, **kwargs):
                calls.append((command,kwargs))
                if '--data-binary' in command:
                    kwargs['stdout'].write(b'%PDF-1.7 sample output')
                if 'rm' in command and cleanup == 'timeout':
                    raise subprocess.TimeoutExpired(command,30)
                code=1 if 'rm' in command and cleanup == 'failed' else 0
                return type('Result', (), {'returncode':code})()
            with patch.dict(os.environ,{'DOCKER_HOST':'tcp://remote.example:2375','DOCKER_CONTEXT':'remote'}), patch('scripts.render_document_gotenberg.shutil.which',return_value=str(self.exe)), patch('scripts.render_document_gotenberg.subprocess.run',side_effect=external):
                result=render(source,self.root/cleanup,image='gotenberg/gotenberg@sha256:'+'a'*64)
            self.assertEqual(result['status'],'DERIVED_UNVERIFIED' if cleanup=='success' else 'BLOCK')
            self.assertFalse(result['isolation_qualified'])
            self.assertFalse(result['acceptance_granted'])
            self.assertEqual(result['pdf_sha256'],hashlib.sha256(b'%PDF-1.7 sample output').hexdigest())
            for command,kwargs in calls:
                self.assertIn('--host',command)
                self.assertNotIn('DOCKER_CONTEXT',kwargs['env'])
                self.assertNotIn('DOCKER_HOST',kwargs['env'])

if __name__ == '__main__':
    unittest.main()

"""Profile availability is distinct from fresh, offline functional probes."""
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


class ProfileTests(unittest.TestCase):
    def test_installed_package_without_models_is_not_ready(self):
        from engineering.local_app.capability_receipts import capability_report
        with patch('engineering.local_app.capability_receipts.package_version',return_value='1.0'),patch.dict(os.environ,{'ENGINEER_OS_TESSERACT_BIN':'Z:/missing/tesseract.exe'},clear=True):
            result=capability_report('engineering')
        self.assertFalse(result['acceptance_granted'])
        self.assertEqual(result['capabilities']['ocr']['probe_status'],'NOT_RUN')
        self.assertFalse(result['capabilities']['ocr']['configured'])
        self.assertFalse(any(x['ready'] for x in result['capabilities'].values()))

    def test_offline_profile_does_not_download_or_execute_on_inventory(self):
        from engineering.local_app.capability_receipts import capability_report
        with patch('subprocess.run',side_effect=AssertionError('Inventory must not execute')),patch('urllib.request.urlopen',side_effect=AssertionError('No network')):
            result=capability_report('native')
        self.assertEqual(result['network_policy'],'NO_DOWNLOADS')
        self.assertFalse(result['execution_verified'])

    def test_missing_optional_adapter_keeps_base_starting(self):
        from engineering.local_app.capability_receipts import capability_report
        with patch('engineering.local_app.capability_receipts.package_version',return_value=None):
            result=capability_report('native')
        self.assertTrue(result['base_start_allowed'])
        self.assertFalse(result['capabilities']['ifc']['installed'])
        self.assertFalse(result['capabilities']['beam']['ready'])

    def test_programfiles_tesseract_found_without_path(self):
        from engineering.local_app.capability_receipts import find_tesseract
        with tempfile.TemporaryDirectory() as tmp:
            binary=Path(tmp)/'Tesseract-OCR/tesseract.exe';binary.parent.mkdir();binary.write_bytes(b'fixture')
            with patch.dict(os.environ,{'ProgramFiles':tmp},clear=True),patch('shutil.which',return_value=None):
                self.assertEqual(find_tesseract(),binary.resolve())

    def test_explicit_missing_binary_does_not_fall_back(self):
        from engineering.local_app.capability_receipts import find_tesseract
        with patch.dict(os.environ,{'ENGINEER_OS_TESSERACT_BIN':'Z:/missing.exe'},clear=True),patch('shutil.which',return_value=__file__):
            self.assertIsNone(find_tesseract())

    def test_profile_names_are_allowlisted(self):
        from engineering.local_app.capability_receipts import capability_report
        with self.assertRaises(ValueError):capability_report('../other')

    def test_probe_timeout_is_failure_without_readiness(self):
        import subprocess
        from engineering.local_app.capability_receipts import probe_capability
        with patch('subprocess.run',side_effect=subprocess.TimeoutExpired('probe',1)):
            result=probe_capability('pdf',timeout=1)
        self.assertEqual(result['probe_status'],'BLOCK')
        self.assertFalse(result['ready'])
        self.assertIn('PROBE_TIMEOUT',result['reasons'])

    def test_office_cannot_become_ready_from_unqualified_sandbox(self):
        from engineering.local_app.capability_receipts import probe_capability
        result=probe_capability('office')
        self.assertFalse(result['ready'])
        self.assertIn('WINDOWS_SOURCE_RENDER_ISOLATION_NOT_QUALIFIED',result['reasons'])

    def test_unknown_probe_is_rejected(self):
        from engineering.local_app.capability_receipts import probe_capability
        with self.assertRaises(ValueError):probe_capability('arbitrary-command')

    def test_pdf_fixed_probe_really_reads_and_rasterizes(self):
        from engineering.local_app.capability_receipts import probe_capability
        result=probe_capability('pdf')
        self.assertEqual(result['probe_status'],'PASS',result)
        self.assertFalse(result['acceptance_granted'])
        self.assertFalse(result['network_isolation_verified'])
        self.assertEqual(len(result['receipt']['source_sha256']),64)

    def test_malformed_child_output_never_ready(self):
        import subprocess
        from engineering.local_app.capability_receipts import probe_capability
        with patch('subprocess.run',return_value=subprocess.CompletedProcess([],0)):
            result=probe_capability('pdf')
        self.assertFalse(result['ready'])
        self.assertIn('PROBE_OUTPUT_INVALID',result['reasons'])

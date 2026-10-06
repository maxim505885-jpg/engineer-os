from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]

class WindowsOneClickContractTests(unittest.TestCase):
    def text(self,path):
        return (ROOT/path).read_text(encoding='utf-8')

    def test_cmd_is_only_one_click_entrypoint(self):
        cmd=self.text('Start_ENGINEER_OS.cmd')
        self.assertIn('scripts\\windows_supervisor.ps1',cmd)
        self.assertNotIn('run_local_app.py',cmd)
        self.assertIn('ExecutionPolicy Bypass',cmd)
        self.assertIn('windows-supervisor.log',cmd)

    def test_supervisor_replaces_manual_start_sequence(self):
        ps=self.text('scripts/windows_supervisor.ps1')
        for marker in (
            'Ensure-Venv','Ensure-Dependencies','Ensure-Ollama',
            'Ensure-OpenWebUI','Ensure-EngineerOS',
            ".env.google-drive","qwen3:8b",
            "ENGINEER_OS_LOCAL_PROVIDER='ollama'",
            "scripts\\run_local_app.py","--no-browser",
            "startup-state.json","poststart-smoke.json","windows_poststart_smoke.py","Browser opened",
        ):
            self.assertIn(marker,ps)
        self.assertNotIn('$AppUrl/api/status',ps)
        self.assertIn("Test-EngineerOS",ps)
        self.assertIn("ENGINEER OS already running",ps)

    def test_dependencies_are_not_reinstalled_every_start(self):
        ps=self.text('scripts/windows_supervisor.ps1')
        self.assertIn('requirements.sha256',ps)
        self.assertIn('Get-FileHash -Algorithm SHA256',ps)
        self.assertIn('Python dependencies unchanged',ps)

    def test_background_policy_is_resource_bounded(self):
        ps=self.text('scripts/windows_supervisor.ps1')
        self.assertIn("ollama",ps.lower())
        self.assertIn("open-webui",ps.lower())
        self.assertNotIn('local_docling_batch.py',ps)
        self.assertNotIn('OfficeCLI',ps)
        self.assertNotIn('stage8_final_audit_offline.py',ps)

    def test_poststart_smoke_uses_only_stdlib_and_checks_required_runtime(self):
        smoke=self.text('scripts/windows_poststart_smoke.py')
        self.assertIn('ENGINEER_OS_WINDOWS_POSTSTART_V1',smoke)
        self.assertIn('/api/tags',smoke)
        self.assertIn('data_dir_write',smoke)
        self.assertIn('ENGINEER OS',smoke)
        self.assertNotIn('requests',smoke)

    def test_stop_does_not_kill_reusable_model_services(self):
        stop=self.text('scripts/windows_stop.ps1')
        self.assertIn('LocalPort 8765',stop)
        self.assertNotIn('11434',stop)
        self.assertNotIn('8080',stop)

if __name__=='__main__':
    unittest.main()

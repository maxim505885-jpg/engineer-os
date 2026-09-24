import json
import subprocess

from engineering.core.contracts import AgentStatus, MaterialRef, SpecialistTask
from engineering.runtime.hermes_adapter import HermesExecutionConfig, HermesRuntimeAdapter, HermesRuntimeError, HermesSubprocessClient


def task():
    return SpecialistTask("task-1", "inspection-agent", "inspection-audit",
                          (MaterialRef("m1", "report", "report.docx", "file:///report.docx"),),
                          "Inspect evidence.", "Проверить отчет согласно ТЗ.")


def test_subprocess_command():
    calls = []
    def runner(command, **kwargs):
        calls.append((command, kwargs))
        return subprocess.CompletedProcess(command, 0, '{"ok": true}', "")
    client = HermesSubprocessClient(HermesExecutionConfig(model="local-model", provider="ollama", toolsets=("filesystem",), timeout_seconds=30), runner)
    assert client.execute("prompt", skills=("inspection-audit",)) == '{"ok": true}'
    command, kwargs = calls[0]
    assert command[:6] == ["hermes", "-z", "--model", "local-model", "--provider", "ollama"]
    assert "--toolsets" in command and "--skills" in command
    assert kwargs["timeout"] == 30


def test_adapter_structured_result():
    response = {"task_id": "task-1", "agent": "inspection-agent", "status": "UNCERTAINTY",
                "findings": [{"certainty": "UNCERTAIN", "evidence_ids": ["m1"]}],
                "evidence_ids": ["m1"], "message": "Insufficient evidence."}
    class Client:
        def execute(self, prompt, *, skills=()):
            assert "inspection-audit" in skills
            return json.dumps(response)
    result = HermesRuntimeAdapter(client=Client()).execute([task()])[0]
    assert result.status is AgentStatus.UNCERTAINTY


def test_adapter_rejects_wrong_identity():
    class Client:
        def execute(self, prompt, *, skills=()):
            return '{"task_id":"other","agent":"inspection-agent","status":"PASS","findings":[],"evidence_ids":[]}'
    try:
        HermesRuntimeAdapter(client=Client()).execute([task()])
    except HermesRuntimeError:
        return
    raise AssertionError("Expected HermesRuntimeError")

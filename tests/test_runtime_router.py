from engineering.core.contracts import AgentResult, AgentStatus, MaterialRef, SpecialistTask
from engineering.runtime.router import EngineeringRuntimeRouter, RuntimePolicy


def task(agent="inspection-agent"):
    return SpecialistTask(
        "task-1", agent, "inspection-audit",
        (MaterialRef("m1", "report", "r.docx"),), "inspect", "TZ"
    )


class FakeRuntime:
    def __init__(self, results):
        self.results = results
        self.calls = 0

    def execute(self, planned):
        self.calls += 1
        return self.results


def test_router_selects_hermes():
    hermes = FakeRuntime([AgentResult("task-1", "inspection-agent", AgentStatus.PASS)])
    codex = FakeRuntime([AgentResult("task-1", "inspection-agent", AgentStatus.ERROR)])
    result = EngineeringRuntimeRouter(RuntimePolicy("hermes"), hermes=hermes, codex=codex).execute([task()])
    assert result[0].status is AgentStatus.PASS
    assert hermes.calls == 1
    assert codex.calls == 0


def test_router_selects_codex():
    hermes = FakeRuntime([AgentResult("task-1", "inspection-agent", AgentStatus.PASS)])
    codex = FakeRuntime([AgentResult("task-1", "inspection-agent", AgentStatus.ACCEPTED)])
    result = EngineeringRuntimeRouter(RuntimePolicy("codex"), hermes=hermes, codex=codex).execute([task()])
    assert result[0].status is AgentStatus.ACCEPTED
    assert codex.calls == 1
    assert hermes.calls == 0


def test_router_missing_backend_is_uncertain():
    result = EngineeringRuntimeRouter(RuntimePolicy("codex"), hermes=None, codex=None).execute([task()])
    assert result[0].status is AgentStatus.UNCERTAINTY


def test_router_rejects_uncertain_finding_as_acceptance():
    finding = {
        "observation": "not enough evidence",
        "basis": "source incomplete",
        "certainty": "UNCERTAIN",
        "conclusion": "cannot confirm",
        "evidence_ids": ["m1"],
    }
    result = EngineeringRuntimeRouter(
        RuntimePolicy("hermes"),
        hermes=FakeRuntime([
            AgentResult("task-1", "inspection-agent", AgentStatus.ACCEPTED, (finding,), ("m1",))
        ]),
    ).execute([task()])
    assert result[0].status is AgentStatus.ERROR
    assert "contract violation" in (result[0].message or "")


def test_router_rejects_unknown_evidence():
    result = EngineeringRuntimeRouter(
        RuntimePolicy("hermes"),
        hermes=FakeRuntime([
            AgentResult("task-1", "inspection-agent", AgentStatus.PASS, (), ("not-supplied",))
        ]),
    ).execute([task()])
    assert result[0].status is AgentStatus.ERROR


def test_router_selects_openwebui():
    openwebui = FakeRuntime([AgentResult("task-1", "inspection-agent", AgentStatus.ACCEPTED)])
    result = EngineeringRuntimeRouter(RuntimePolicy("openwebui"), openwebui=openwebui).execute([task()])
    assert result[0].status is AgentStatus.ACCEPTED
    assert openwebui.calls == 1

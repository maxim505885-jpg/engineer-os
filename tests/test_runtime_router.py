from engineering.core.contracts import AgentResult, AgentStatus, MaterialRef, SpecialistTask
from engineering.runtime.router import EngineeringRuntimeRouter, RuntimePolicy


def task():
    return SpecialistTask(
        "task-1", "inspection-agent", "inspection-audit",
        (MaterialRef("m1", "report", "r.docx"),), "inspect", "TZ"
    )


class FakeRuntime:
    def __init__(self, status):
        self.status = status
        self.calls = 0

    def execute(self, planned):
        self.calls += 1
        return [AgentResult(planned[0].task_id, planned[0].agent, self.status)]


def test_router_selects_hermes():
    hermes = FakeRuntime(AgentStatus.PASS)
    codex = FakeRuntime(AgentStatus.ERROR)
    result = EngineeringRuntimeRouter(RuntimePolicy("hermes"), hermes=hermes, codex=codex).execute([task()])
    assert result[0].status is AgentStatus.PASS
    assert hermes.calls == 1
    assert codex.calls == 0


def test_router_selects_codex():
    hermes = FakeRuntime(AgentStatus.PASS)
    codex = FakeRuntime(AgentStatus.ACCEPTED)
    result = EngineeringRuntimeRouter(RuntimePolicy("codex"), hermes=hermes, codex=codex).execute([task()])
    assert result[0].status is AgentStatus.ACCEPTED
    assert codex.calls == 1
    assert hermes.calls == 0


def test_router_missing_backend_is_uncertain():
    result = EngineeringRuntimeRouter(RuntimePolicy("codex"), hermes=None, codex=None).execute([task()])
    assert result[0].status is AgentStatus.UNCERTAINTY

import json

from engineering.core.contracts import AgentStatus, MaterialRef, SpecialistTask
from engineering.runtime.router import EngineeringRuntimeRouter, RuntimePolicy
from engineering.runtime.open_webui_adapter import OpenWebUIClient, OpenWebUIExecutionConfig, OpenWebUIRuntimeAdapter


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def read(self):
        return json.dumps(self.payload).encode('utf-8')


def test_open_webui_client_uses_chat_completions_boundary():
    seen = {}

    def opener(request, timeout):
        seen['url'] = request.full_url
        seen['auth'] = request.headers.get('Authorization')
        seen['body'] = json.loads(request.data.decode('utf-8'))
        seen['timeout'] = timeout
        return FakeResponse({'choices': [{'message': {'content': '{}'}}]})

    client = OpenWebUIClient(OpenWebUIExecutionConfig(
        base_url='http://localhost:8080/', api_key='secret', model='local-model', timeout_seconds=17
    ), opener=opener)
    client.execute('hello')

    assert seen['url'] == 'http://localhost:8080/api/chat/completions'
    assert seen['auth'] == 'Bearer secret'
    assert seen['body']['model'] == 'local-model'
    assert seen['body']['stream'] is False
    assert seen['timeout'] == 17


def test_open_webui_runtime_adapter_parses_structured_result():
    task = SpecialistTask(
        task_id='task-1', agent='inspection-agent', skill='inspection-audit',
        inputs=(MaterialRef(id='mat-1', kind='report', name='report.docx'),),
        purpose='audit', tz='check supplied evidence',
    )
    payload = {
        'choices': [{'message': {'content': json.dumps({
            'task_id': 'task-1', 'agent': 'inspection-agent', 'status': 'ACCEPTED',
            'findings': [], 'evidence_ids': [], 'message': 'ok'
        })}}],
    }

    class Client:
        def execute(self, prompt):
            return payload

    result = OpenWebUIRuntimeAdapter(Client()).execute([task])[0]
    assert result.status.value == 'ACCEPTED'
    assert result.task_id == 'task-1'
    assert result.agent == 'inspection-agent'
def test_openwebui_to_router_model_free_e2e():
    task = SpecialistTask(
        task_id='e2e-task-1', agent='inspection-agent', skill='inspection-audit',
        inputs=(MaterialRef(id='evidence-1', kind='report', name='report.docx'),),
        purpose='validate supplied evidence', tz='do not invent missing facts',
    )
    finding = {
        'observation': 'Observed condition is documented in supplied report.',
        'basis': 'Directly supplied report evidence.',
        'certainty': 'CONFIRMED',
        'conclusion': 'Condition is confirmed from the supplied evidence.',
        'evidence_ids': ['evidence-1'],
    }
    payload = {
        'choices': [{'message': {'content': json.dumps({
            'task_id': task.task_id, 'agent': task.agent, 'status': 'ACCEPTED',
            'findings': [finding], 'evidence_ids': ['evidence-1'], 'message': 'validated'
        })}}],
    }

    class Client:
        def execute(self, prompt):
            assert 'Never invent facts' in prompt
            assert task.task_id in prompt
            return payload

    runtime = OpenWebUIRuntimeAdapter(Client())
    router = EngineeringRuntimeRouter(RuntimePolicy('openwebui'), openwebui=runtime)
    result = router.execute([task])

    assert len(result) == 1
    assert result[0].status.value == 'ACCEPTED'
    assert result[0].task_id == task.task_id
    assert result[0].agent == task.agent
    assert result[0].evidence_ids == ('evidence-1',)


def test_openwebui_normalizes_status_string_as_empty_findings():
    task = SpecialistTask(
        task_id='uncertain-task', agent='inspection-agent', skill='inspection-audit',
        inputs=(), purpose='validate missing evidence', tz='do not invent missing facts',
    )
    payload = {
        'choices': [{'message': {'content': json.dumps({
            'task_id': task.task_id, 'agent': task.agent, 'status': 'UNCERTAINTY',
            'findings': 'UNCERTAINTY', 'evidence_ids': [], 'message': 'Insufficient evidence.'
        })}}],
    }

    class Client:
        def execute(self, prompt):
            assert 'findings MUST ALWAYS be a JSON ARRAY' in prompt
            return payload

    result = OpenWebUIRuntimeAdapter(Client()).execute([task])[0]
    assert result.status is AgentStatus.UNCERTAINTY
    assert result.findings == ()

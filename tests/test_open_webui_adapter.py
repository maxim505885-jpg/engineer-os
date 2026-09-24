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
        config = OpenWebUIExecutionConfig(model='local-model')
        def execute(self, prompt, model=None):
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
        config = OpenWebUIExecutionConfig(model='local-model')
        def execute(self, prompt, model=None):
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
        config = OpenWebUIExecutionConfig(model='local-model')
        def execute(self, prompt, model=None):
            assert 'findings MUST ALWAYS be a JSON ARRAY' in prompt
            return payload

    result = OpenWebUIRuntimeAdapter(Client()).execute([task])[0]
    assert result.status is AgentStatus.UNCERTAINTY
    assert result.findings == ()


def test_openwebui_falls_back_to_configured_model():
    task = SpecialistTask(
        task_id='fallback-task', agent='inspection-agent', skill='inspection-audit',
        inputs=(), purpose='runtime fallback', tz='do not invent missing facts',
    )
    calls = []

    class Client:
        config = OpenWebUIExecutionConfig(
            model='primary-model', fallback_models=('qwen3:8b',)
        )

        def execute(self, prompt, model=None):
            calls.append(model)
            if model == 'primary-model':
                from engineering.runtime.open_webui_adapter import OpenWebUIRuntimeError
                raise OpenWebUIRuntimeError('primary unavailable')
            return {'choices': [{'message': {'content': json.dumps({
                'task_id': task.task_id, 'agent': task.agent, 'status': 'UNCERTAINTY',
                'findings': [], 'evidence_ids': [], 'message': 'fallback response'
            })}}]}

    result = OpenWebUIRuntimeAdapter(Client()).execute([task])[0]
    assert calls == ['primary-model', 'qwen3:8b']
    assert result.status is AgentStatus.UNCERTAINTY
    assert result.message.startswith('Runtime model fallback used: qwen3:8b.')


def test_openwebui_transport_error_triggers_configured_fallback():
    from io import BytesIO
    from urllib.error import HTTPError

    task = SpecialistTask(
        task_id="transport-fallback-task",
        agent="inspection-agent",
        skill="inspection-audit",
        inputs=(),
        purpose="runtime fallback after transport error",
        tz="do not invent missing facts",
    )
    calls = []

    def opener(request, timeout):
        calls.append(json.loads(request.data.decode("utf-8"))["model"])
        if calls[-1] == "primary-model":
            raise HTTPError(
                request.full_url,
                429,
                "rate limited",
                {"Content-Type": "application/json"},
                BytesIO(b'{"detail":"rate limited"}'),
            )
        return FakeResponse({"choices": [{"message": {"content": json.dumps({
            "task_id": task.task_id,
            "agent": task.agent,
            "status": "UNCERTAINTY",
            "findings": [],
            "evidence_ids": [],
            "message": "fallback response",
        })}}]})

    client = OpenWebUIClient(
        OpenWebUIExecutionConfig(
            base_url="http://localhost:8080",
            model="primary-model",
            fallback_models=("qwen3:8b",),
        ),
        opener=opener,
    )

    result = OpenWebUIRuntimeAdapter(client).execute([task])[0]

    assert calls == ["primary-model", "qwen3:8b"]
    assert result.status is AgentStatus.UNCERTAINTY
    assert result.message.startswith("Runtime model fallback used: qwen3:8b.")

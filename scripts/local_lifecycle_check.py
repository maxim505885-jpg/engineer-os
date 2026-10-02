"""Offline local HTTP/queue/persistence check with synthetic model responses."""
import argparse
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import re
import sys
import tempfile
import threading

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from engineering.core import EngineerTask, MaterialRef, TaskEngine, TaskStore
from engineering.core.engineer_core import AgentRuntimeAdapter
from engineering.core.task_engine import TaskStatus
from engineering.core.task_worker import TaskWorker
from engineering.runtime.open_webui_adapter import OpenWebUIClient, OpenWebUIExecutionConfig, OpenWebUIRuntimeAdapter
from engineering.runtime.router import EngineeringRuntimeRouter, RuntimePolicy
from scripts.local_openwebui_smoke import evaluate_smoke


class FixtureHandler(BaseHTTPRequestHandler):
    def log_message(self, *args): pass
    def do_POST(self):
        assert self.path == '/api/chat/completions'
        request = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        prompt = request['messages'][0]['content']
        result = {'task_id': re.search(r'^task_id: (.+)$', prompt, re.M)[1],
                  'agent': re.search(r'^agent: (.+)$', prompt, re.M)[1],
                  'status': 'UNCERTAINTY', 'findings': [], 'evidence_ids': [],
                  'message': 'Synthetic fixture only; no engineering conclusion.'}
        body = json.dumps({'choices': [{'message': {'content': json.dumps(result)}}]}).encode()
        self.send_response(200); self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body))); self.end_headers(); self.wfile.write(body)


def check() -> dict:
    checks = []
    server = ThreadingHTTPServer(('127.0.0.1', 0), FixtureHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    try:
        runtime = EngineeringRuntimeRouter(RuntimePolicy(backend='openwebui'), openwebui=
            OpenWebUIRuntimeAdapter(OpenWebUIClient(OpenWebUIExecutionConfig(
                base_url=f'http://127.0.0.1:{server.server_port}', model='synthetic-fixture', timeout_seconds=5))))
        smoke = evaluate_smoke(runtime)
        assert smoke['runtime_health'] == 'PASSED' and smoke['engineering_status'] == 'UNCERTAINTY'
        checks.append('real loopback HTTP and Open WebUI result parsing')
        with tempfile.TemporaryDirectory(prefix='engineer-local-lifecycle-') as tmp:
            path = Path(tmp) / 'tasks.json'
            task = EngineerTask('local-check', 'Synthetic persistence verification',
                                (MaterialRef('fixture', 'test', 'synthetic data'),), ('inspection',))
            engine = TaskEngine(store=TaskStore(path)); engine.submit(task)
            restarted = TaskEngine(store=TaskStore(path))
            assert restarted.get(task.task_id).status == TaskStatus.QUEUED
            checks.append('queued task survives a new engine instance')
            assert TaskWorker(restarted, lambda: runtime).run_once() == 1
            checks.append('worker executes queued task through HTTP model adapter')
            reopened = TaskEngine(store=TaskStore(path)); record = reopened.get(task.task_id)
            assert record.status == TaskStatus.BLOCKED and record.result_status.value == 'UNCERTAINTY'
            assert record.state == restarted.get(task.task_id).state
            assert len(record.state.planned) == 2 and len(record.state.results) == 2
            assert TaskStore(path).list_runs()[0].status == 'BLOCKED'
            checks.append('full plan/results/status reopen with non-acceptance retained')
            interrupted = EngineerTask('interrupted', task.tz, task.materials, task.requested_checks)
            reopened.submit(interrupted)
            def interrupt(p): raise KeyboardInterrupt()
            try: reopened.run(interrupted.task_id, AgentRuntimeAdapter({'inspection-agent': interrupt}))
            except KeyboardInterrupt: pass
            recovered = TaskEngine(store=TaskStore(path))
            assert recovered.get(interrupted.task_id).status == TaskStatus.RUNNING
            checks.append('interrupted execution remains durably RUNNING')
            recovered.requeue(interrupted.task_id, reason='Synthetic explicit restart')
            assert TaskWorker(recovered, lambda: runtime).run_once() == 1
            assert TaskStore(path).load()[1].status == TaskStatus.BLOCKED
            checks.append('explicit retry completes with a newly persisted result')
    finally:
        server.shutdown(); server.server_close(); thread.join(timeout=2)
    return {'test_status': 'passed', 'completed_at': datetime.now(timezone.utc).isoformat(),
            'checks': [{'name': name, 'passed': True} for name in checks],
            'engineering_acceptance': 'NOT_TESTED',
            'limitations': 'Synthetic HTTP responses on Linux; no actual Ollama/Open WebUI, Windows launcher, browser chat/history, production Supabase or document verification.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('output', type=Path)
    args = parser.parse_args(); result = check()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print('LOCAL LIFECYCLE CHECKS:', len(result['checks']), result['test_status'])

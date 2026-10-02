import tempfile
import unittest
from pathlib import Path

from engineering.core import AgentResult, AgentStatus, EngineerTask, MaterialRef, TaskEngine, TaskStore
from engineering.core.engineer_core import AgentRuntimeAdapter
from engineering.core.task_engine import TaskStatus


class LocalRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.store = TaskStore(Path(self.tmp.name) / 'tasks.json')
        self.engine = TaskEngine(store=self.store)
        self.task = EngineerTask('recovery', 'Synthetic local lifecycle check',
                                (MaterialRef('fixture', 'test', 'synthetic'),), ('inspection',))
        self.engine.submit(self.task)

    def test_running_is_durable_before_model_call(self):
        def handler(planned):
            disk = self.store.load()[0]
            self.assertEqual(disk.status, TaskStatus.RUNNING)
            self.assertIsNotNone(disk.started_at)
            return AgentResult(planned.task_id, planned.agent, AgentStatus.UNCERTAINTY)
        self.engine.run_next(AgentRuntimeAdapter({'inspection-agent': handler, 'final-audit-agent': handler}))
        # Exceptions inside handlers are caught by the engine; check final record too.
        self.assertEqual(self.engine.get('recovery').result_status, AgentStatus.UNCERTAINTY)

    def test_plan_and_results_survive_reopen(self):
        self.engine.run_next(AgentRuntimeAdapter())
        loaded = self.store.load()[0]
        self.assertEqual([p.agent for p in loaded.state.planned],
                         ['inspection-agent', 'final-audit-agent'])
        self.assertEqual(loaded.state.results, self.engine.get('recovery').state.results)

    def test_retry_clears_previous_result_and_error(self):
        self.engine.run_next(AgentRuntimeAdapter({'inspection-agent': lambda p: (_ for _ in ()).throw(RuntimeError('failure'))}))
        record = self.engine.get('recovery')
        record.result_status = AgentStatus.ERROR
        self.engine.requeue('recovery')
        loaded = self.store.load()[0]
        self.assertIsNone(loaded.result_status)
        self.assertIsNone(loaded.state)
        self.assertIsNone(loaded.error)

    def test_running_save_failure_prevents_execution(self):
        self.store.save = lambda records: (_ for _ in ()).throw(OSError('disk failure'))
        calls = []
        def handler(p): calls.append(p); return AgentResult(p.task_id, p.agent, AgentStatus.UNCERTAINTY)
        with self.assertRaises(OSError):
            self.engine.run_next(AgentRuntimeAdapter({'inspection-agent': handler}))
        self.assertEqual(calls, [])
        self.assertEqual(self.engine.get('recovery').status, TaskStatus.QUEUED)


if __name__ == '__main__': unittest.main()

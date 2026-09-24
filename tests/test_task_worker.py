import unittest
from unittest.mock import Mock

from engineering.core import TaskWorker, WorkerConfig, recover_stale_running_tasks
from engineering.core.task_engine import TaskEngine, TaskRecord, TaskStatus


class WorkerTests(unittest.TestCase):
    def test_empty_queue_does_not_execute(self):
        engine = TaskEngine()
        factory = Mock()
        worker = TaskWorker(engine, factory, WorkerConfig(poll_interval_seconds=0.1))
        self.assertEqual(worker.run_once(), 0)
        factory.assert_not_called()

    def test_stale_running_task_is_requeued(self):
        engine = TaskEngine()
        record = TaskRecord(task=Mock())
        record.task.task_id = "stale-1"
        record.status = TaskStatus.RUNNING
        engine._tasks["stale-1"] = record

        self.assertEqual(recover_stale_running_tasks(engine), 1)
        self.assertEqual(record.status, TaskStatus.QUEUED)
        self.assertIsNotNone(record.error)
        self.assertIsNone(record.started_at)
        self.assertIsNone(record.finished_at)


if __name__ == "__main__":
    unittest.main()

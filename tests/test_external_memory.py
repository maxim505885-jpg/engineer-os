import unittest

from engineering.memory.external_memory import (
    ExternalMemoryAdapter,
    MemoryBoundaryError,
    MemoryRecord,
    MemoryTrust,
    memory_context,
)


class ExternalMemoryBoundaryTests(unittest.TestCase):
    def test_memory_is_explicitly_not_evidence(self):
        record = MemoryRecord("m1", "Подтверждённый ранее шаблон", "report:42", MemoryTrust.CONFIRMED_REFERENCE)
        context = memory_context((record,))
        self.assertEqual(context[0]["evidentiary_status"], "NOT_EVIDENCE")
        self.assertEqual(context[0]["trust"], "CONFIRMED_REFERENCE")

    def test_unverified_is_default(self):
        record = MemoryRecord("m1", "Старый ответ модели", "chat:1")
        self.assertEqual(record.trust, MemoryTrust.UNVERIFIED)

    def test_duplicate_backend_records_fail_closed(self):
        record = MemoryRecord("m1", "Контекст", "chat:1")
        adapter = ExternalMemoryAdapter(lambda query: (record, record))
        with self.assertRaises(MemoryBoundaryError):
            adapter.search("перекрытие")

    def test_invalid_backend_record_fails_closed(self):
        adapter = ExternalMemoryAdapter(lambda query: ({"text": "raw"},))
        with self.assertRaises(MemoryBoundaryError):
            adapter.search("норма")


if __name__ == "__main__":
    unittest.main()

import os
import unittest
from unittest.mock import patch

from engineering.core.supabase_task_store import SupabaseTaskStore


class SupabaseTaskStoreTests(unittest.TestCase):
    def test_requires_server_configuration(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError):
                SupabaseTaskStore()

    def test_uuid_mapping_is_strict(self):
        self.assertEqual(
            SupabaseTaskStore._uuid_or_none("00000000-0000-0000-0000-000000000001"),
            "00000000-0000-0000-0000-000000000001",
        )
        self.assertIsNone(SupabaseTaskStore._uuid_or_none("project-1"))


if __name__ == "__main__":
    unittest.main()

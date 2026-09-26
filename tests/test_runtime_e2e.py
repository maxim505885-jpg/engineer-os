import os
import unittest
from unittest.mock import patch

from e2e.server import Handler


class RuntimeConfigTests(unittest.TestCase):
    def test_e2e_requires_explicit_enable(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertNotEqual(os.environ.get("ENGINEER_OS_E2E_ENABLED"), "true")


if __name__ == "__main__":
    unittest.main()

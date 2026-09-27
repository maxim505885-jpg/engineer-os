import logging
import unittest

from scripts.local_docling_smoke import _TableLossMonitor


class TableLossMonitorTests(unittest.TestCase):
    def test_captures_table_cell_loss_warning(self):
        monitor = _TableLossMonitor()
        logger = logging.getLogger()
        logger.addHandler(monitor)
        try:
            logging.getLogger("MatchingPostProcessor").warning(
                "15 of 229 pdf cells matched neither a row nor a column band of the 46x7 grid and were dropped from the table"
            )
        finally:
            logger.removeHandler(monitor)
        self.assertEqual(len(monitor.messages), 1)


if __name__ == "__main__":
    unittest.main()

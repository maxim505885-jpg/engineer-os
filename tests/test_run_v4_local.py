import unittest

from scripts.run_v4_local import windows


class V4LocalRunnerTests(unittest.TestCase):
    def test_covers_full_document_in_bounded_windows(self):
        planned = list(windows(534))
        self.assertEqual(planned[0], (1, 20))
        self.assertEqual(planned[-1], (521, 534))
        self.assertEqual(sum(end - start + 1 for start, end in planned), 534)


if __name__ == "__main__":
    unittest.main()

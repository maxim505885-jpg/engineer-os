import unittest

from scripts.local_docling_batch import ranges


class LocalDoclingBatchTests(unittest.TestCase):
    def test_ranges_are_bounded_and_cover_each_page_once(self):
        self.assertEqual(list(ranges(11, 16, 2)), [(11, 12), (13, 14), (15, 16)])
        with self.assertRaises(ValueError):
            list(ranges(1, 534, 2))


if __name__ == "__main__":
    unittest.main()

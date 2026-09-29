import unittest

from scripts.v4_drawing_register_check import compare_rows


class DrawingRegisterCheckTests(unittest.TestCase):
    def test_matches_wrapped_cells_but_preserves_punctuation(self):
        rows = [["Раздел", None, None], ["1", "Рисунок Ж.1. План на отм.\n+5.000;", ""]]
        self.assertEqual(compare_rows(rows, {"1": "Рисунок Ж.1. План на отм. +5.000"}), [])
        self.assertEqual(compare_rows(rows, {"1": "Рисунок Ж.1. План на отм. +5,000"}),
                         [{"figure": 1, "reason": "TEXT_MISMATCH"}])

    def test_missing_or_duplicate_source_row_remains_blocked(self):
        rows = [["1", "Рисунок Ж.1. A", ""], ["1", "Рисунок Ж.1. B", ""]]
        self.assertEqual(compare_rows(rows, {"1": "Рисунок Ж.1. A", "2": "Рисунок Ж.2. B"}),
                         [{"figure": 1, "reason": "SOURCE_ROW_COUNT_2"},
                          {"figure": 2, "reason": "SOURCE_ROW_COUNT_0"}])


if __name__ == "__main__":
    unittest.main()

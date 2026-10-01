import unittest

from scripts.v4_drawing_levels import compare_levels


class DrawingLevelTests(unittest.TestCase):
    def test_checks_exact_decimal_separator_and_sign_against_page_text(self):
        text = "Рисунок Ж.6. План на отм. +17,340; План на отм. +18,976;\nРисунок Ж.7. Разрез"
        claims = {"6": "Рисунок Ж.6. План на отм. +17,340; План на отм. +18,976",
                  "7": "Рисунок Ж.7. Разрез"}
        self.assertEqual(compare_levels(text, claims), [])
        claims["6"] = claims["6"].replace(",", ".")
        self.assertEqual(compare_levels(text, claims), [{"figure": 6,
                          "claimed": ["+17.340", "+18.976"],
                          "source": ["+17,340", "+18,976"]}])

    def test_missing_figure_fails_closed(self):
        self.assertEqual(compare_levels("Рисунок Ж.1. Без отметок", {"2": "Рисунок Ж.2. +5.000"}),
                         [{"figure": 2, "claimed": ["+5.000"], "source": None}])


if __name__ == "__main__":
    unittest.main()

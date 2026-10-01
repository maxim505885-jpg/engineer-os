import unittest

from scripts.v4_manual_page_overlay import overlay


class ManualPageOverlayTests(unittest.TestCase):
    def setUp(self):
        self.sha = "a" * 64
        self.review = {"source_sha256": self.sha, "status": "BLOCK",
                       "blocked_reasons": {"MERGED_TABLE_CELL": [490],
                                           "MISSING_TABLE_CELLS": [491, 500]}}
        self.recovered = {"source_sha256": self.sha, "status": "BLOCK",
                          "region_status": "UNCERTAINTY", "blocks": [
                              {"kind": "table_row", "text": f"Рисунок Ж.{n}.",
                               "provenance": [{"page_no": 490 if n == 1 else 491}]}
                              for n in (1, 2)]}
        stamp = "ОСК-ССК-22/0526-1 Взаи. инв. № Инв. № подл. Подп. и дата Изм. Кол.уч Лист № док. Подп. Дата"
        self.texts = {490: "Приложение Ж Ведомость чертежей Наименование Примечание "
                            f"Рисунок Ж.1. {stamp} 490",
                      491: "Результаты геодезических измерений Рисунок Ж.2. "
                           f"{stamp} 491"}

    def test_overlay_keeps_global_block_and_does_not_mutate_original(self):
        result = overlay(self.review, self.recovered, self.texts, expected_rows=2)
        self.assertEqual(result["remaining_blocked_pages"], 3)
        self.assertEqual(result["manual_page_status"], {"490": "UNCERTAINTY",
                                                         "491": "UNCERTAINTY"})
        self.assertEqual(result["status"], "BLOCK")
        self.assertEqual(result["remaining_manual_review_pages"], 1)
        self.assertEqual(self.review["blocked_reasons"]["MERGED_TABLE_CELL"], [490])

    def test_missing_page_shell_or_row_blocks_transition(self):
        for texts in ({490: self.texts[490], 491: "Рисунок Ж.2."},
                      {490: self.texts[490].replace("Примечание", ""), 491: self.texts[491]}):
            with self.subTest(texts=texts), self.assertRaises(ValueError):
                overlay(self.review, self.recovered, texts, expected_rows=2)


if __name__ == "__main__":
    unittest.main()

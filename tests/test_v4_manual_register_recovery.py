import unittest

from scripts.v4_manual_register_recovery import assemble


class ManualRegisterRecoveryTests(unittest.TestCase):
    def test_preserves_page_provenance_and_blocked_page_status(self):
        evidence = {"source_sha256": "a" * 64, "status": "BLOCK", "pages": [
            {"page": 490, "claims": [
                {"locator": "register_heading", "transcription": "Ведомость чертежей"},
                {"locator": "category_heading", "transcription": "Обмерные чертежи"},
                {"locator": "1", "transcription": "Рисунок Ж.1. План"}]},
            {"page": 491, "claims": [
                {"locator": "category_heading", "transcription": "Геодезические измерения"},
                {"locator": "2", "transcription": "Рисунок Ж.2. Разрез"}]},
        ]}
        result = assemble(evidence, {"checked_rows": 2, "mismatches": [], "status": "BLOCK"},
                          expected_rows=2)
        self.assertEqual(result["status"], "BLOCK")
        self.assertEqual(result["region_status"], "UNCERTAINTY")
        self.assertEqual([b["provenance"][0]["page_no"] for b in result["blocks"]],
                         [490, 490, 490, 491, 491])
        self.assertEqual([b["text"] for b in result["blocks"] if b["kind"] == "table_row"],
                         ["Рисунок Ж.1. План", "Рисунок Ж.2. Разрез"])

    def test_rejects_unverified_or_incomplete_rows(self):
        evidence = {"source_sha256": "a" * 64, "status": "BLOCK", "pages": [
            {"page": 490, "claims": [{"locator": "1", "transcription": "Рисунок Ж.1"}]}]}
        with self.assertRaisesRegex(ValueError, "verification"):
            assemble(evidence, {"checked_rows": 1, "mismatches": [1], "status": "BLOCK"},
                     expected_rows=1)
        with self.assertRaisesRegex(ValueError, "verification"):
            assemble(evidence, {"checked_rows": 1, "mismatches": [], "status": "BLOCK"},
                     expected_rows=2)
        with self.assertRaisesRegex(ValueError, "rows"):
            assemble(evidence, {"checked_rows": 2, "mismatches": [], "status": "BLOCK"},
                     expected_rows=2)


if __name__ == "__main__":
    unittest.main()

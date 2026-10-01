import unittest

from scripts.v4_registry_pair_check import compare


class RegistryPairCheckTests(unittest.TestCase):
    def test_same_organization_different_scope_is_recorded_without_acceptance(self):
        survey = {"source_sha256": "a" * 64, "status": "BLOCK", "pages": [
            {"page": 486, "claims": [{"locator": "ogrn", "transcription": "123"},
                                      {"locator": "1.6", "transcription": "И-1"},
                                      {"locator": "extract_number", "transcription": "A"}]}]}
        design = {"source_sha256": "a" * 64, "status": "BLOCK", "pages": [
            {"page": 488, "claims": [{"locator": "ogrn", "transcription": "123"},
                                      {"locator": "1.6", "transcription": "П-2"},
                                      {"locator": "extract_number", "transcription": "B"}]}]}
        result = compare(survey, design, common=("ogrn",), distinct=("1.6", "extract_number"))
        self.assertEqual(result["status"], "BLOCK")
        self.assertEqual(result["shared_identity"]["ogrn"], "123")
        self.assertEqual(result["distinct_fields"]["1.6"], ["И-1", "П-2"])
        design["pages"][0]["claims"][0]["transcription"] = "999"
        with self.assertRaisesRegex(ValueError, "identity"):
            compare(survey, design, common=("ogrn",), distinct=("1.6",))

    def test_repeated_page_marks_do_not_mask_duplicate_registry_fields(self):
        survey = {"source_sha256": "a" * 64, "status": "BLOCK", "pages": [
            {"claims": [{"locator": "ogrn", "transcription": "123"},
                        {"locator": "sheet_stamp", "transcription": "one"}]},
            {"claims": [{"locator": "sheet_stamp", "transcription": "two"}]}]}
        design = {"source_sha256": "a" * 64, "status": "BLOCK", "pages": [
            {"claims": [{"locator": "ogrn", "transcription": "123"}]}]}
        self.assertEqual(compare(survey, design, common=("ogrn",), distinct=())["status"], "BLOCK")
        survey["pages"][1]["claims"].append({"locator": "ogrn", "transcription": "123"})
        with self.assertRaisesRegex(ValueError, "duplicate registry field ogrn"):
            compare(survey, design, common=("ogrn",), distinct=())


if __name__ == "__main__":
    unittest.main()

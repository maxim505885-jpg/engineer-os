import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from scripts.v4_manual_evidence import validate


class ManualEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "source.pdf"
        self.source.write_bytes(b"same PDF")
        self.digest = hashlib.sha256(self.source.read_bytes()).hexdigest()
        self.review = self.root / "review.json"
        self.review.write_text(json.dumps({"source_sha256": self.digest, "status": "BLOCK",
                                           "blocked_reasons": {"MERGED_TABLE_CELL": [488]}}))
        self.data = {"source_sha256": self.digest, "status": "BLOCK", "pages": [{
            "page": 488, "required_locators": ["1.1", "1.8", "qr"], "claims": [
                {"locator": "1.1", "transcription": "6150032997", "source": "rendered_pdf"},
                {"locator": "1.8", "transcription": "", "observed_blank": True,
                 "source": "rendered_pdf"},
            ]}]}

    def test_accepts_source_bound_partial_evidence_without_upgrading_status(self):
        result = validate(self.source, self.review, self.data)
        self.assertEqual(result, {"pages": 1, "claims": 2, "status": "BLOCK",
                                  "required": 3, "missing": 1,
                                  "missing_by_page": {"488": ["qr"]}})

    def test_rejects_wrong_source_page_or_acceptance(self):
        for change, error in [
            ({"source_sha256": "0" * 64}, "SHA-256"),
            ({"status": "PASS"}, "BLOCK"),
            ({"pages": [{"page": 489, "claims": self.data["pages"][0]["claims"]}]}, "blocked"),
        ]:
            with self.subTest(change=change):
                with self.assertRaisesRegex(ValueError, error):
                    validate(self.source, self.review, {**self.data, **change})

    def test_rejects_duplicate_or_unmarked_blank_claims(self):
        claim = self.data["pages"][0]["claims"][0]
        for claims in ([claim, claim], [{**claim, "transcription": ""}]):
            with self.subTest(claims=claims), self.assertRaises(ValueError):
                validate(self.source, self.review, {**self.data, "pages": [
                    {"page": 488, "required_locators": ["1.1", "1.8", "qr"], "claims": claims}]})

    def test_rejects_unplanned_claim_or_duplicate_requirement(self):
        entry = self.data["pages"][0]
        for changed in (
            {**entry, "required_locators": ["1.1", "1.1"]},
            {**entry, "required_locators": ["1.8", "qr"]},
        ):
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                validate(self.source, self.review, {**self.data, "pages": [changed]})


if __name__ == "__main__":
    unittest.main()

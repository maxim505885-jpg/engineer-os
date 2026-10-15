"""Synthetic fixtures exercise the offline CLI, never a real PDF acceptance."""

import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/evaluate_docling_extraction.py"


class ExtractionRegressionTests(unittest.TestCase):
    def setUp(self):
        self.baseline = {
            "schema_version": 1, "source_sha256": "a" * 64,
            "project_id": "synthetic-project", "document_id": "synthetic-document",
            "page_start": 1, "page_end": 2,
            "review": {"reviewer": "test fixture author", "reviewed_at": "2026-10-03T18:00:00Z",
                       "source_ref": "synthetic fixture, not an engineering document"},
            "pages": [
                {"page_no": 1, "required_text": ["Фундамент"], "required_table_rows": []},
                {"page_no": 2, "required_text": [],
                 "required_table_rows": ["Параметр: Нагрузка | Значение: 12 кПа | Обоснование: Тест"]},
            ],
        }
        self.extraction = {
            **{k: self.baseline[k] for k in (
                "source_sha256", "project_id", "document_id", "page_start", "page_end")},
            "parser": "docling", "status": "UNCERTAINTY",
            "blocks": [
                {"block_id": "b1", "kind": "text", "text": "Фундамент здания",
                 "provenance": [{"page_no": 1, "bbox": None}]},
                {"block_id": "b2", "kind": "table_row",
                 "text": "Параметр: Нагрузка | Значение: 12 кПа | Обоснование: Тест",
                 "provenance": [{"page_no": 2, "bbox": None}]},
            ],
        }

    def run_cli(self, baseline=None, extraction=None, output_to_input=False):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            baseline_path, extraction_path = root / "baseline.json", root / "extraction.json"
            baseline_path.write_text(json.dumps(self.baseline if baseline is None else baseline), encoding="utf-8")
            extraction_path.write_text(json.dumps(self.extraction if extraction is None else extraction), encoding="utf-8")
            before = extraction_path.read_bytes()
            output = extraction_path if output_to_input else root / "report.json"
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(baseline_path), str(extraction_path), "--output", str(output)],
                capture_output=True, text=True,
            )
            self.assertEqual(extraction_path.read_bytes(), before, "evaluation must not rewrite extraction")
            report = json.loads(result.stdout) if result.stdout else None
            if not output_to_input:
                self.assertEqual(json.loads(output.read_text(encoding="utf-8")), report)
            return result, report

    def test_matches_cyrillic_and_table_values_without_accepting_document(self):
        result, report = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(report["status"], "PASS")
        self.assertFalse(report["acceptance_granted"])
        self.assertEqual(report["document_status"], "UNCERTAINTY")
        self.assertEqual(report["evidentiary_status"], "NOT_EVIDENCE")
        self.assertEqual(report["checks_passed"], 2)
        self.assertEqual(len(report["extraction_sha256"]), 64)

    def test_changed_table_value_blocks(self):
        self.extraction["blocks"][1]["text"] = "Параметр: Нагрузка | Значение: 21 кПа | Обоснование: Тест"
        result, report = self.run_cli()
        self.assertEqual(result.returncode, 2)
        self.assertEqual(report["status"], "BLOCK")
        self.assertEqual(report["checks_passed"], 1)

    def test_text_on_wrong_page_cannot_satisfy_expectation(self):
        self.extraction["blocks"][0]["provenance"][0]["page_no"] = 2
        result, report = self.run_cli()
        self.assertEqual(result.returncode, 2)
        self.assertEqual(report["status"], "BLOCK")

    def test_duplicate_expected_rows_require_distinct_rows(self):
        self.baseline["pages"][1]["required_table_rows"] *= 2
        result, report = self.run_cli()
        self.assertEqual(result.returncode, 2)
        self.assertEqual(report["status"], "BLOCK")

    def test_multi_page_text_cannot_prove_which_page_contains_a_phrase(self):
        self.extraction["blocks"][0]["provenance"].append({"page_no": 2})
        result, report = self.run_cli()
        self.assertEqual(result.returncode, 2)
        self.assertEqual(report["status"], "BLOCK")

    def test_identity_and_provenance_fail_closed(self):
        for mutate in (
            lambda x: x.update(source_sha256="b" * 64),
            lambda x: x.update(document_id="other-document"),
            lambda x: x.update(status="BLOCK"),
            lambda x: x.update(status="ACCEPTED"),
            lambda x: x.update(parser="other-parser"),
            lambda x: x["blocks"][0].update(provenance=[]),
            lambda x: x["blocks"][0]["provenance"][0].update(page_no=True),
            lambda x: x["blocks"][0]["provenance"][0].update(page_no=3),
            lambda x: x["blocks"][1]["provenance"].append({"page_no": 1}),
            lambda x: x["blocks"][1].update(block_id="b1"),
        ):
            with self.subTest(mutation=mutate):
                extraction = copy.deepcopy(self.extraction)
                mutate(extraction)
                result, report = self.run_cli(extraction=extraction)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(report["status"], "BLOCK")

    def test_unreviewed_empty_and_partial_baselines_cannot_pass(self):
        for mutate in (
            lambda x: x.update(review=None),
            lambda x: x["review"].update(reviewed_at="not-a-date"),
            lambda x: x.update(pages=[]),
            lambda x: x["pages"].pop(),
            lambda x: x["pages"][0].update(required_text=[]),
        ):
            with self.subTest(mutation=mutate):
                baseline = copy.deepcopy(self.baseline)
                mutate(baseline)
                result, report = self.run_cli(baseline=baseline)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(report["status"], "BLOCK")

    def test_output_cannot_overwrite_inputs(self):
        result, report = self.run_cli(output_to_input=True)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(report["status"], "BLOCK")

    def test_unbounded_page_range_is_rejected_before_allocating_page_sets(self):
        self.baseline["page_end"] = 1_000_000_000
        self.extraction["page_end"] = 1_000_000_000
        result, report = self.run_cli()
        self.assertEqual(result.returncode, 2)
        self.assertEqual(report["status"], "BLOCK")

    def test_missing_and_malformed_inputs_return_block_report(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bad = root / "bad.json"
            for content in ("not JSON", '{"source_sha256": "a", "source_sha256": "b"}', "NaN"):
                bad.write_text(content, encoding="utf-8")
                result = subprocess.run([sys.executable, str(SCRIPT), str(bad), str(bad)],
                                        capture_output=True, text=True)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(json.loads(result.stdout)["status"], "BLOCK")
            result = subprocess.run([sys.executable, str(SCRIPT), str(root / "missing.json"), str(bad)],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertTrue(json.loads(result.stdout)["errors"])


if __name__ == "__main__":
    unittest.main()

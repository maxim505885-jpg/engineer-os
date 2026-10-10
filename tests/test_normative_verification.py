import unittest

from engineering.normative.verification import (
    NormativeVerificationRecord,
    gate_normative_verification,
)


class NormativeVerificationTests(unittest.TestCase):
    def _record(self, **overrides):
        data = dict(
            document="СП TEST",
            edition="2026",
            scope="Несущие конструкции",
            clause="1.2.3",
            requirement="Проверенное требование",
            actual_condition="Установленный факт",
            evidence_ids=("ev-1",),
            comparison="Сопоставление требования и факта",
            conclusion="Вывод",
        )
        data.update(overrides)
        return NormativeVerificationRecord(**data)

    def test_complete_chain_is_not_accepted_only_ready_for_expert_verification(self):
        result = gate_normative_verification(self._record())
        self.assertEqual(result.status, "READY_FOR_EXPERT_VERIFICATION")
        self.assertEqual(result.missing_fields, ())

    def test_clause_without_evidence_blocks(self):
        result = gate_normative_verification(self._record(evidence_ids=()))
        self.assertEqual(result.status, "BLOCK")
        self.assertIn("evidence_ids", result.missing_fields)

    def test_missing_edition_scope_or_requirement_blocks(self):
        result = gate_normative_verification(
            self._record(edition="", scope="", requirement="")
        )
        self.assertEqual(result.status, "BLOCK")
        self.assertEqual(
            result.missing_fields,
            ("edition", "scope", "requirement"),
        )


if __name__ == "__main__":
    unittest.main()

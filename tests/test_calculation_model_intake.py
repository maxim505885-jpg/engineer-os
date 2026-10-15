import unittest

from engineering.calculation.model_intake import (
    CalculationArtifact,
    CalculationArtifactRole,
    audit_calculation_model_intake,
)


class CalculationModelIntakeTests(unittest.TestCase):
    def _artifact(self, role):
        return CalculationArtifact(
            artifact_id="artifact-" + role.value.lower(),
            role=role,
            source_sha256="a" * 64,
            source_ref="file:" + role.value.lower(),
        )

    def test_missing_model_inputs_block(self):
        result = audit_calculation_model_intake(
            (self._artifact(CalculationArtifactRole.MODEL),)
        )
        self.assertEqual(result.status, "BLOCK")
        self.assertIn(CalculationArtifactRole.LOADS_COMBINATIONS, result.missing_roles)
        self.assertIn(CalculationArtifactRole.ACTUAL_STRUCTURE_REFERENCE, result.missing_roles)

    def test_complete_intake_is_only_ready_for_semantic_review(self):
        result = audit_calculation_model_intake(
            tuple(self._artifact(role) for role in CalculationArtifactRole)
        )
        self.assertEqual(result.status, "READY_FOR_SEMANTIC_REVIEW")
        self.assertEqual(result.missing_roles, ())

    def test_bad_hash_is_rejected(self):
        with self.assertRaises(ValueError):
            CalculationArtifact("x", CalculationArtifactRole.MODEL, "bad", "file:x")

    def test_duplicate_artifact_id_is_rejected(self):
        a = self._artifact(CalculationArtifactRole.MODEL)
        b = CalculationArtifact(
            a.artifact_id,
            CalculationArtifactRole.GEOMETRY,
            "b" * 64,
            "file:geometry",
        )
        with self.assertRaises(ValueError):
            audit_calculation_model_intake((a, b))


if __name__ == "__main__":
    unittest.main()

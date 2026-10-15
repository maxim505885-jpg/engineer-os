import unittest
import importlib.util
from dataclasses import replace


@unittest.skipUnless(importlib.util.find_spec('Pynite'),'optional requirements-calculation.txt not installed')
class ControlBeamTests(unittest.TestCase):
    def inputs(self):
        from engineering.calculation.control_beam import BeamInput
        return BeamInput(length_m=6.,elastic_modulus_pa=210e9,inertia_m4=8e-6,
                         area_m2=0.003,load_n_m=1000.,source_sha256='a'*64,
                         evidence_ids=('synthetic-benchmark',),units='N_m_Pa')

    def test_simply_supported_udl_matches_independent_closed_form(self):
        from engineering.calculation.control_beam import calculate_beam
        result=calculate_beam(self.inputs())
        self.assertEqual(result['status'],'PASS')
        self.assertAlmostEqual(result['results']['reaction_left_n'],3000.,places=5)
        self.assertAlmostEqual(result['results']['reaction_right_n'],3000.,places=5)
        self.assertAlmostEqual(abs(result['results']['midspan_moment_nm']),4500.,places=5)
        expected=5*1000*6**4/(384*210e9*8e-6)
        self.assertAlmostEqual(-result['results']['midspan_deflection_m'],expected,places=9)
        self.assertEqual(result['data_class'],'CALCULATED')
        self.assertFalse(result['acceptance_granted'])
        self.assertEqual(result['source_sha256'],'a'*64)

    def test_invalid_units_nonfinite_zero_geometry_and_missing_provenance_block(self):
        from engineering.calculation.control_beam import calculate_beam
        for changes in (dict(units='kN_mm'),dict(length_m=0),dict(inertia_m4=-1),
                        dict(load_n_m=float('nan')),dict(evidence_ids=()),dict(source_sha256='bad')):
            with self.subTest(changes=changes):
                result=calculate_beam(replace(self.inputs(),**changes))
                self.assertEqual(result['status'],'BLOCK')
                self.assertNotIn('results',result)

    def test_zero_load_is_valid_and_never_accepts_structure(self):
        from engineering.calculation.control_beam import calculate_beam
        result=calculate_beam(replace(self.inputs(),load_n_m=0))
        self.assertEqual(result['status'],'PASS')
        self.assertEqual(result['results']['reaction_left_n'],0)
        self.assertFalse(result['actual_structure_verified'])

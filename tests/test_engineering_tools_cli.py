import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class EngineeringToolsCLITests(unittest.TestCase):
    def test_rectangle_cli_returns_geometric_properties_not_acceptance(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'section.json'
            path.write_text(json.dumps(dict(width_m=.2,height_m=.4,source_sha256='a'*64,
                evidence_ids=['synthetic'],units='N_m_Pa')))
            result=subprocess.run([sys.executable,'scripts/engineering_tools.py','rectangle',str(path)],capture_output=True)
            self.assertEqual(result.returncode,0,result.stderr)
            data=json.loads(result.stdout)
            self.assertAlmostEqual(data['results']['area_m2'],.08)
            self.assertFalse(data['acceptance_granted'])

    @unittest.skipUnless(importlib.util.find_spec('Pynite'),'optional Pynite dependency absent')
    def test_frame_cli_runs_typed_source_bound_cantilever(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'frame.json'
            path.write_text(json.dumps(dict(nodes=[dict(name='A',x_m=0.,y_m=0.,fix_x=True,fix_y=True,fix_rz=True),
                dict(name='B',x_m=2.,y_m=0.)],members=[dict(name='M',start='A',end='B',elastic_modulus_pa=210e9,
                area_m2=.01,iz_m4=1e-5)],loads=[['B',0.,-1000.,0.]],source_sha256='a'*64,
                evidence_ids=['synthetic'],units='N_m_Pa',kind='frame')))
            result=subprocess.run([sys.executable,'scripts/engineering_tools.py','planar',str(path)],capture_output=True)
            self.assertEqual(result.returncode,0,result.stderr)
            data=json.loads(result.stdout)
            self.assertAlmostEqual(data['results']['nodes']['A']['reaction_fy_n'],1000.)
            self.assertFalse(data['actual_structure_verified'])

    @unittest.skipUnless(importlib.util.find_spec('ifcopenshell'),'optional IFC dependency absent')
    def test_ifc_cli_preserves_source_and_emits_unaccepted_inventory(self):
        source=Path(__file__).parent/'fixtures/bim/reference.ifc'
        sha=hashlib.sha256(source.read_bytes()).hexdigest()
        result=subprocess.run([sys.executable,'scripts/engineering_tools.py','ifc',str(source),'--sha256',sha],capture_output=True)
        self.assertEqual(result.returncode,0,result.stderr)
        data=json.loads(result.stdout)
        self.assertEqual(len(data['elements']),4)
        self.assertFalse(data['acceptance_granted'])
        self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),sha)

    def test_ifc_cli_bad_identity_is_blocked_with_json(self):
        source=Path(__file__).parent/'fixtures/bim/reference.ifc'
        result=subprocess.run([sys.executable,'scripts/engineering_tools.py','ifc',str(source),'--sha256','0'*64],capture_output=True)
        self.assertEqual(result.returncode,2)
        self.assertEqual(json.loads(result.stdout)['status'],'BLOCK')

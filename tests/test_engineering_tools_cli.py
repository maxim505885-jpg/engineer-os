import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest


class EngineeringToolsCLITests(unittest.TestCase):
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

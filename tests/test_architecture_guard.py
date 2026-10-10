import tempfile
import unittest
from pathlib import Path


class ArchitectureGuardTests(unittest.TestCase):
    def audit(self, files):
        try:
            from scripts.architecture_guard import audit
        except ImportError:
            self.fail('Architecture release guard is not available')
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for name, text in files.items():
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text, encoding='utf-8')
            return audit(root)

    def test_domain_cannot_import_cabinet_or_inference(self):
        for statement in ['import engineering.local_app.store as s',
                          'from ..local_app import store',
                          'from engineering.model_gateway import openai_compatible',
                          'import runtime']:
            with self.subTest(statement=statement):
                errors = self.audit({'engineering/normative/check.py': statement})
                self.assertTrue(errors)
                self.assertIn('DOMAIN_DEPENDENCY', errors[0])

    def test_runtime_cannot_depend_on_local_cabinet(self):
        self.assertTrue(self.audit({'runtime/check.py': 'from engineering.local_app import store'}))

    def test_solver_execution_stays_in_bridge(self):
        self.assertTrue(self.audit({'engineering/calculation/check.py': 'import subprocess'}))
        self.assertEqual(self.audit({'engineering/calculation/solver_bridge.py': 'import subprocess\nsubprocess.run(["solver"], shell=False)'}), [])

    def test_bridge_cannot_enable_or_guess_shell(self):
        for value in ['True', 'flag', 'None']:
            with self.subTest(value=value):
                self.assertTrue(self.audit({'engineering/calculation/solver_bridge.py': f'import subprocess\nsubprocess.run(["solver"], shell={value})'}))

    def test_syntax_failure_blocks_instead_of_skipping(self):
        self.assertTrue(self.audit({'engineering/normative/check.py': 'def broken('}))

    def test_pure_domain_imports_and_unrelated_layers_allowed(self):
        self.assertEqual(self.audit({'engineering/normative/check.py': 'from decimal import Decimal',
                                     'engineering/local_app/worker.py': 'import subprocess'}), [])

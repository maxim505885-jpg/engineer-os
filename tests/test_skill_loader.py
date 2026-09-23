import tempfile
import unittest
from pathlib import Path

from engineering.core.skill_loader import SkillLoader


class SkillLoaderTests(unittest.TestCase):
    def test_load_skill(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill = root / "skills" / "demo"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text("# Demo\\nRule: no invention.", encoding="utf-8")
            self.assertIn("no invention", SkillLoader(root).load("demo"))

    def test_rejects_path_traversal(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                SkillLoader(tmp).load("../secret")

from __future__ import annotations

from pathlib import Path


class SkillLoader:
    """Loads ENGINEER OS skill instructions from the repository."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)

    def load(self, skill: str) -> str:
        if not skill or "/" in skill or "\\" in skill or ".." in skill:
            raise ValueError(f"Invalid skill name: {skill!r}")
        path = self.root / "skills" / skill / "SKILL.md"
        if not path.is_file():
            raise FileNotFoundError(f"ENGINEER OS skill not found: {skill}")
        return path.read_text(encoding="utf-8")

    def load_optional(self, skill: str) -> str | None:
        try:
            return self.load(skill)
        except FileNotFoundError:
            return None

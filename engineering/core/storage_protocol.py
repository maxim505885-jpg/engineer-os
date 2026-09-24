from __future__ import annotations

from typing import Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    from .task_engine import TaskRecord


class TaskRepository(Protocol):
    """Persistence boundary used by Task Engine."""

    def save(self, records: tuple["TaskRecord", ...] | list["TaskRecord"]) -> None: ...
    def load(self) -> list["TaskRecord"]: ...

"""ENGINEER OS core contracts and orchestration primitives."""

from .contracts import AgentResult, AgentStatus, EngineerTask, MaterialRef, SpecialistTask
from .engineer_core import EngineerCore
from .runner import EngineerRunner, RunSummary
from .task_engine import TaskEngine, TaskRecord, TaskStatus
from .task_store import MaterialRecord, ProjectRecord, RunRecord, TaskStore
from .supabase_task_store import SupabaseTaskStore
from .task_worker import TaskWorker, WorkerConfig, recover_stale_running_tasks
from engineering.runtime.router import EngineeringRuntimeRouter, RuntimePolicy

__all__ = [
    "AgentResult", "AgentStatus", "EngineerTask", "MaterialRef", "SpecialistTask", "EngineerCore", "EngineerRunner", "RunSummary", "TaskEngine", "TaskRecord", "TaskStatus", "TaskStore", "ProjectRecord", "MaterialRecord", "RunRecord"
]

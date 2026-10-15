"""Read-only project-scoped Agent Memory adapter (pinned REST memories API)."""
from __future__ import annotations

from pathlib import Path
from urllib.parse import quote, urlencode

from engineering.integrations.local_http import IntegrationError, get_local_json, local_url
from engineering.memory.external_memory import ExternalMemoryAdapter, MemoryRecord


def resolve_secret(origin: str, explicit: str | None, secret_file: Path | None = None) -> str:
    """Read the upstream generated secret only after validating a loopback destination."""
    local_url(origin)
    if explicit is not None:
        return explicit
    path = secret_file if secret_file is not None else Path.home() / ".agentmemory" / "secret"
    try:
        with path.open("r", encoding="utf-8") as source:
            secret = source.read(8193).strip()
    except FileNotFoundError:
        return ""
    except (OSError, UnicodeError):
        raise IntegrationError("Cannot read the local Agent Memory secret") from None
    if len(secret) > 8192 or "\n" in secret or "\r" in secret:
        raise IntegrationError("Invalid local Agent Memory secret")
    return secret


class AgentMemoryHTTPAdapter(ExternalMemoryAdapter):
    def __init__(self, origin: str, project: str, *, enabled: bool = False,
                 secret: str = "", limit: int = 10) -> None:
        self.origin = local_url(origin)
        if not isinstance(project, str) or not project.strip():
            raise IntegrationError("project is required")
        if type(limit) is not int or not 1 <= limit <= 50:
            raise IntegrationError("limit must be an integer from 1 to 50")
        self.project = project.strip()
        self.enabled = enabled
        self.secret = secret
        self.limit = limit
        super().__init__(self._recall)

    def _recall(self, query: str) -> tuple[MemoryRecord, ...]:
        if self.enabled is not True:
            raise IntegrationError("Agent Memory is disabled; enable it explicitly")
        params = urlencode({"project": self.project, "q": query, "latest": "true", "limit": self.limit})
        payload = get_local_json(self.origin, "/agentmemory/memories?" + params, secret=self.secret)
        items = payload.get("memories")
        if not isinstance(items, list) or len(items) > self.limit:
            raise IntegrationError("Invalid Agent Memory memories response")
        records = []
        seen = set()
        for item in items:
            if (not isinstance(item, dict) or item.get("project") != self.project
                    or item.get("isLatest") is not True):
                raise IntegrationError("Unscoped or superseded memory rejected")
            memory_id, content = item.get("id"), item.get("content")
            if (not isinstance(memory_id, str) or not memory_id.strip()
                    or not isinstance(content, str) or not content.strip() or memory_id in seen):
                raise IntegrationError("Invalid or duplicate memory record")
            seen.add(memory_id)
            records.append(MemoryRecord(memory_id, content,
                           self.origin + "/agentmemory/memories/" + quote(memory_id, safe="")))
        return tuple(records)

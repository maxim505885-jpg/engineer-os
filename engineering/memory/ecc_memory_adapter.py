"""Read ECC records through host-configured transports as non-evidentiary context.

No plugin installation, subprocess, write, trust promotion or acceptance occurs
here. Transport identity and project partition isolation belong to the host.
"""
from __future__ import annotations

from datetime import datetime
import hashlib
import re
from typing import Callable

from .external_memory import ExternalMemoryAdapter, MemoryBoundaryError, MemoryRecord

_FIELDS = {'schema', 'id', 'title', 'kind', 'scope', 'trust', 'status', 'sourceHarness',
           'targetHarnesses', 'tags', 'links', 'createdAt', 'updatedAt', 'body'}
_KINDS = {'context', 'decision', 'fact', 'handoff', 'lesson', 'note', 'preference', 'runbook'}
_ID = re.compile(r'mem_[a-z0-9][a-z0-9_-]{2,127}\Z')
_SLUG = re.compile(r'[a-z0-9][a-z0-9._-]{0,63}\Z')
_CONTROL = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f\u202a-\u202e\u2066-\u2069]')


def _reject():
    raise MemoryBoundaryError('ECC memory response is invalid, incomplete or outside configured scope')


def _text(value: object, limit: int) -> bool:
    if not isinstance(value, str) or not value.strip() or len(value) > limit or _CONTROL.search(value):
        return False
    try:
        return len(value.encode('utf-8')) <= limit
    except UnicodeError:
        return False


def _strings(value: object, pattern, limit: int, minimum: int = 0) -> bool:
    return (isinstance(value, list) and minimum <= len(value) <= limit
            and all(isinstance(v, str) and pattern.fullmatch(v) for v in value)
            and len(value) == len(set(value)))


def _timestamp(value: object) -> bool:
    if not isinstance(value, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z', value):
        return False
    try:
        datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError:
        return False
    return True


class ECCMemoryAdapter(ExternalMemoryAdapter):
    """Fail-closed search/read bridge for ecc.memory.v1.

    search_transport(query) returns the ECC search response; read_transport(id,
    scope) returns an ECC read response. Both must be bound by the host to the
    same authorized project vault. The body is read in full, never from excerpt.
    """

    def __init__(self, search_transport: Callable[[str], dict],
                 read_transport: Callable[[str, str], dict], *, harness: str,
                 scopes: tuple[str, ...] = ('project', 'team')):
        if (not isinstance(harness, str) or not _SLUG.fullmatch(harness)
                or not scopes or any(s not in ('project', 'team') for s in scopes)
                or len(scopes) != len(set(scopes))):
            raise ValueError('Configure one harness and explicit project/team scopes')
        self._search_transport = search_transport
        self._read_transport = read_transport
        self.harness = harness
        self.scopes = scopes
        super().__init__(self._retrieve)

    def _validate(self, memory: object, *, body: bool) -> None:
        fields = _FIELDS if body else _FIELDS - {'body'}
        if not isinstance(memory, dict) or set(memory) != fields:
            _reject()
        if (memory['schema'] != 'ecc.memory.v1' or memory['trust'] != 'unreviewed'
                or memory['status'] != 'active' or memory['scope'] not in self.scopes
                or memory['kind'] not in _KINDS or not isinstance(memory['id'], str)
                or not _ID.fullmatch(memory['id']) or not _text(memory['title'], 200)
                or not isinstance(memory['sourceHarness'], str)
                or not _SLUG.fullmatch(memory['sourceHarness'])
                or not _strings(memory['targetHarnesses'], _SLUG, 32, 1)
                or not ({'all', self.harness} & set(memory['targetHarnesses']))
                or not _strings(memory['tags'], _SLUG, 32)
                or not _strings(memory['links'], _ID, 64)
                or not _timestamp(memory['createdAt']) or not _timestamp(memory['updatedAt'])
                or memory['updatedAt'] < memory['createdAt']
                or (body and not _text(memory['body'], 65536))):
            _reject()

    def _retrieve(self, query: str) -> tuple[MemoryRecord, ...]:
        if not _text(query, 500): _reject()
        try:
            payload = self._search_transport(query)
            if not isinstance(payload, dict): _reject()
            diagnostics = payload.get('diagnostics')
            if (not isinstance(diagnostics, dict)
                    or any(type(diagnostics.get(k)) is not int or diagnostics[k] != 0
                           for k in ('invalidFileCount', 'skippedSymlinkCount'))
                    or any(diagnostics.get(k) is not False for k in ('truncated', 'diagnosticsTruncated'))):
                _reject()
            results = payload.get('results')
            if not isinstance(results, list) or len(results) > 100: _reject()
            records = []
            seen = set()
            for item in results:
                if not isinstance(item, dict): _reject()
                summary = item.get('memory')
                self._validate(summary, body=False)
                if summary['id'] in seen: _reject()
                seen.add(summary['id'])
                read = self._read_transport(summary['id'], summary['scope'])
                if not isinstance(read, dict): _reject()
                memory = read.get('memory')
                self._validate(memory, body=True)
                if {k: v for k, v in memory.items() if k != 'body'} != summary: _reject()
                digest = hashlib.sha256(memory['body'].encode('utf-8')).hexdigest()
                locator = f"ecc-memory:{memory['scope']}:{memory['sourceHarness']}:{memory['id']}:sha256:{digest}"
                records.append(MemoryRecord(memory['id'], memory['body'], locator))
            return tuple(records)
        except Exception:
            # Neither backend errors nor recalled content enter logs/exceptions.
            raise MemoryBoundaryError('ECC memory recall failed closed') from None

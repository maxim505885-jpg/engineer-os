"""Opt-in, project-bound read transport for a reviewed ECC source checkout."""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import shutil
import subprocess

from .ecc_memory_adapter import ECCMemoryAdapter
from .external_memory import MemoryBoundaryError

SUPPORTED_ECC_COMMIT = 'ef648e01899ba3e8dc6371642deaaf64b4477775'


class ECCCLITransport:
    """Runs only search/read from the pinned ECC checkout; never initializes/writes.

    The local operator owns/trusts the checkout and executable paths. Git checks
    detect ordinary drift; they are not authentication or a filesystem race fence.
    """
    def __init__(self, ecc_checkout: str | Path, project: str | Path, *,
                 vault: str | Path | None = None, harness: str = 'codex',
                 scopes: tuple[str, ...] = ('project', 'team'), limit: int = 20,
                 node: str = 'node', git: str = 'git', runner=subprocess.run):
        self.ecc = Path(ecc_checkout).resolve()
        self.project = Path(project).resolve()
        self.vault = Path(vault).resolve() if vault is not None else self.project / '.engineer-os/ecc-memory'
        if (not self.project.is_dir() or not self.vault.is_relative_to(self.project)
                or self.vault == self.project):
            raise ValueError('Choose a separate vault directory inside the project')
        if type(limit) is not int or not 1 <= limit <= 100:
            raise ValueError('Recall limit must be between 1 and 100')
        # Reuse the adapter's harness/scope configuration checks before execution.
        ECCMemoryAdapter(lambda q: {}, lambda i, s: {}, harness=harness, scopes=scopes)
        self.harness, self.scopes, self.limit = harness, tuple(scopes), limit
        self._runner = runner
        self.node = shutil.which(node)
        self.git = shutil.which(git)
        if not self.node or not self.git or not (self.ecc / 'scripts/memory.js').is_file():
            raise MemoryBoundaryError('ECC checkout, Node or Git is unavailable')
        self._env = {'PATH': os.environ.get('PATH', ''),
                     'ECC_MEMORY_PROJECT_ROOT': str(self.vault),
                     'ECC_MEMORY_USER_ROOT': str(self.vault / '.user-disabled'),
                     'ECC_MEMORY_HARNESS': harness}
        for name in ('SYSTEMROOT', 'WINDIR', 'COMSPEC', 'PATHEXT', 'TEMP', 'TMP'):
            if name in os.environ: self._env[name] = os.environ[name]
        head = self._execute([self.git, '-C', str(self.ecc), 'rev-parse', 'HEAD']).strip()
        status = self._execute([self.git, '-C', str(self.ecc), 'status', '--porcelain'])
        if head != SUPPORTED_ECC_COMMIT or status.strip():
            raise MemoryBoundaryError('ECC source revision differs or checkout is not clean')

    def _execute(self, command: list[str]) -> str:
        try:
            result = self._runner(command, cwd=str(self.project), env=dict(self._env),
                                  capture_output=True, text=True, encoding='utf-8',
                                  timeout=30, shell=False, check=False)
            if result.returncode or len(result.stdout.encode('utf-8')) > 1024 * 1024:
                raise ValueError('unavailable response')
            return result.stdout
        except Exception:
            raise MemoryBoundaryError('ECC read process failed closed') from None

    def _json(self, arguments: list[str]) -> dict:
        try:
            payload = json.loads(self._execute([self.node, str(self.ecc / 'scripts/memory.js'),
                                               *arguments, '--json']))
            if not isinstance(payload, dict): raise ValueError('invalid response')
            return payload
        except Exception:
            raise MemoryBoundaryError('ECC read response failed closed') from None

    def search(self, query: str) -> dict:
        args = ['search', query, '--target-harness', self.harness, '--limit', str(self.limit)]
        for scope in self.scopes: args.extend(['--scope', scope])
        return self._json(args)

    def read(self, memory_id: str, scope: str) -> dict:
        if (not isinstance(memory_id, str) or not re.fullmatch(r'mem_[a-z0-9][a-z0-9_-]{2,127}', memory_id)
                or scope not in self.scopes):
            raise MemoryBoundaryError('ECC read identifier or scope is invalid')
        return self._json(['read', memory_id, '--scope', scope])

    def adapter(self) -> ECCMemoryAdapter:
        return ECCMemoryAdapter(self.search, self.read, harness=self.harness, scopes=self.scopes)

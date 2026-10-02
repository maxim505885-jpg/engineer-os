"""Synthetic real ECC CLI check of ENGINEER OS's opt-in read adapter."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
import platform
from pathlib import Path
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from engineering.memory.ecc_cli_transport import ECCCLITransport
from engineering.memory.external_memory import MemoryBoundaryError, memory_context

PIN = 'ef648e01899ba3e8dc6371642deaaf64b4477775'


def check(repo: Path) -> dict:
    if subprocess.check_output(['git', '-C', str(repo), 'rev-parse', 'HEAD'], text=True).strip() != PIN:
        raise ValueError('Pinned ECC checkout required')
    if subprocess.check_output(['git', '-C', str(repo), 'status', '--porcelain'], text=True):
        raise ValueError('Clean ECC checkout required')
    checks = []
    with tempfile.TemporaryDirectory(prefix='engineer-ecc-adapter-') as root:
        vault = Path(root) / 'project-vault'
        env = {'PATH': os.environ.get('PATH', ''), 'ECC_MEMORY_PROJECT_ROOT': str(vault),
               'ECC_MEMORY_USER_ROOT': str(Path(root) / 'user-vault'), 'ECC_MEMORY_HARNESS': 'codex'}
        for key in ('SYSTEMROOT', 'WINDIR', 'COMSPEC', 'PATHEXT'):
            if key in os.environ: env[key] = os.environ[key]
        def cli(args, body=None):
            result = subprocess.run(['node', str(repo / 'scripts/memory.js'), *args, '--json'],
                input=body, text=True, encoding='utf-8', capture_output=True, timeout=30, env=env, cwd=root)
            if result.returncode: raise RuntimeError('Synthetic CLI operation failed; output withheld')
            return json.loads(result.stdout)
        for target, title in (('all', 'adapter shared'), ('codex', 'adapter targeted'), ('claude', 'adapter foreign')):
            cli(['save', '--scope', 'project', '--title', title, '--target', target, '--stdin'],
                'Synthetic adapter checkpoint: status BLOCK, не проверено.')
        adapter = ECCCLITransport(repo, Path(root), vault=vault,
                                  harness='codex', scopes=('project',)).adapter()
        records = adapter.search('adapter')
        assert len(records) == 2
        checks.append({'name': 'real CLI search returns only shared/codex records', 'passed': True})
        assert all(r.text == 'Synthetic adapter checkpoint: status BLOCK, не проверено.' for r in records)
        checks.append({'name': 'full Cyrillic body preserved across search/read', 'passed': True})
        assert all(r['evidentiary_status'] == 'NOT_EVIDENCE' and r['trust'] == 'UNVERIFIED'
                   for r in memory_context(records))
        checks.append({'name': 'all recalled records remain non-evidentiary', 'passed': True})
        assert records == adapter.search('adapter')
        checks.append({'name': 'recall stable across fresh CLI subprocesses', 'passed': True})
        assert all(r.source_ref.endswith('sha256:' + hashlib.sha256(r.text.encode('utf-8')).hexdigest())
                   for r in records)
        checks.append({'name': 'context locators bind exact body digest', 'passed': True})
        files = list(vault.rglob('*.md'))
        assert files
        bad = files[0].parent / 'mem_bad_fixture.md'
        bad.write_text('Synthetic malformed ECC record', encoding='utf-8')
        try:
            adapter.search('adapter')
        except MemoryBoundaryError:
            checks.append({'name': 'malformed on-disk vault blocks whole recall', 'passed': True})
        else: raise AssertionError('Malformed vault did not block recall')
    return {'status': 'passed', 'ecc_commit': PIN, 'checks': checks,
            'platform': platform.platform(),
            'completed_at': datetime.now(timezone.utc).isoformat(),
            'node_version': subprocess.check_output(['node', '--version'], env=env, text=True).strip(),
            'boundary': 'Real local CLI with synthetic disposable data on the reported platform; not production or live app verification.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('ecc_checkout', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    result = check(args.ecc_checkout.resolve())
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('ADAPTER CLI CHECKS:', len(result['checks']))

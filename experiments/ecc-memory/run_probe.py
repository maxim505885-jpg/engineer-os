"""Reproduce a pinned ECC synthetic memory probe without installing a plugin."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ECC_COMMIT = 'ef648e01899ba3e8dc6371642deaaf64b4477775'


def run_json(command, cwd, env):
    result = subprocess.run(command, cwd=cwd, env=env, capture_output=True,
                            text=True, timeout=120, check=False)
    if result.returncode:
        raise RuntimeError('Probe failed; raw subprocess output withheld')
    return json.loads(result.stdout)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('ecc_checkout', type=Path)
    parser.add_argument('node_modules', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    repo = args.ecc_checkout.resolve()
    env = {'PATH': os.environ.get('PATH', ''), 'NODE_PATH': str(args.node_modules.resolve())}
    # Windows needs these OS variables to spawn processes; never forward credentials.
    for name in ('SYSTEMROOT', 'WINDIR', 'COMSPEC', 'PATHEXT'):
        if name in os.environ: env[name] = os.environ[name]
    head = subprocess.check_output(['git', '-C', str(repo), 'rev-parse', 'HEAD'], env=env, text=True).strip()
    dirty = subprocess.check_output(['git', '-C', str(repo), 'status', '--porcelain'], env=env, text=True)
    if head != ECC_COMMIT or dirty:
        raise ValueError('Use the pinned clean ECC checkout; probe executes upstream source')
    dependency = json.loads((args.node_modules / 'ajv' / 'package.json').read_text())
    if dependency['version'] != '8.20.0': raise ValueError('Ajv 8.20.0 required by this pinned experiment')
    evidence = run_json(['node', 'examples/unified-memory/evidence.test.cjs'], repo, env)
    conformance = run_json(['node', 'examples/unified-memory/conformance.cjs'], repo, env)
    monitor = run_json(['node', str(Path(__file__).with_name('check_context_monitor.cjs')), str(repo)], repo, env)
    boundary = run_json([sys.executable, str(Path(__file__).with_name('check_engineer_boundary.py'))], repo, env)
    if any(r.get('status') != 'passed' for r in (evidence, conformance, boundary, monitor)):
        raise ValueError('A probe did not pass')
    receipt = {'status': 'passed', 'ecc_commit': head, 'ajv_version': dependency['version'],
               'ajv_package_json_sha256': hashlib.sha256((args.node_modules / 'ajv' / 'package.json').read_bytes()).hexdigest(),
               'upstream_evidence': evidence, 'upstream_cli_mcp_conformance': conformance,
               'engineer_os_boundary': boundary, 'context_monitor': monitor,
               'context_monitor_source_sha256': hashlib.sha256((repo / 'scripts/hooks/ecc-context-monitor.js').read_bytes()).hexdigest(),
               'total_checks': evidence['checks'] + len(conformance['checks']) + len(boundary['checks']) + len(monitor['checks']),
               'limitations': ['Linux execution only; native Windows untested.',
                 'Codex/Claude/Hermes are synthetic MCP host labels, not live app integrations.',
                 'Ajv package manifest digest is recorded; this is not a dependency security audit.',
                 'No production memory backend, actual report data, LLM, OAuth, sync or acceptance RPC used.',
                 'No ECC data automatically enters ENGINEER OS or its Evidence Register.']}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
    print(f"CHECKS: {receipt['total_checks']}; REPORT: {args.output}")


if __name__ == '__main__': main()

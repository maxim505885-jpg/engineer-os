"""Explicit local ECC recall; prints non-evidentiary context, never acceptance."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from engineering.memory.ecc_cli_transport import ECCCLITransport
from engineering.memory.external_memory import MemoryBoundaryError, memory_context


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('ecc_checkout', type=Path)
    parser.add_argument('project', type=Path)
    parser.add_argument('query')
    parser.add_argument('--vault', type=Path)
    parser.add_argument('--harness', default='codex')
    args = parser.parse_args()
    try:
        transport = ECCCLITransport(args.ecc_checkout, args.project, vault=args.vault, harness=args.harness)
        context = memory_context(transport.adapter().search(args.query))
    except (ValueError, MemoryBoundaryError):
        print('BLOCK: ECC recall configuration or data check failed.', file=sys.stderr)
        return 2
    print(json.dumps({'evidentiary_status': 'NOT_EVIDENCE', 'records': context}, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__': raise SystemExit(main())

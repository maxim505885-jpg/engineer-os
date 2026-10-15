"""Optional local engineering tools. JSON output is a candidate, never acceptance."""
import argparse
from dataclasses import fields
import json
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    commands=parser.add_subparsers(dest='command',required=True)
    for name in ('ifc','ifc-diff','dxf-diff'):
        child=commands.add_parser(name)
        child.add_argument('source',type=Path)
        child.add_argument('--sha256',required=True)
        if name.endswith('diff'):child.add_argument('output',type=Path)
    beam=commands.add_parser('beam');beam.add_argument('input',type=Path)
    args=parser.parse_args()
    try:
        if args.command=='ifc':
            from engineering.bim.ifc_adapter import inspect_ifc
            result=inspect_ifc(args.source,expected_sha256=args.sha256)
        elif args.command=='ifc-diff':
            from engineering.bim.ifc_adapter import compare_ifc
            result=compare_ifc(args.source,args.output,source_sha256=args.sha256)
        elif args.command=='dxf-diff':
            from engineering.cad.roundtrip import compare_dxf
            result=compare_dxf(args.source,args.output,source_sha256=args.sha256)
        else:
            from engineering.calculation.control_beam import BeamInput,calculate_beam
            if args.input.stat().st_size>65536:raise ValueError('bounded input required')
            data=json.loads(args.input.read_text(encoding='utf-8'))
            if not isinstance(data,dict) or set(data)!={f.name for f in fields(BeamInput)}:
                raise ValueError('exact input fields required')
            if not isinstance(data['evidence_ids'],list):raise ValueError('evidence list required')
            data['evidence_ids']=tuple(data['evidence_ids'])
            result=calculate_beam(BeamInput(**data))
    except Exception:
        result=dict(status='BLOCK',reasons=['ENGINEERING_TOOL_INPUT_OR_EXECUTION_FAILED'],acceptance_granted=False)
    print(json.dumps(result,ensure_ascii=True,allow_nan=False))
    return 2 if result['status']=='BLOCK' else 0


if __name__=='__main__':raise SystemExit(main())

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
    for name in ('ifc','ifc-diff','dxf-diff','ifc-geometry','ifc-requirements','dwg-convert'):
        child=commands.add_parser(name)
        child.add_argument('source',type=Path)
        child.add_argument('--sha256',required=True)
        if name.endswith('diff'):child.add_argument('output',type=Path)
        if name=='ifc-requirements':child.add_argument('--rules',required=True,type=Path)
        if name=='dwg-convert':
            child.add_argument('--converter',required=True,type=Path)
            child.add_argument('--destination',required=True,type=Path)
    for name in ('beam','planar','rectangle'):
        child=commands.add_parser(name);child.add_argument('input',type=Path)
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
        elif args.command=='ifc-geometry':
            from engineering.bim.ifc_geometry import inspect_geometry
            result=inspect_geometry(args.source,expected_sha256=args.sha256)
        elif args.command=='ifc-requirements':
            from engineering.bim.ifc_requirements import check_requirements
            if args.rules.stat().st_size>65536:raise ValueError('bounded requirements required')
            rules=json.loads(args.rules.read_text(encoding='utf-8'))
            result=check_requirements(args.source,expected_sha256=args.sha256,requirements=rules)
        elif args.command=='dwg-convert':
            from engineering.cad.conversion import convert_dwg
            result=convert_dwg(args.source,args.destination,converter=args.converter,source_sha256=args.sha256)
        else:
            if args.input.stat().st_size>65536:raise ValueError('bounded input required')
            data=json.loads(args.input.read_text(encoding='utf-8'))
            if not isinstance(data,dict) or not isinstance(data.get('evidence_ids'),list):
                raise ValueError('typed fields and evidence list required')
            data['evidence_ids']=tuple(data['evidence_ids'])
            if args.command=='planar':
                from engineering.calculation.planar_control import PlanarInput,Node,Member,calculate_planar
                if not all(isinstance(data.get(k),list) for k in ('nodes','members','loads')):
                    raise ValueError('node/member/load lists required')
                data['nodes']=tuple(Node(**n) for n in data['nodes'])
                data['members']=tuple(Member(**m) for m in data['members'])
                data['loads']=tuple(tuple(load) for load in data['loads'])
                result=calculate_planar(PlanarInput(**data))
            elif args.command=='rectangle':
                from engineering.calculation.section_control import RectangleInput,calculate_rectangle
                result=calculate_rectangle(RectangleInput(**data))
            else:
                from engineering.calculation.control_beam import BeamInput,calculate_beam
                if set(data)!={f.name for f in fields(BeamInput)}:raise ValueError('exact beam fields required')
                result=calculate_beam(BeamInput(**data))
    except Exception:
        result=dict(status='BLOCK',reasons=['ENGINEERING_TOOL_INPUT_OR_EXECUTION_FAILED'],acceptance_granted=False)
    print(json.dumps(result,ensure_ascii=True,allow_nan=False))
    return 2 if result['status']=='BLOCK' else 0


if __name__=='__main__':raise SystemExit(main())

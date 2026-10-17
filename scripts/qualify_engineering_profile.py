"""Explicit offline synthetic probes. No installs, model downloads or acceptance."""
import argparse
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from engineering.local_app.capability_receipts import capability_report,probe_capability
from engineering.local_app.build_identity import BuildIdentity


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile',choices=('native','engineering'),default='engineering')
    parser.add_argument('--probe',action='store_true')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    report=capability_report(args.profile)
    report.update(created_at=datetime.now(timezone.utc).isoformat(),
        build=BuildIdentity(ROOT,profile=args.profile,discover_git=True).report(),
        receipt_authority='NONE_DIAGNOSTIC_ONLY',portable=False)
    if args.probe:
        for name,value in report['capabilities'].items():
            value.update(probe_capability(name))
        report['status']='PASS' if all(x['ready'] for x in report['capabilities'].values()) else 'UNCERTAINTY'
    # An existing target must be a regular file; never follow a link or overwrite
    # a source. Only the fixed diagnostic filename is allowed.
    target=args.output.absolute()
    if target.name!='capability-report.json' or target.is_symlink():parser.error('Output must be capability-report.json, without a symbolic link')
    target.parent.mkdir(parents=True,exist_ok=True)
    fd,temp=tempfile.mkstemp(prefix='profile-',suffix='.json',dir=target.parent)
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as stream:
            json.dump(report,stream,ensure_ascii=False,allow_nan=False,indent=2);stream.flush();os.fsync(stream.fileno())
        os.replace(temp,target)
    finally:
        if Path(temp).exists():Path(temp).unlink()
    print(json.dumps(dict(status=report['status'],acceptance_granted=False,
        capabilities={name:value['probe_status'] for name,value in report['capabilities'].items()},output=str(target))))


if __name__=='__main__':main()

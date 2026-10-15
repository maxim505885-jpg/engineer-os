"""Inventory a user source directory into a new report outside that directory."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from engineering.document_intelligence.corpus_audit import audit_corpus


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--expected-manifest',type=Path)
    args=parser.parse_args()
    if args.output.resolve().is_relative_to(args.source.resolve()) or args.output.exists():
        parser.error('choose a new report path outside the source directory')
    manifest=json.loads(args.expected_manifest.read_text(encoding='utf-8')) if args.expected_manifest else None
    report=audit_corpus(args.source,expected_manifest=manifest)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open('x',encoding='utf-8') as stream:
        json.dump(report,stream,ensure_ascii=False,indent=2)
    print(json.dumps({k:v for k,v in report.items() if k!='files'},ensure_ascii=True))
    return 2 if report['status']=='BLOCK' else 0


if __name__=='__main__':raise SystemExit(main())

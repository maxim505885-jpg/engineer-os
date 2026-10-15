from __future__ import annotations

import argparse
import json
from pathlib import Path

from engineering.local_app.final_audit import evaluate_offline_stage7

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("stage7_snapshot")
    ap.add_argument("--out")
    args=ap.parse_args()
    case=json.loads(Path(args.stage7_snapshot).read_text(encoding="utf-8"))
    result=evaluate_offline_stage7(case)
    text=json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True)
    if args.out:Path(args.out).write_text(text+"\n",encoding="utf-8")
    print(text)

if __name__=="__main__":
    main()

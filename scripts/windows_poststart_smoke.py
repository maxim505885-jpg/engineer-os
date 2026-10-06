from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import tempfile
from urllib.request import urlopen

def get_text(url: str, timeout: float = 5.0) -> str:
    with urlopen(url, timeout=timeout) as response:
        if not 200 <= response.status < 300:
            raise RuntimeError(f"HTTP {response.status}: {url}")
        return response.read().decode("utf-8", errors="replace")

def main(argv=None) -> int:
    p=argparse.ArgumentParser()
    p.add_argument("--app-url",required=True)
    p.add_argument("--ollama-url",required=True)
    p.add_argument("--model",required=True)
    p.add_argument("--data-dir",required=True)
    p.add_argument("--out",required=True)
    args=p.parse_args(argv)

    checks=[]
    failures=[]

    try:
        html=get_text(args.app_url)
        ok="ENGINEER OS" in html
        checks.append(dict(name="engineer_os_html",status="PASS" if ok else "BLOCK"))
        if not ok:failures.append("ENGINEER_OS_HTML_NOT_READY")
    except Exception as exc:
        checks.append(dict(name="engineer_os_html",status="BLOCK",error=str(exc)))
        failures.append("ENGINEER_OS_HTTP_FAILED")

    try:
        tags=json.loads(get_text(args.ollama_url.rstrip("/")+"/api/tags"))
        names=[str(x.get("name","")) for x in tags.get("models",[]) if isinstance(x,dict)]
        ok=args.model in names or any(x.startswith(args.model) for x in names)
        checks.append(dict(name="ollama_model",status="PASS" if ok else "BLOCK",models=names))
        if not ok:failures.append("OLLAMA_MODEL_MISSING")
    except Exception as exc:
        checks.append(dict(name="ollama_model",status="BLOCK",error=str(exc)))
        failures.append("OLLAMA_API_FAILED")

    data_dir=Path(args.data_dir).resolve()
    try:
        data_dir.mkdir(parents=True,exist_ok=True)
        fd,name=tempfile.mkstemp(prefix="stage9-write-",suffix=".tmp",dir=data_dir)
        Path(name).write_text("ENGINEER OS stage9 write probe",encoding="utf-8")
        Path(name).unlink(missing_ok=True)
        checks.append(dict(name="data_dir_write",status="PASS",path=str(data_dir)))
    except Exception as exc:
        checks.append(dict(name="data_dir_write",status="BLOCK",path=str(data_dir),error=str(exc)))
        failures.append("DATA_DIR_NOT_WRITABLE")

    result=dict(
        schema="ENGINEER_OS_WINDOWS_POSTSTART_V1",
        python=sys.version.split()[0],
        app_url=args.app_url,
        ollama_url=args.ollama_url,
        model=args.model,
        data_dir=str(data_dir),
        checks=checks,
        status="PASS" if not failures else "BLOCK",
        blocker_codes=failures,
    )
    out=Path(args.out)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False,sort_keys=True))
    return 0 if result["status"]=="PASS" else 2

if __name__=="__main__":
    raise SystemExit(main())

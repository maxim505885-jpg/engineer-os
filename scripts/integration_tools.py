"""Optional local tools. Run from any working directory; defaults do not execute agents."""
from __future__ import annotations

import argparse
import asyncio
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from engineering.integrations.browser_use_local import run_browser
from engineering.integrations.local_http import IntegrationError
from engineering.memory.agentmemory_http import AgentMemoryHTTPAdapter, resolve_secret
from engineering.memory.external_memory import MemoryBoundaryError, memory_context


def status() -> dict:
    lock = json.loads((ROOT / "integrations/upstreams.json").read_text(encoding="utf-8"))
    rows = []
    for item in lock["repositories"]:
        path = ROOT / item["path"]
        head = None
        if (path / ".git").exists():
            result = subprocess.run(["git", "-C", str(path), "rev-parse", "HEAD"],
                                    capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                head = result.stdout.strip()
        rows.append({"id": item["id"], "expected_commit": item["commit"],
                     "source_status": "PIN_VERIFIED" if head == item["commit"] else "NOT_READY",
                     "selected_paths": item["selected_paths"],
                     "runtime_status": "NOT_RUN"})
    return {"repositories": rows, "browser_package_installed":
            importlib.util.find_spec("browser_use") is not None,
            "acceptance_granted": False, "default_enabled": False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("status")
    memory = commands.add_parser("memory-recall")
    memory.add_argument("--enable", action="store_true")
    memory.add_argument("--url", default="http://127.0.0.1:3111")
    memory.add_argument("--project", required=True)
    memory.add_argument("--query", required=True)
    browser = commands.add_parser("browser-run")
    browser.add_argument("--enable", action="store_true")
    browser.add_argument("--task", required=True)
    browser.add_argument("--domain", action="append", required=True)
    browser.add_argument("--model", default="qwen3:8b")
    browser.add_argument("--ollama-url", default="http://127.0.0.1:11434")
    browser.add_argument("--max-steps", type=int, default=10)
    args = parser.parse_args()
    try:
        if args.command == "status":
            output = status()
        elif args.command == "memory-recall":
            adapter = AgentMemoryHTTPAdapter(args.url, args.project, enabled=args.enable,
                                            secret=resolve_secret(args.url, os.environ.get("AGENTMEMORY_SECRET")))
            output = {"context": memory_context(adapter.search(args.query)),
                      "acceptance_granted": False}
        else:
            output = asyncio.run(run_browser(args.task, enabled=args.enable, domains=args.domain,
                                            model=args.model, ollama_url=args.ollama_url,
                                            max_steps=args.max_steps))
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return 0
    except (IntegrationError, MemoryBoundaryError) as exc:
        print(json.dumps({"status": "BLOCK", "error": str(exc),
                          "acceptance_granted": False}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

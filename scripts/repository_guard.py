from __future__ import annotations

import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
FORBIDDEN_EXACT={".env"}
FORBIDDEN_PARTS=("client_secret","credentials.json","token.json","refresh_token")
ALLOWED_ENV={".env.example"}

def tracked_files()->list[str]:
    run=subprocess.run(["git","ls-files"],cwd=ROOT,text=True,capture_output=True,check=True)
    return [line.strip() for line in run.stdout.splitlines() if line.strip()]

def main()->int:
    errors=[]
    files=tracked_files()
    lowered={p:p.lower() for p in files}

    for path,low in lowered.items():
        name=Path(path).name.lower()
        if name in FORBIDDEN_EXACT and name not in ALLOWED_ENV:
            errors.append(f"tracked secret-like file: {path}")
        if name.startswith(".env.") and name != ".env.example":
            errors.append(f"tracked environment file: {path}")
        if any(part in low for part in FORBIDDEN_PARTS):
            errors.append(f"tracked credential-like path: {path}")

    required={
        ".github/CODEOWNERS",
        "SECURITY.md",
        ".github/dependabot.yml",
        ".github/workflows/core-tests.yml",
        ".github/workflows/repository-security.yml",
        ".github/workflows/repository-backup.yml",
    }
    for path in sorted(required-set(files)):
        errors.append(f"required repository protection file missing: {path}")

    codeowners=(ROOT/".github/CODEOWNERS").read_text(encoding="utf-8")
    if "@maxim505885-jpg" not in codeowners:
        errors.append("CODEOWNERS does not include repository owner")

    conflict_tokens=("<<<<<<< ","=======",">>>>>>> ")
    for path in files:
        if path=="scripts/repository_guard.py":
            continue
        p=ROOT/path
        if not p.is_file() or p.suffix.lower() in {".png",".jpg",".jpeg",".gif",".pdf",".doc",".docx",".xls",".xlsx",".lir",".zip"}:
            continue
        try:text=p.read_text(encoding="utf-8")
        except (UnicodeDecodeError,OSError):continue
        if all(token in text for token in conflict_tokens):
            errors.append(f"unresolved merge markers: {path}")

    if errors:
        print("REPOSITORY_GUARD=BLOCK")
        for item in errors:print("-",item)
        return 2
    print(f"REPOSITORY_GUARD=PASS tracked_files={len(files)}")
    return 0

if __name__=="__main__":
    raise SystemExit(main())

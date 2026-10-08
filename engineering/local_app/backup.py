"""Validated backup/restore for ENGINEER OS local application data."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import sqlite3
import tempfile
import time
import zipfile

from .lock import DataLock

SCHEMA="ENGINEER_OS_DATA_BACKUP_V1"
DATA_TABLES=(
    "sessions","messages","files","jobs","local_evidence","analysis_receipts",
    "analysis_contexts","extraction_pages","source_reviews","requirement_sets",
    "domain_packets","requirement_assessments","real_case_snapshots","final_audits",
)

class BackupError(RuntimeError):
    pass

def _sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

def _integrity(db_path: Path) -> None:
    try:
        with sqlite3.connect(db_path) as db:
            result=db.execute("PRAGMA integrity_check").fetchone()
            if not result or result[0]!="ok":
                raise BackupError("SQLite integrity_check failed")
            fk=list(db.execute("PRAGMA foreign_key_check"))
            if fk:
                raise BackupError("SQLite foreign_key_check failed")
    except sqlite3.DatabaseError as exc:
        raise BackupError("Backup SQLite database is invalid") from exc

def _counts(db_path: Path) -> dict[str,int]:
    with sqlite3.connect(db_path) as db:
        names={row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        missing=[name for name in DATA_TABLES if name not in names]
        if missing:
            raise BackupError("Backup database misses required tables: "+", ".join(missing))
        return {name:db.execute(f"SELECT count(*) FROM {name}").fetchone()[0] for name in DATA_TABLES}

def _safe_archive_name(name: str) -> bool:
    p=PurePosixPath(name)
    return bool(name) and not p.is_absolute() and ".." not in p.parts and "\\" not in name

def create_backup(source, archive) -> dict:
    source=Path(source).resolve()
    archive=Path(archive).resolve()
    db_path=source/"history.sqlite3"
    if not db_path.is_file():
        raise BackupError(f"ENGINEER OS data database not found: {db_path}")
    archive.parent.mkdir(parents=True,exist_ok=True)
    if archive.exists():
        raise BackupError(f"Backup already exists: {archive}")

    with DataLock(source):
        with tempfile.TemporaryDirectory(prefix="engineer-os-backup-") as tmp:
            stage=Path(tmp)
            snapshot=stage/"history.sqlite3"
            try:
                with sqlite3.connect(db_path) as src, sqlite3.connect(snapshot) as dst:
                    src.backup(dst)
            except sqlite3.DatabaseError as exc:
                raise BackupError("Cannot create SQLite snapshot") from exc
            _integrity(snapshot)
            counts=_counts(snapshot)

            files=[]
            with sqlite3.connect(snapshot) as db:
                db.row_factory=sqlite3.Row
                rows=list(db.execute("SELECT id,name,path,sha256,size FROM files ORDER BY id"))
            staged_files=stage/"files";staged_files.mkdir()
            seen=set()
            for row in rows:
                original=Path(row["path"]).resolve()
                if not original.is_file():
                    raise BackupError(f"Original file is missing: {row['name']}")
                actual_size=original.stat().st_size
                actual_sha=_sha256(original)
                if actual_size!=row["size"] or actual_sha!=row["sha256"]:
                    raise BackupError(f"Original identity mismatch: {row['name']}")
                suffix=original.suffix.lower()
                archive_name=f"files/{row['id']}{suffix}"
                if archive_name in seen:
                    raise BackupError("Duplicate backup file path")
                seen.add(archive_name)
                target=stage/archive_name
                shutil.copyfile(original,target)
                files.append(dict(
                    id=row["id"],name=row["name"],archive_path=archive_name,
                    sha256=actual_sha,size=actual_size,
                ))

            manifest=dict(
                schema=SCHEMA,
                created_at=time.time(),
                database=dict(
                    archive_path="history.sqlite3",
                    sha256=_sha256(snapshot),
                    size=snapshot.stat().st_size,
                    table_counts=counts,
                ),
                files=files,
                acceptance_note="Backup preserves records; restore never creates or upgrades acceptance.",
            )
            manifest_path=stage/"manifest.json"
            manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")

            try:
                with zipfile.ZipFile(archive,"x",compression=zipfile.ZIP_DEFLATED,allowZip64=True) as z:
                    z.write(manifest_path,"manifest.json")
                    z.write(snapshot,"history.sqlite3")
                    for item in files:
                        z.write(stage/item["archive_path"],item["archive_path"])
            except Exception:
                archive.unlink(missing_ok=True)
                raise

    result=validate_backup(archive)
    result["archive"]=str(archive)
    return result

def validate_backup(archive) -> dict:
    archive=Path(archive).resolve()
    if not archive.is_file():
        raise BackupError(f"Backup file not found: {archive}")
    try:
        with zipfile.ZipFile(archive,"r") as z:
            names=z.namelist()
            if len(names)!=len(set(names)) or any(not _safe_archive_name(name) for name in names):
                raise BackupError("Backup contains unsafe or duplicate paths")
            if "manifest.json" not in names or "history.sqlite3" not in names:
                raise BackupError("Backup manifest/database missing")
            try:
                manifest=json.loads(z.read("manifest.json").decode("utf-8"))
            except (UnicodeDecodeError,json.JSONDecodeError) as exc:
                raise BackupError("Backup manifest is invalid") from exc
            if manifest.get("schema")!=SCHEMA:
                raise BackupError("Unsupported backup schema")
            expected={"manifest.json","history.sqlite3"}|{item.get("archive_path") for item in manifest.get("files",[])}
            if None in expected or set(names)!=expected:
                raise BackupError("Backup file set does not match manifest")

            with tempfile.TemporaryDirectory(prefix="engineer-os-validate-") as tmp:
                root=Path(tmp)
                z.extractall(root)
                db_info=manifest.get("database") or {}
                db=root/"history.sqlite3"
                if db.stat().st_size!=db_info.get("size") or _sha256(db)!=db_info.get("sha256"):
                    raise BackupError("Backup database checksum mismatch")
                _integrity(db)
                counts=_counts(db)
                if counts!=db_info.get("table_counts"):
                    raise BackupError("Backup database table counts changed")
                by_id={}
                for item in manifest.get("files",[]):
                    if not isinstance(item,dict) or not isinstance(item.get("id"),str):
                        raise BackupError("Invalid file manifest entry")
                    if item["id"] in by_id:
                        raise BackupError("Duplicate file id in manifest")
                    path=root/item["archive_path"]
                    if not path.is_file() or path.stat().st_size!=item.get("size") or _sha256(path)!=item.get("sha256"):
                        raise BackupError("Backup original checksum mismatch")
                    by_id[item["id"]]=item
                with sqlite3.connect(db) as check:
                    rows=list(check.execute("SELECT id,sha256,size FROM files"))
                if {row[0] for row in rows}!=set(by_id):
                    raise BackupError("Database originals do not match manifest")
                for fid,sha,size in rows:
                    item=by_id[fid]
                    if sha!=item["sha256"] or size!=item["size"]:
                        raise BackupError("Database original identity does not match manifest")
    except zipfile.BadZipFile as exc:
        raise BackupError("Backup archive is not a valid ZIP") from exc
    return dict(
        schema=SCHEMA,status="PASS",archive=str(archive),
        database_sha256=manifest["database"]["sha256"],
        table_counts=manifest["database"]["table_counts"],
        originals=len(manifest["files"]),
    )

def restore_backup(archive, target) -> dict:
    archive=Path(archive).resolve()
    target=Path(target).resolve()
    validation=validate_backup(archive)

    if target.exists() and any(target.iterdir()):
        raise BackupError("Restore target must be missing or empty; existing data is never overwritten")
    target.parent.mkdir(parents=True,exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="engineer-os-restore-",dir=target.parent) as tmp:
        stage=Path(tmp)/"data";stage.mkdir()
        with zipfile.ZipFile(archive,"r") as z:
            manifest=json.loads(z.read("manifest.json").decode("utf-8"))
            z.extract("history.sqlite3",stage)
            (stage/"files").mkdir()
            for item in manifest["files"]:
                source=item["archive_path"]
                suffix=Path(source).suffix.lower()
                dest=stage/"files"/f"{item['id']}{suffix}"
                with z.open(source) as src,dest.open("wb") as dst:
                    shutil.copyfileobj(src,dst)
                if dest.stat().st_size!=item["size"] or _sha256(dest)!=item["sha256"]:
                    raise BackupError("Restored original identity mismatch")

        db_path=stage/"history.sqlite3"
        with sqlite3.connect(db_path) as db:
            db.execute("PRAGMA foreign_keys=ON")
            for item in manifest["files"]:
                suffix=Path(item["archive_path"]).suffix.lower()
                final_path=target/"files"/f"{item['id']}{suffix}"
                if db.execute("UPDATE files SET path=? WHERE id=?",(str(final_path),item["id"])).rowcount!=1:
                    raise BackupError("Cannot rebind restored original path")
            db.commit()
        _integrity(db_path)

        # Validate the rewritten DB against the restored file identities.
        with sqlite3.connect(db_path) as db:
            db.row_factory=sqlite3.Row
            rows=list(db.execute("SELECT id,path,sha256,size FROM files"))
        for row in rows:
            local=stage/"files"/Path(row["path"]).name
            if not local.is_file() or local.stat().st_size!=row["size"] or _sha256(local)!=row["sha256"]:
                raise BackupError("Restored database/file binding failed")

        if target.exists():
            target.rmdir()
        shutil.move(str(stage),str(target))

    # Prove the final target is structurally sound and independently lockable.
    with DataLock(target):
        _integrity(target/"history.sqlite3")
        counts=_counts(target/"history.sqlite3")
    return dict(
        schema=SCHEMA,status="PASS",target=str(target),
        table_counts=counts,originals=validation["originals"],
        acceptance_note="Restore preserved stored audit records without creating new acceptance.",
    )

def main(argv=None) -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest="command",required=True)
    p=sub.add_parser("backup");p.add_argument("--source",required=True);p.add_argument("--out",required=True)
    p=sub.add_parser("validate");p.add_argument("--archive",required=True)
    p=sub.add_parser("restore");p.add_argument("--archive",required=True);p.add_argument("--target",required=True)
    args=parser.parse_args(argv)
    try:
        if args.command=="backup": result=create_backup(args.source,args.out)
        elif args.command=="validate": result=validate_backup(args.archive)
        else: result=restore_backup(args.archive,args.target)
        print(json.dumps(result,ensure_ascii=False,sort_keys=True))
        return 0
    except (BackupError,RuntimeError,OSError,sqlite3.Error) as exc:
        print(json.dumps(dict(schema=SCHEMA,status="BLOCK",error=str(exc)),ensure_ascii=False,sort_keys=True))
        return 2

if __name__=="__main__":
    raise SystemExit(main())

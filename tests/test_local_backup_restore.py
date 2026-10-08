import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
import unittest
import uuid
from unittest import mock
import zipfile

from engineering.local_app.backup import BackupError,create_backup,restore_backup,validate_backup
from engineering.local_app.files import _atomic_write_original,preserve_file
from engineering.local_app.lock import DataLock
from engineering.local_app.store import Store


class LocalDataBackupRestoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)/"source"
        self.store=Store(self.root)

    def tearDown(self):
        self.tmp.cleanup()

    def seed_full_state(self):
        session=self.store.create_session("Reliability case")
        original=preserve_file(self.store,session["id"],"исходник.txt",b"height 4m")
        now=time.time()
        job=str(uuid.uuid4())
        evidence=str(uuid.uuid4())
        review=str(uuid.uuid4())
        reqset=str(uuid.uuid4())
        domain=str(uuid.uuid4())
        case=str(uuid.uuid4())
        audit=str(uuid.uuid4())
        with self.store.connection() as db:
            db.execute(
                "INSERT INTO jobs(id,session_id,prompt,file_ids,state,result,error,created,updated,parent_id,mode,requested_checks) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                (job,session["id"],"Reliability",json.dumps([original["id"]]),"SUCCEEDED",
                 json.dumps({"engineering_status":"BLOCK","acceptance_granted":False}),None,now,now,None,"CORE_RUN",json.dumps(["report"]))
            )
            db.execute("INSERT INTO messages(session_id,role,content,created) VALUES(?,?,?,?)",(session["id"],"user","Reliability",now))
            db.execute("INSERT INTO local_evidence VALUES(?,?,?,?,?)",(evidence,session["id"],original["id"],json.dumps({"id":evidence,"status":"UNVERIFIED","acceptance_granted":False}),now))
            db.execute("INSERT INTO analysis_receipts(job_id,record) VALUES(?,?)",(job,json.dumps({"status":"COMPLETED","acceptance_granted":False})))
            db.execute("INSERT INTO analysis_contexts VALUES(?,?,?)",(job,"report",json.dumps([{"role":"user","content":"x"}])))
            db.execute("INSERT INTO extraction_pages VALUES(?,?,?)",(job,1,json.dumps({"page":1,"execution":"COMPLETED","status":"UNCERTAINTY","blocks":[]})))
            db.execute("INSERT INTO source_reviews VALUES(?,?,?,?,?,?)",(review,evidence,session["id"],1,json.dumps({"id":review,"decision":"SOURCE_CONFIRMED","acceptance_granted":False}),now))
            db.execute("INSERT INTO requirement_sets VALUES(?,?,?,?)",(reqset,session["id"],json.dumps({"id":reqset,"requirements":[{"id":"R1"}]}),now))
            db.execute("INSERT INTO domain_packets VALUES(?,?,?,?)",(domain,session["id"],1,json.dumps({"id":domain,"status":"BLOCK","acceptance_granted":False})))
            db.execute("INSERT INTO requirement_assessments VALUES(?,?,?,?,?)",(str(uuid.uuid4()),reqset,"R1",1,json.dumps({"status":"UNCERTAINTY","acceptance_granted":False})))
            db.execute("INSERT INTO real_case_snapshots VALUES(?,?,?,?,?,?)",(case,session["id"],job,1,json.dumps({"id":case,"engineering_status":"BLOCK","acceptance_granted":False}),now))
            db.execute("INSERT INTO final_audits VALUES(?,?,?,?,?,?)",(audit,session["id"],case,1,json.dumps({"id":audit,"decision":"BLOCK","effective_acceptance_granted":False,"acceptance_granted":False}),now))
        return session,original

    def test_full_state_backup_restore_rebinds_paths_and_preserves_fail_closed_data(self):
        session,original=self.seed_full_state()
        archive=Path(self.tmp.name)/"backup.zip"
        created=create_backup(self.root,archive)
        self.assertEqual(created["status"],"PASS")
        self.assertEqual(created["originals"],1)

        target=Path(self.tmp.name)/"restored"
        restored=restore_backup(archive,target)
        self.assertEqual(restored["status"],"PASS")
        self.assertEqual(restored["table_counts"]["final_audits"],1)

        restored_store=Store(target)
        snap=restored_store.snapshot(session["id"])
        self.assertEqual(len(snap["files"]),1)
        private=restored_store.get_file(original["id"])
        self.assertEqual(Path(private["path"]).parent,target/"files")
        self.assertEqual(Path(private["path"]).read_bytes(),b"height 4m")
        with restored_store.connection() as db:
            audit=json.loads(db.execute("SELECT record FROM final_audits").fetchone()[0])
        self.assertFalse(audit["acceptance_granted"])
        self.assertFalse(audit["effective_acceptance_granted"])

    def test_backup_refuses_active_data_directory(self):
        self.seed_full_state()
        with DataLock(self.root):
            with self.assertRaises(RuntimeError):
                create_backup(self.root,Path(self.tmp.name)/"active.zip")

    def test_restore_refuses_nonempty_target(self):
        self.seed_full_state()
        archive=Path(self.tmp.name)/"backup.zip"
        create_backup(self.root,archive)
        target=Path(self.tmp.name)/"occupied";target.mkdir();(target/"keep.txt").write_text("keep")
        with self.assertRaises(BackupError):
            restore_backup(archive,target)
        self.assertEqual((target/"keep.txt").read_text(),"keep")

    def test_tampered_backup_is_blocked_before_restore(self):
        self.seed_full_state()
        archive=Path(self.tmp.name)/"backup.zip"
        create_backup(self.root,archive)
        tampered=Path(self.tmp.name)/"tampered.zip"
        with zipfile.ZipFile(archive,"r") as src,zipfile.ZipFile(tampered,"w",zipfile.ZIP_DEFLATED) as dst:
            for name in src.namelist():
                data=src.read(name)
                if name.startswith("files/"):data=b"tampered"
                dst.writestr(name,data)
        with self.assertRaises(BackupError):
            validate_backup(tampered)
        target=Path(self.tmp.name)/"never-created"
        with self.assertRaises(BackupError):
            restore_backup(tampered,target)
        self.assertFalse(target.exists())

    def test_interrupted_running_job_is_failed_on_restart_without_acceptance(self):
        session=self.store.create_session("Crash")
        job=self.store.enqueue(session["id"],"Crash test",[])
        with self.store.connection() as db:
            db.execute("UPDATE jobs SET state='RUNNING',result=? WHERE id=?",(json.dumps({"text":"partial","acceptance_granted":False}),job["id"]))
        restarted=Store(self.root)
        restarted.interrupt_running()
        state=restarted.snapshot(session["id"])["jobs"][0]
        self.assertEqual(state["state"],"FAILED")
        self.assertFalse(state["result"]["acceptance_granted"])
        self.assertIn("interrupted",state["error"].lower())

    def test_atomic_original_write_removes_partial_file_on_replace_failure(self):
        target=Path(self.tmp.name)/"atomic.bin"
        with mock.patch("engineering.local_app.files.os.replace",side_effect=OSError("disk failure")):
            with self.assertRaises(OSError):
                _atomic_write_original(target,b"payload")
        self.assertFalse(target.exists())
        self.assertEqual(list(target.parent.glob(target.name+".partial-*")),[])

    def test_legacy_schema_gets_pre_migration_snapshot(self):
        legacy=Path(self.tmp.name)/"legacy";legacy.mkdir()
        db_path=legacy/"history.sqlite3"
        with sqlite3.connect(db_path) as db:
            db.executescript("""
            CREATE TABLE sessions(id TEXT PRIMARY KEY,title TEXT NOT NULL,created REAL NOT NULL);
            CREATE TABLE messages(seq INTEGER PRIMARY KEY AUTOINCREMENT,session_id TEXT NOT NULL,role TEXT NOT NULL,content TEXT NOT NULL,created REAL NOT NULL);
            CREATE TABLE files(id TEXT PRIMARY KEY,session_id TEXT NOT NULL,name TEXT NOT NULL,path TEXT NOT NULL,sha256 TEXT NOT NULL,size INTEGER NOT NULL,text TEXT NOT NULL,extraction_status TEXT NOT NULL,extraction_note TEXT NOT NULL,text_truncated INTEGER NOT NULL,created REAL NOT NULL);
            CREATE TABLE jobs(id TEXT PRIMARY KEY,session_id TEXT NOT NULL,prompt TEXT NOT NULL,file_ids TEXT NOT NULL,state TEXT NOT NULL,result TEXT,error TEXT,created REAL NOT NULL,updated REAL NOT NULL);
            """)
        Store(legacy)
        snapshots=list((legacy/"pre-migration").glob("history-*.sqlite3"))
        self.assertEqual(len(snapshots),1)
        with sqlite3.connect(snapshots[0]) as db:
            names={r[1] for r in db.execute("PRAGMA table_info(jobs)")}
        self.assertNotIn("mode",names)
        with sqlite3.connect(db_path) as db:
            names={r[1] for r in db.execute("PRAGMA table_info(jobs)")}
        self.assertIn("mode",names)

    def test_stale_lock_file_and_crashed_owner_are_recoverable(self):
        lock_root=Path(self.tmp.name)/"lock-crash"
        marker=Path(self.tmp.name)/"locked.marker"
        code=(
            "import time;from pathlib import Path;"
            "from engineering.local_app.lock import DataLock;"
            + "root=Path(r'"+lock_root.as_posix()+"');marker=Path(r'"+marker.as_posix()+"');"
            + "ctx=DataLock(root);ctx.__enter__();marker.write_text('locked');time.sleep(60)"
        )
        child=subprocess.Popen([sys.executable,"-c",code],cwd=Path(__file__).resolve().parents[1])
        try:
            deadline=time.time()+5
            while not marker.exists() and time.time()<deadline:
                time.sleep(.05)
            self.assertTrue(marker.exists(),"child did not acquire data lock")
            with self.assertRaises(RuntimeError):
                with DataLock(lock_root):
                    pass
        finally:
            child.kill();child.wait(timeout=5)
        self.assertTrue((lock_root/"app.lock").exists(),"lock file is intentionally persistent")
        with DataLock(lock_root):
            pass

    def test_launcher_can_restart_after_forced_process_exit(self):
        data=Path(self.tmp.name)/"launcher-data"
        root=Path(__file__).resolve().parents[1]
        def start():
            return subprocess.Popen(
                [sys.executable,"scripts/run_local_app.py","--no-browser","--port","0","--data-dir",str(data)],
                cwd=root,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,
            )
        first=start()
        try:
            line=""
            deadline=time.time()+10
            while time.time()<deadline:
                current=first.stdout.readline()
                if current:
                    line+=current
                    if "ENGINEER OS: http://127.0.0.1:" in line:
                        break
                elif first.poll() is not None:
                    break
            self.assertIn("ENGINEER OS: http://127.0.0.1:",line)
        finally:
            first.kill();first.wait(timeout=5)
        second=start()
        try:
            line=""
            deadline=time.time()+10
            while time.time()<deadline:
                current=second.stdout.readline()
                if current:
                    line+=current
                    if "ENGINEER OS: http://127.0.0.1:" in line:
                        break
                elif second.poll() is not None:
                    break
            self.assertIn("ENGINEER OS: http://127.0.0.1:",line)
        finally:
            second.kill();second.wait(timeout=5)


if __name__=="__main__":
    unittest.main()

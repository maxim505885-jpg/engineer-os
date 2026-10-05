"""Transactional, disk-backed conversations and single-claim jobs."""
from contextlib import contextmanager
import json
from pathlib import Path
import sqlite3
import time
import uuid


def identifier(value):
    if not isinstance(value,str):raise ValueError('Invalid identifier')
    try:valid=str(uuid.UUID(value))==value
    except ValueError:valid=False
    if not valid:raise ValueError('Invalid identifier')
    return value


class Store:
    def __init__(self,root):
        self.root=Path(root).resolve();self.root.mkdir(parents=True,exist_ok=True)
        self.path=self.root/'history.sqlite3'
        with self.connection() as db:
            db.executescript('''
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS sessions(id TEXT PRIMARY KEY,title TEXT NOT NULL,created REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS messages(seq INTEGER PRIMARY KEY AUTOINCREMENT,session_id TEXT NOT NULL REFERENCES sessions(id),role TEXT NOT NULL,content TEXT NOT NULL,created REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS files(id TEXT PRIMARY KEY,session_id TEXT NOT NULL REFERENCES sessions(id),name TEXT NOT NULL,path TEXT NOT NULL,sha256 TEXT NOT NULL,size INTEGER NOT NULL,text TEXT NOT NULL,extraction_status TEXT NOT NULL,extraction_note TEXT NOT NULL,text_truncated INTEGER NOT NULL,created REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS jobs(id TEXT PRIMARY KEY,session_id TEXT NOT NULL REFERENCES sessions(id),prompt TEXT NOT NULL,file_ids TEXT NOT NULL,state TEXT NOT NULL,result TEXT,error TEXT,created REAL NOT NULL,updated REAL NOT NULL);
            CREATE UNIQUE INDEX IF NOT EXISTS one_active_job ON jobs(session_id) WHERE state IN ('QUEUED','RUNNING');
            ''')

    @contextmanager
    def connection(self):
        db=sqlite3.connect(self.path,timeout=10);db.row_factory=sqlite3.Row
        db.execute('PRAGMA foreign_keys=ON')
        try:
            with db:yield db
        finally:db.close()

    def create_session(self,title='Новый диалог'):
        if not isinstance(title,str) or not title.strip() or len(title)>120:raise ValueError('Title must contain 1–120 characters')
        record=dict(id=str(uuid.uuid4()),title=title.strip(),created=time.time())
        with self.connection() as db:db.execute('INSERT INTO sessions VALUES(:id,:title,:created)',record)
        return record

    def sessions(self):
        with self.connection() as db:return [dict(r) for r in db.execute('SELECT * FROM sessions ORDER BY created DESC LIMIT 500')]

    def snapshot(self,session_id):
        identifier(session_id)
        with self.connection() as db:
            session=db.execute('SELECT * FROM sessions WHERE id=?',(session_id,)).fetchone()
            if session is None:raise ValueError('Conversation not found')
            messages=[dict(r) for r in db.execute('SELECT * FROM (SELECT * FROM messages WHERE session_id=? ORDER BY seq DESC LIMIT 200) ORDER BY seq',(session_id,))]
            jobs=[self.job_dict(r) for r in db.execute('SELECT * FROM jobs WHERE session_id=? ORDER BY created DESC LIMIT 200',(session_id,))]
            files=[self.file_dict(r) for r in db.execute('SELECT * FROM files WHERE session_id=? ORDER BY created LIMIT 200',(session_id,))]
            count=db.execute('SELECT count(*) FROM messages WHERE session_id=?',(session_id,)).fetchone()[0]
        return dict(session=dict(session),messages=messages,jobs=jobs,files=files,history_windowed=count>len(messages),message_count=count)

    @staticmethod
    def file_dict(row,private=False):
        r=dict(row);r['text_truncated']=bool(r['text_truncated']);r['acceptance_granted']=False
        if not private:
            r.pop('path');r.pop('text')
        return r

    @staticmethod
    def job_dict(row):
        r=dict(row);r['file_ids']=json.loads(r['file_ids']);r['result']=json.loads(r['result']) if r['result'] else None
        return r

    def get_file(self,file_id):
        identifier(file_id)
        with self.connection() as db:r=db.execute('SELECT * FROM files WHERE id=?',(file_id,)).fetchone()
        if r is None:raise ValueError('File not found')
        return self.file_dict(r,private=True)

    def add_file(self,record):
        with self.connection() as db:
            db.execute('BEGIN IMMEDIATE')
            if db.execute('SELECT id FROM sessions WHERE id=?',(record['session_id'],)).fetchone() is None:raise ValueError('Conversation not found')
            if db.execute('SELECT count(*) FROM files WHERE session_id=?',(record['session_id'],)).fetchone()[0]>=200:
                raise ValueError('Conversation attachment limit: 200 files; create another conversation')
            db.execute('INSERT INTO files VALUES(:id,:session_id,:name,:path,:sha256,:size,:text,:extraction_status,:extraction_note,:text_truncated,:created)',record)
        return self.file_dict(record)

    def enqueue(self,session_id,prompt,file_ids):
        identifier(session_id)
        if not isinstance(prompt,str) or not prompt.strip() or len(prompt)>8000:raise ValueError('Message must contain 1–8000 characters')
        if not isinstance(file_ids,list) or len(file_ids)>20 or any(not isinstance(x,str) for x in file_ids) or len(set(file_ids))!=len(file_ids):raise ValueError('Select up to 20 distinct files')
        for value in file_ids:identifier(value)
        now=time.time();record=dict(id=str(uuid.uuid4()),session_id=session_id,prompt=prompt.strip(),file_ids=json.dumps(file_ids),state='QUEUED',result=None,error=None,created=now,updated=now)
        try:
            with self.connection() as db:
                db.execute('BEGIN IMMEDIATE')
                if db.execute('SELECT id FROM sessions WHERE id=?',(session_id,)).fetchone() is None:raise ValueError('Conversation not found')
                for fid in file_ids:
                    if db.execute('SELECT id FROM files WHERE id=? AND session_id=?',(fid,session_id)).fetchone() is None:raise ValueError('Attachment belongs to another conversation or does not exist')
                db.execute('INSERT INTO jobs VALUES(:id,:session_id,:prompt,:file_ids,:state,:result,:error,:created,:updated)',record)
                db.execute('INSERT INTO messages(session_id,role,content,created) VALUES(?,?,?,?)',(session_id,'user',record['prompt'],now))
                db.execute("UPDATE sessions SET title=? WHERE id=? AND title='Новый диалог'",(record['prompt'][:60],session_id))
        except sqlite3.IntegrityError:raise ValueError('This conversation already has an active task') from None
        return self.job_dict(record)

    def claim(self):
        with self.connection() as db:
            db.execute('BEGIN IMMEDIATE')
            r=db.execute("SELECT * FROM jobs WHERE state='QUEUED' ORDER BY created LIMIT 1").fetchone()
            if r is None:return None
            db.execute("UPDATE jobs SET state='RUNNING',updated=? WHERE id=?",(time.time(),r['id']))
            return self.job_dict(dict(r,state='RUNNING'))

    def finish(self,job_id,result):
        identifier(job_id)
        if not isinstance(result,dict) or not isinstance(result.get('text'),str) or not result['text'].strip():raise ValueError('Nonempty model response required')
        result=dict(result,engineering_status='UNCERTAINTY',evidentiary_status='NOT_EVIDENCE',acceptance_granted=False,final_audit='NOT_RUN')
        with self.connection() as db:
            db.execute('BEGIN IMMEDIATE')
            r=db.execute("SELECT * FROM jobs WHERE id=? AND state='RUNNING'",(job_id,)).fetchone()
            if r is None:raise ValueError('Task is not running')
            now=time.time();db.execute("UPDATE jobs SET state='SUCCEEDED',result=?,updated=? WHERE id=?",(json.dumps(result,ensure_ascii=False),now,job_id))
            db.execute('INSERT INTO messages(session_id,role,content,created) VALUES(?,?,?,?)',(r['session_id'],'assistant',result['text'],now))

    def fail(self,job_id,error):
        identifier(job_id)
        with self.connection() as db:db.execute("UPDATE jobs SET state='FAILED',error=?,updated=? WHERE id=? AND state='RUNNING'",(str(error)[:500],time.time(),job_id))

    def interrupt_running(self):
        # The caller must own the exclusive data-directory lock.
        with self.connection() as db:db.execute("UPDATE jobs SET state='FAILED',error='Execution interrupted; submit again to retry.',updated=? WHERE state='RUNNING'",(time.time(),))

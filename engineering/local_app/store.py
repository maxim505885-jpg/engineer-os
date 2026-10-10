"""Transactional, disk-backed conversations and single-claim jobs."""
from contextlib import contextmanager
import json
import hashlib
import os
import tempfile
from pathlib import Path
import sqlite3
import time
import uuid
from .coverage import unknown_coverage
from .lock import managed_file,managed_database


def identifier(value):
    if not isinstance(value,str):raise ValueError('Invalid identifier')
    try:valid=str(uuid.UUID(value))==value
    except ValueError:valid=False
    if not valid:raise ValueError('Invalid identifier')
    return value


class ReviewConflict(ValueError):
    pass


def _migration_backup(db,root):
    target=root/'history.pre-migration-v0.sqlite3'
    managed_file(target)
    def verify(path):
        managed_database(path)
        saved=sqlite3.connect(path)
        try:
            if saved.execute('PRAGMA integrity_check').fetchone()[0]!='ok' or saved.execute('PRAGMA user_version').fetchone()[0]!=0:
                raise ValueError('Invalid migration recovery copy')
            # A structurally valid empty or older unrelated database is not a
            # recovery copy of the data that is about to be migrated.
            def digest_dump(connection):
                digest=hashlib.sha256()
                for line in connection.iterdump():digest.update(line.encode('utf-8'));digest.update(b'\n')
                return digest.digest()
            if digest_dump(saved)!=digest_dump(db):raise ValueError('Migration recovery copy does not match current data')
        finally:saved.close()
    if target.exists():verify(target);return
    fd,name=tempfile.mkstemp(prefix='migration-',suffix='.sqlite3',dir=root);os.close(fd)
    temporary=Path(name)
    try:
        saved=sqlite3.connect(temporary)
        try:db.backup(saved)
        finally:saved.close()
        verify(temporary)
        os.link(temporary,target)
    finally:temporary.unlink(missing_ok=True)


class Store:
    def verification_key(self):
        """Read a provisioned local issuer key; never mint authority on audit.

        The current app has no verification issuer/provisioning HTTP endpoint.
        A missing, malformed or symlinked key fails closed. Backup must preserve
        this key together with verification records once an issuer is added.
        """
        path=self.root/'engineering-verification.key'
        try:
            managed_file(path)
            with path.open('rb') as stream:key=stream.read(33)
            return key if len(key)==32 else None
        except (OSError,ValueError):return None

    def __init__(self,root):
        self.root=Path(root).resolve();self.root.mkdir(parents=True,exist_ok=True)
        self.path=self.root/'history.sqlite3'
        existed=self.path.exists()
        with self.connection() as db:
            version=db.execute('PRAGMA user_version').fetchone()[0]
            if version>1:raise RuntimeError('Database is from a newer ENGINEER OS version; use the matching application')
            if existed and version==0:
                _migration_backup(db,self.root)
            db.executescript('''
            PRAGMA journal_mode=WAL;
            BEGIN IMMEDIATE;
            CREATE TABLE IF NOT EXISTS sessions(id TEXT PRIMARY KEY,title TEXT NOT NULL,created REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS messages(seq INTEGER PRIMARY KEY AUTOINCREMENT,session_id TEXT NOT NULL REFERENCES sessions(id),role TEXT NOT NULL,content TEXT NOT NULL,created REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS files(id TEXT PRIMARY KEY,session_id TEXT NOT NULL REFERENCES sessions(id),name TEXT NOT NULL,path TEXT NOT NULL,sha256 TEXT NOT NULL,size INTEGER NOT NULL,text TEXT NOT NULL,extraction_status TEXT NOT NULL,extraction_note TEXT NOT NULL,text_truncated INTEGER NOT NULL,created REAL NOT NULL,source_metadata TEXT NOT NULL DEFAULT '{}',extraction_coverage TEXT NOT NULL DEFAULT '{}');
            CREATE TABLE IF NOT EXISTS jobs(id TEXT PRIMARY KEY,session_id TEXT NOT NULL REFERENCES sessions(id),prompt TEXT NOT NULL,file_ids TEXT NOT NULL,state TEXT NOT NULL,result TEXT,error TEXT,created REAL NOT NULL,updated REAL NOT NULL,parent_id TEXT,mode TEXT NOT NULL DEFAULT 'CHAT',requested_checks TEXT NOT NULL DEFAULT '[]');
            CREATE TABLE IF NOT EXISTS local_evidence(id TEXT PRIMARY KEY,session_id TEXT NOT NULL REFERENCES sessions(id),file_id TEXT NOT NULL REFERENCES files(id),record TEXT NOT NULL,created REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS analysis_receipts(seq INTEGER PRIMARY KEY AUTOINCREMENT,job_id TEXT NOT NULL REFERENCES jobs(id),record TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS analysis_contexts(job_id TEXT NOT NULL REFERENCES jobs(id),role TEXT NOT NULL,messages TEXT NOT NULL,PRIMARY KEY(job_id,role));
            CREATE TABLE IF NOT EXISTS extraction_pages(job_id TEXT NOT NULL REFERENCES jobs(id),page INTEGER NOT NULL,record TEXT NOT NULL,PRIMARY KEY(job_id,page));
            CREATE TABLE IF NOT EXISTS source_reviews(id TEXT PRIMARY KEY,candidate_id TEXT NOT NULL REFERENCES local_evidence(id),session_id TEXT NOT NULL REFERENCES sessions(id),revision INTEGER NOT NULL,record TEXT NOT NULL,created REAL NOT NULL,UNIQUE(candidate_id,revision));
            CREATE TABLE IF NOT EXISTS requirement_sets(id TEXT PRIMARY KEY,session_id TEXT NOT NULL REFERENCES sessions(id),record TEXT NOT NULL,created REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS domain_packets(id TEXT PRIMARY KEY,session_id TEXT NOT NULL REFERENCES sessions(id),revision INTEGER NOT NULL,record TEXT NOT NULL,UNIQUE(session_id,revision));
            CREATE TABLE IF NOT EXISTS requirement_assessments(id TEXT PRIMARY KEY,set_id TEXT NOT NULL REFERENCES requirement_sets(id),requirement_id TEXT NOT NULL,revision INTEGER NOT NULL,record TEXT NOT NULL,UNIQUE(set_id,requirement_id,revision));
            CREATE TABLE IF NOT EXISTS real_case_snapshots(id TEXT PRIMARY KEY,session_id TEXT NOT NULL REFERENCES sessions(id),job_id TEXT NOT NULL REFERENCES jobs(id),revision INTEGER NOT NULL,record TEXT NOT NULL,created REAL NOT NULL,UNIQUE(session_id,revision));
            CREATE TABLE IF NOT EXISTS final_audits(id TEXT PRIMARY KEY,session_id TEXT NOT NULL REFERENCES sessions(id),case_id TEXT NOT NULL REFERENCES real_case_snapshots(id),revision INTEGER NOT NULL,record TEXT NOT NULL,created REAL NOT NULL,UNIQUE(session_id,revision));
            CREATE TABLE IF NOT EXISTS knowledge_revisions(id TEXT NOT NULL,revision INTEGER NOT NULL,source_session_id TEXT NOT NULL REFERENCES sessions(id),record TEXT NOT NULL,PRIMARY KEY(id,revision));
            CREATE TABLE IF NOT EXISTS knowledge_content(id TEXT NOT NULL,revision INTEGER NOT NULL,content TEXT NOT NULL,PRIMARY KEY(id,revision),FOREIGN KEY(id,revision) REFERENCES knowledge_revisions(id,revision));
            CREATE TABLE IF NOT EXISTS conclusion_drafts(id TEXT PRIMARY KEY,session_id TEXT NOT NULL REFERENCES sessions(id),revision INTEGER NOT NULL,record TEXT NOT NULL,UNIQUE(session_id,revision));
            CREATE UNIQUE INDEX IF NOT EXISTS one_active_job ON jobs(session_id) WHERE state IN ('QUEUED','RUNNING');
            ''')
            columns={r['name'] for r in db.execute('PRAGMA table_info(jobs)')}
            file_columns={r['name'] for r in db.execute('PRAGMA table_info(files)')}
            if 'parent_id' not in columns:db.execute('ALTER TABLE jobs ADD COLUMN parent_id TEXT')
            if 'mode' not in columns:db.execute("ALTER TABLE jobs ADD COLUMN mode TEXT NOT NULL DEFAULT 'CHAT'")
            if 'requested_checks' not in columns:db.execute("ALTER TABLE jobs ADD COLUMN requested_checks TEXT NOT NULL DEFAULT '[]'")
            if 'source_metadata' not in file_columns:db.execute("ALTER TABLE files ADD COLUMN source_metadata TEXT NOT NULL DEFAULT '{}'")
            if 'extraction_coverage' not in file_columns:db.execute("ALTER TABLE files ADD COLUMN extraction_coverage TEXT NOT NULL DEFAULT '{}'")
            db.execute('PRAGMA user_version=1')

    @contextmanager
    def connection(self):
        managed_database(self.path)
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
            jobs=[self.job_dict(r) for r in db.execute('SELECT * FROM jobs WHERE session_id=? AND parent_id IS NULL ORDER BY created DESC LIMIT 200',(session_id,))]
            files=[self.file_dict(r) for r in db.execute('SELECT * FROM files WHERE session_id=? ORDER BY created LIMIT 200',(session_id,))]
            evidence=[json.loads(r['record']) for r in db.execute('SELECT record FROM local_evidence WHERE session_id=? ORDER BY created LIMIT 500',(session_id,))]
            review_rows=db.execute('SELECT candidate_id,record FROM source_reviews WHERE session_id=? ORDER BY revision',(session_id,))
            reviews={}
            for row in review_rows:reviews.setdefault(row['candidate_id'],[]).append(json.loads(row['record']))
            for item in evidence:
                item['reviews']=reviews.get(item['id'],[]);item['review_revision']=len(item['reviews']);item['latest_review']=item['reviews'][-1] if item['reviews'] else None
            count=db.execute('SELECT count(*) FROM messages WHERE session_id=?',(session_id,)).fetchone()[0]
        return dict(session=dict(session),messages=messages,jobs=jobs,files=files,evidence=evidence,history_windowed=count>len(messages),message_count=count)

    def history(self,session_id,*,kind='messages',before=None,limit=50):
        identifier(session_id)
        if kind not in {'messages','jobs'}:raise ValueError('Unknown history kind')
        if type(limit) is not int or not 1<=limit<=200:raise ValueError('History limit must be 1–200')
        if before is not None and (type(before) is not int or not 1<=before<=9223372036854775807):raise ValueError('Invalid history cursor')
        table=kind;column='seq' if kind=='messages' else 'rowid'
        with self.connection() as db:
            if db.execute('SELECT id FROM sessions WHERE id=?',(session_id,)).fetchone() is None:raise ValueError('Conversation not found')
            conditions='session_id=?'+(' AND parent_id IS NULL' if kind=='jobs' else '')
            args=[session_id]
            if before is not None:conditions+=f' AND {column}<?';args.append(before)
            rows=db.execute(f'SELECT {column} AS history_cursor,* FROM {table} WHERE {conditions} ORDER BY {column} DESC LIMIT ?',(*args,limit+1)).fetchall()
        has_more=len(rows)>limit;rows=rows[:limit]
        cursor=rows[-1]['history_cursor'] if rows else None
        records=[]
        for row in rows:
            record=dict(row);record.pop('history_cursor')
            records.append(record if kind=='messages' else self.job_dict(record))
        return dict(records=records,has_more=has_more,next_before=cursor if has_more else None,kind=kind)

    @staticmethod
    def file_dict(row,private=False):
        r=dict(row);r['text_truncated']=bool(r['text_truncated']);r['acceptance_granted']=False
        source=r.get('source_metadata','{}');r['source_metadata']=json.loads(source) if isinstance(source,str) else source
        coverage=r.get('extraction_coverage',{})
        coverage=json.loads(coverage) if isinstance(coverage,str) else coverage
        r['extraction_coverage']=coverage or unknown_coverage()
        if not private:
            r.pop('path');r.pop('text')
        return r

    @staticmethod
    def job_dict(row):
        r=dict(row);r['file_ids']=json.loads(r['file_ids']);r['result']=json.loads(r['result']) if r['result'] else None;r['requested_checks']=json.loads(r['requested_checks'])
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
            stored=dict(record,source_metadata=json.dumps(record.get('source_metadata',{}),ensure_ascii=False),extraction_coverage=json.dumps(record.get('extraction_coverage',unknown_coverage()),ensure_ascii=False))
            db.execute('INSERT INTO files(id,session_id,name,path,sha256,size,text,extraction_status,extraction_note,text_truncated,created,source_metadata,extraction_coverage) VALUES(:id,:session_id,:name,:path,:sha256,:size,:text,:extraction_status,:extraction_note,:text_truncated,:created,:source_metadata,:extraction_coverage)',stored)
        return self.file_dict(record)

    def get_evidence(self,session_id,candidate_id):
        identifier(session_id);identifier(candidate_id)
        with self.connection() as db:r=db.execute('SELECT record FROM local_evidence WHERE id=? AND session_id=?',(candidate_id,session_id)).fetchone()
        if r is None:raise ValueError('Source candidate not found in this conversation')
        return json.loads(r['record'])

    def requirements_state(self,session_id):
        identifier(session_id)
        with self.connection() as db:
            if db.execute('SELECT id FROM sessions WHERE id=?',(session_id,)).fetchone() is None:raise ValueError('Conversation not found')
            sets=[json.loads(r['record']) for r in db.execute('SELECT record FROM requirement_sets WHERE session_id=? ORDER BY rowid',(session_id,))]
            events=[json.loads(r['record']) for r in db.execute('SELECT a.record FROM requirement_assessments a JOIN requirement_sets s ON s.id=a.set_id WHERE s.session_id=? ORDER BY a.rowid',(session_id,))]
        return dict(sets=sets,assessments=events)

    def domain_packets_state(self,session_id):
        self.requirements_state(session_id)
        with self.connection() as db:
            return [json.loads(r['record']) for r in db.execute('SELECT record FROM domain_packets WHERE session_id=? ORDER BY revision',(session_id,))]

    def add_domain_packet(self,event,expected_revision):
        from .analysis_identity import digest
        with self.connection() as db:
            db.execute('BEGIN IMMEDIATE')
            count=db.execute('SELECT count(*) FROM domain_packets WHERE session_id=?',(event['session_id'],)).fetchone()[0]
            if count!=expected_revision:raise ReviewConflict('Domain packet changed; reopen before saving')
            if count>=100:raise ValueError('Domain packet history limit: 100 per conversation')
            for source in event['sources']:
                r=db.execute('SELECT record FROM local_evidence WHERE id=? AND session_id=?',(source['candidate_id'],event['session_id'])).fetchone()
                review=db.execute('SELECT id,revision FROM source_reviews WHERE candidate_id=? ORDER BY revision DESC LIMIT 1',(source['candidate_id'],)).fetchone()
                if not r or digest(json.loads(r['record']))!=source['candidate_sha256'] or (review['revision'] if review else 0)!=source['review_revision'] or (review['id'] if review else None)!=source['review_event_id']:
                    raise ReviewConflict('Source review changed before packet save')
            event=dict(event,revision=count+1)
            db.execute('INSERT INTO domain_packets VALUES(?,?,?,?)',(event['id'],event['session_id'],event['revision'],json.dumps(event,ensure_ascii=False)))
        return event


    def real_case_state(self,session_id):
        identifier(session_id)
        with self.connection() as db:
            if db.execute('SELECT id FROM sessions WHERE id=?',(session_id,)).fetchone() is None:raise ValueError('Conversation not found')
            return [json.loads(r['record']) for r in db.execute('SELECT record FROM real_case_snapshots WHERE session_id=? ORDER BY revision',(session_id,))]

    def add_real_case_snapshot(self,event,expected_revision):
        identifier(event['session_id']);identifier(event['job_id'])
        if type(expected_revision) is not int or expected_revision<0:raise ValueError('Case revision required')
        with self.connection() as db:
            db.execute('BEGIN IMMEDIATE')
            if db.execute('SELECT id FROM jobs WHERE id=? AND session_id=?',(event['job_id'],event['session_id'])).fetchone() is None:
                raise ValueError('Case job not found in this conversation')
            count=db.execute('SELECT count(*) FROM real_case_snapshots WHERE session_id=?',(event['session_id'],)).fetchone()[0]
            if count!=expected_revision:raise ReviewConflict('Real case changed; reopen before saving')
            if count>=100:raise ValueError('Real case history limit: 100 per conversation')
            record=dict(event,revision=count+1)
            db.execute('INSERT INTO real_case_snapshots VALUES(?,?,?,?,?,?)',
                (record['id'],record['session_id'],record['job_id'],record['revision'],json.dumps(record,ensure_ascii=False),record['created']))
        return record


    def final_audit_state(self,session_id):
        identifier(session_id)
        with self.connection() as db:
            if db.execute('SELECT id FROM sessions WHERE id=?',(session_id,)).fetchone() is None:raise ValueError('Conversation not found')
            return [json.loads(r['record']) for r in db.execute('SELECT record FROM final_audits WHERE session_id=? ORDER BY revision',(session_id,))]

    def add_final_audit(self,event,expected_revision):
        identifier(event['session_id']);identifier(event['case_id'])
        if type(expected_revision) is not int or expected_revision<0:raise ValueError('Final audit revision required')
        with self.connection() as db:
            db.execute('BEGIN IMMEDIATE')
            if db.execute('SELECT id FROM real_case_snapshots WHERE id=? AND session_id=?',(event['case_id'],event['session_id'])).fetchone() is None:
                raise ValueError('Final audit case not found in this conversation')
            count=db.execute('SELECT count(*) FROM final_audits WHERE session_id=?',(event['session_id'],)).fetchone()[0]
            if count!=expected_revision:raise ReviewConflict('FINAL AUDIT changed; reopen before saving')
            if count>=100:raise ValueError('FINAL AUDIT history limit: 100 per conversation')
            record=dict(event,revision=count+1)
            db.execute('INSERT INTO final_audits VALUES(?,?,?,?,?,?)',
                (record['id'],record['session_id'],record['case_id'],record['revision'],json.dumps(record,ensure_ascii=False),record['created']))
        return record

    def add_requirement_set(self,record):
        with self.connection() as db:
            db.execute('BEGIN IMMEDIATE')
            if db.execute('SELECT count(*) FROM requirement_sets WHERE session_id=?',(record['session_id'],)).fetchone()[0]>=20:raise ValueError('Requirement set limit: 20 per conversation')
            db.execute('INSERT INTO requirement_sets VALUES(?,?,?,?)',(record['id'],record['session_id'],json.dumps(record,ensure_ascii=False),record['created']))
        return record

    def add_requirement_assessment(self,session_id,event,expected_revision):
        with self.connection() as db:
            db.execute('BEGIN IMMEDIATE')
            latest=db.execute('SELECT id,record FROM requirement_sets WHERE session_id=? ORDER BY rowid DESC LIMIT 1',(session_id,)).fetchone()
            if latest is None or latest['id']!=event['set_id'] or event['requirement_id'] not in {r['id'] for r in json.loads(latest['record'])['requirements']}:raise ValueError('Current requirement not found')
            count=db.execute('SELECT count(*) FROM requirement_assessments WHERE set_id=? AND requirement_id=?',(event['set_id'],event['requirement_id'])).fetchone()[0]
            if count!=expected_revision:raise ReviewConflict('Requirement assessment changed; reopen before saving')
            total=db.execute('SELECT count(*) FROM requirement_assessments a JOIN requirement_sets s ON s.id=a.set_id WHERE s.session_id=?',(session_id,)).fetchone()[0]
            if count>=50 or total>=1000:raise ValueError('Requirement assessment history limit')
            for source in event['sources']:
                candidate=db.execute('SELECT record FROM local_evidence WHERE id=? AND session_id=?',(source['candidate_id'],session_id)).fetchone()
                revision=db.execute('SELECT count(*) FROM source_reviews WHERE candidate_id=?',(source['candidate_id'],)).fetchone()[0]
                if candidate is None or revision!=source['review_revision']:raise ReviewConflict('Source review changed; reopen before saving')
            event=dict(event,revision=count+1)
            db.execute('INSERT INTO requirement_assessments VALUES(?,?,?,?,?)',(event['id'],event['set_id'],event['requirement_id'],event['revision'],json.dumps(event,ensure_ascii=False)))
        return event

    def append_review(self,event,expected_revision):
        with self.connection() as db:
            db.execute('BEGIN IMMEDIATE')
            row=db.execute('SELECT record FROM local_evidence WHERE id=? AND session_id=?',(event['candidate_id'],event['session_id'])).fetchone()
            if row is None:raise ValueError('Candidate not found in this conversation')
            count=db.execute('SELECT count(*) FROM source_reviews WHERE candidate_id=?',(event['candidate_id'],)).fetchone()[0]
            if count!=expected_revision:raise ReviewConflict('Review changed; reopen candidate before saving your decision')
            if count>=50 or db.execute('SELECT count(*) FROM source_reviews WHERE session_id=?',(event['session_id'],)).fetchone()[0]>=500:raise ValueError('Review history limit reached (50 per candidate, 500 per conversation)')
            event=dict(event,revision=count+1,candidate_digest=hashlib.sha256(json.dumps(json.loads(row['record']),sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest(),acceptance_granted=False,actor_verified=False)
            db.execute('INSERT INTO source_reviews VALUES(?,?,?,?,?,?)',(event['id'],event['candidate_id'],event['session_id'],event['revision'],json.dumps(event,ensure_ascii=False),event['created']))
        return event

    def add_evidence(self,record):
        with self.connection() as db:
            db.execute('BEGIN IMMEDIATE')
            if db.execute('SELECT id FROM files WHERE id=? AND session_id=?',(record['file_id'],record['session_id'])).fetchone() is None:raise ValueError('Original isolation failure')
            if db.execute('SELECT count(*) FROM local_evidence WHERE session_id=?',(record['session_id'],)).fetchone()[0]>=500:raise ValueError('Candidate limit: 500 per conversation')
            db.execute('INSERT INTO local_evidence VALUES(?,?,?,?,?)',(record['id'],record['session_id'],record['file_id'],json.dumps(record,ensure_ascii=False),record['created']))
        return record

    def enqueue(self,session_id,prompt,file_ids,*,mode='CHAT',requested_checks=None):
        identifier(session_id)
        if not isinstance(prompt,str) or not prompt.strip() or len(prompt)>8000:raise ValueError('Message must contain 1–8000 characters')
        if not isinstance(file_ids,list) or len(file_ids)>20 or any(not isinstance(x,str) for x in file_ids) or len(set(file_ids))!=len(file_ids):raise ValueError('Select up to 20 distinct files')
        if not isinstance(mode,str) or mode not in {'CHAT','CORE_PLAN','CORE_RUN','EXTRACT_NATIVE','EXTRACT_DOCLING','EXTRACT_OCR'}:raise ValueError('Unknown task mode')
        checks=requested_checks if requested_checks is not None else (['report','normative'] if mode in {'CORE_PLAN','CORE_RUN'} else [])
        from engineering.core.engineer_core import CHECK_REGISTRY
        if not isinstance(checks,list) or len(checks)>5 or any(not isinstance(c,str) or c not in CHECK_REGISTRY for c in checks) or len(set(checks))!=len(checks):raise ValueError('Invalid requested engineering checks')
        if mode not in {'CORE_PLAN','CORE_RUN'} and checks:raise ValueError('Engineering checks require a CORE mode')
        if mode in {'CORE_PLAN','CORE_RUN'} and (not file_ids or not checks):raise ValueError('ТЗ, selected originals and checks required for CORE')
        if mode.startswith('EXTRACT_'):
            if len(file_ids)!=1:raise ValueError('Extraction requires one PDF')
            original=self.get_file(file_ids[0])
            allowed={'.pdf','.png','.jpg','.jpeg'} if mode=='EXTRACT_OCR' else {'.pdf'}
            if Path(original['name']).suffix.lower() not in allowed:raise ValueError('Unsupported original for extraction backend')
        for value in file_ids:identifier(value)
        now=time.time();record=dict(id=str(uuid.uuid4()),session_id=session_id,prompt=prompt.strip(),file_ids=json.dumps(file_ids),state='QUEUED',result=None,error=None,created=now,updated=now,mode=mode,requested_checks=json.dumps(checks))
        try:
            with self.connection() as db:
                db.execute('BEGIN IMMEDIATE')
                if db.execute('SELECT id FROM sessions WHERE id=?',(session_id,)).fetchone() is None:raise ValueError('Conversation not found')
                for fid in file_ids:
                    if db.execute('SELECT id FROM files WHERE id=? AND session_id=?',(fid,session_id)).fetchone() is None:raise ValueError('Attachment belongs to another conversation or does not exist')
                db.execute('INSERT INTO jobs(id,session_id,prompt,file_ids,state,result,error,created,updated,mode,requested_checks) VALUES(:id,:session_id,:prompt,:file_ids,:state,:result,:error,:created,:updated,:mode,:requested_checks)',record)
                db.execute('INSERT INTO messages(session_id,role,content,created) VALUES(?,?,?,?)',(session_id,'user',record['prompt'],now))
                db.execute("UPDATE sessions SET title=? WHERE id=? AND title='Новый диалог'",(record['prompt'][:60],session_id))
        except sqlite3.IntegrityError:raise ValueError('This conversation already has an active task') from None
        return self.job_dict(record)

    def automatic_extraction(self,parent,file_id,backend,parser_identity=None):
        from .core_plan import verify_originals
        f=self.get_file(file_id);verify_originals([f])
        if f['session_id']!=parent['session_id'] or file_id not in parent['file_ids']:raise ValueError('Attachment isolation failure')
        with self.connection() as db:
            existing=db.execute("SELECT * FROM jobs WHERE session_id=? AND mode=? AND file_ids=? AND state='SUCCEEDED' ORDER BY created DESC LIMIT 20",(parent['session_id'],'EXTRACT_'+backend.upper(),json.dumps([file_id]))).fetchall()
            for row in existing:
                job=self.job_dict(row);r=(job['result'] or {}).get('extraction',{})
                if r.get('source_sha256')==f['sha256'] and (parser_identity is None or r.get('parser_identity')==parser_identity) and r.get('cycle_complete') and not r.get('failed_pages') and not r.get('budget_exhausted'):return job,False
            db.execute('BEGIN IMMEDIATE')
            current=db.execute("SELECT id FROM jobs WHERE id=? AND state='RUNNING'",(parent['id'],)).fetchone()
            if current is None:raise ValueError('Parent task not running')
            previous=db.execute('SELECT * FROM jobs WHERE parent_id=? AND file_ids=? ORDER BY created DESC LIMIT 1',(parent['id'],json.dumps([file_id]))).fetchone()
            if previous:
                child=self.job_dict(previous);r=(child['result'] or {}).get('extraction',{})
                if r.get('budget_exhausted'):raise ValueError('Attachment extraction budget exhausted; resume cannot reset it')
                if r.get('source_sha256')==f['sha256'] and r.get('parser_identity')==parser_identity and not r.get('budget_exhausted') and child['state'] in {'FAILED','SUCCEEDED'}:
                    db.execute("UPDATE jobs SET state='ATTACHMENT',error=NULL,updated=? WHERE id=?",(time.time(),child['id']))
                    return dict(child,state='ATTACHMENT'),True
            now=time.time();record=dict(id=str(uuid.uuid4()),session_id=parent['session_id'],prompt='Автоматическая обработка документа',file_ids=json.dumps([file_id]),state='ATTACHMENT',result=None,error=None,created=now,updated=now,mode='EXTRACT_'+backend.upper(),requested_checks='[]',parent_id=parent['id'])
            db.execute('INSERT INTO jobs(id,session_id,prompt,file_ids,state,result,error,created,updated,mode,requested_checks,parent_id) VALUES(:id,:session_id,:prompt,:file_ids,:state,:result,:error,:created,:updated,:mode,:requested_checks,:parent_id)',record)
        return self.job_dict(record),True

    def finish_attachment(self,job_id,result):
        result=dict(result,acceptance_granted=False)
        with self.connection() as db:
            previous=db.execute('SELECT result FROM jobs WHERE id=?',(job_id,)).fetchone()
            prior=json.loads(previous['result']) if previous and previous['result'] else {}
            if 'document_analysis' in prior:result['document_analysis']=prior['document_analysis']
            if db.execute("UPDATE jobs SET result=?,state='SUCCEEDED',updated=? WHERE id=? AND state='ATTACHMENT'",(json.dumps(result,ensure_ascii=False),time.time(),job_id)).rowcount!=1:raise ValueError('Attachment task not running')

    def analysis_progress(self,job_id,report):
        with self.connection() as db:
            db.execute('BEGIN IMMEDIATE')
            row=db.execute("SELECT result FROM jobs WHERE id=? AND state='RUNNING'",(job_id,)).fetchone()
            if row is None:raise ValueError('Task not running')
            result=json.loads(row['result']) if row['result'] else dict(text='Обработка прикреплённого документа…',acceptance_granted=False)
            result['document_analysis']=report
            db.execute('UPDATE jobs SET result=?,updated=? WHERE id=?',(json.dumps(result,ensure_ascii=False),time.time(),job_id))

    def save_analysis_receipt(self,job_id,record,*,update_seq=None):
        with self.connection() as db:
            db.execute('BEGIN IMMEDIATE')
            row=db.execute("SELECT result FROM jobs WHERE id=? AND state='RUNNING'",(job_id,)).fetchone()
            if row is None:raise ValueError('Task not running')
            encoded=json.dumps(dict(record,acceptance_granted=False,scope='PRELIMINARY_ANALYSIS'),ensure_ascii=False)
            if update_seq is None:
                cur=db.execute('INSERT INTO analysis_receipts(job_id,record) VALUES(?,?)',(job_id,encoded));seq=cur.lastrowid
            else:
                if db.execute("UPDATE analysis_receipts SET record=? WHERE seq=? AND job_id=? AND json_extract(record,'$.status')='RUNNING'",(encoded,update_seq,job_id)).rowcount!=1:raise ValueError('Call checkpoint changed')
                seq=update_seq
            if record.get('role')!='CHAT' and record.get('status')=='COMPLETED' and json.loads(record['text']).get('status')=='BLOCK':
                result=json.loads(row['result'])
                result['document_analysis']['roles'][record['role']]['block_seen']=True
                db.execute('UPDATE jobs SET result=? WHERE id=?',(json.dumps(result,ensure_ascii=False),job_id))
            return seq

    def reconcile_interrupted_analysis_receipts(self,job_id):
        """On resumed execution, preserve old incomplete calls as interrupted attempts.

        A RUNNING receipt has no verified response. Never convert it to COMPLETED,
        reuse it as a cached result, or erase its attempt from the audit trail.
        """
        with self.connection() as db:
            db.execute('BEGIN IMMEDIATE')
            if db.execute("SELECT id FROM jobs WHERE id=? AND state='RUNNING'",(job_id,)).fetchone() is None:
                raise ValueError('Task not running')
            rows=db.execute("SELECT seq,record FROM analysis_receipts WHERE job_id=? AND json_extract(record,'$.status')='RUNNING' ORDER BY seq",(job_id,)).fetchall()
            for row in rows:
                record=json.loads(row['record'])
                record.update(status='INTERRUPTED',error='Prior model response not durably recorded; retry required.',acceptance_granted=False)
                db.execute("UPDATE analysis_receipts SET record=? WHERE seq=? AND job_id=? AND json_extract(record,'$.status')='RUNNING'",
                           (json.dumps(record,ensure_ascii=False),row['seq'],job_id))
            return len(rows)

    def analysis_receipts(self,session_id,job_id,*,offset=0,limit=50):
        identifier(session_id);identifier(job_id)
        if type(offset) is not int or offset<0 or type(limit) is not int or not 1<=limit<=50:raise ValueError('Invalid analysis window')
        with self.connection() as db:
            if db.execute('SELECT id FROM jobs WHERE id=? AND session_id=? AND parent_id IS NULL',(job_id,session_id)).fetchone() is None:raise ValueError('Analysis not found in conversation')
            rows=db.execute('SELECT seq,record FROM analysis_receipts WHERE job_id=? ORDER BY seq LIMIT ? OFFSET ?',(job_id,limit,offset)).fetchall()
            total=db.execute('SELECT count(*) FROM analysis_receipts WHERE job_id=?',(job_id,)).fetchone()[0]
        return dict(records=[dict(json.loads(r['record']),receipt_id=r['seq']) for r in rows],total=total,has_more=offset+len(rows)<total)

    def analysis_context(self,job_id,role,messages):
        with self.connection() as db:
            db.execute('BEGIN IMMEDIATE')
            if db.execute("SELECT id FROM jobs WHERE id=? AND state='RUNNING'",(job_id,)).fetchone() is None:raise ValueError('Task not running')
            row=db.execute('SELECT messages FROM analysis_contexts WHERE job_id=? AND role=?',(job_id,role)).fetchone()
            if row:return json.loads(row['messages'])
            db.execute('INSERT INTO analysis_contexts VALUES(?,?,?)',(job_id,role,json.dumps(messages,ensure_ascii=False)))
        return messages

    def resume_analysis(self,session_id,job_id,model):
        identifier(session_id);identifier(job_id)
        from .analysis_identity import identity
        try:
            with self.connection() as db:
                db.execute('BEGIN IMMEDIATE')
                row=db.execute('SELECT * FROM jobs WHERE id=? AND session_id=? AND parent_id IS NULL',(job_id,session_id)).fetchone()
                if row is None:raise ValueError('Analysis not found in conversation')
                job=self.job_dict(row);report=(job['result'] or {}).get('document_analysis',{})
                if job['mode'] not in {'CHAT','CORE_RUN'} or job['state'] not in {'FAILED','SUCCEEDED','CANCELLED'} or not report or report.get('all_batches_completed') or report.get('budget_exhausted') or not report.get('resume_supported'):
                    raise ValueError('Analysis cannot be resumed; create a new task if inputs/settings changed')
                _,fingerprint,supported=identity(self,job,model)
                if not supported or fingerprint!=report.get('identity_sha256'):raise ValueError('Analysis identity changed; submit a new task')
                report['resume_count']=report.get('resume_count',0)+1
                job['result']['document_analysis']=report
                db.execute("UPDATE jobs SET state='QUEUED',error=NULL,result=?,updated=? WHERE id=?",(json.dumps(job['result'],ensure_ascii=False),time.time(),job_id))
                return dict(job,state='QUEUED',error=None)
        except sqlite3.IntegrityError:raise ValueError('Conversation already has an active task') from None

    def enqueue_extraction(self,session_id,file_id,backend):
        if not isinstance(backend,str) or backend not in {'native','docling','ocr'}:raise ValueError('Unknown extraction backend')
        return self.enqueue(session_id,'Извлечение PDF · '+backend,[file_id],mode='EXTRACT_'+backend.upper())

    def extraction_job(self,session_id,job_id):
        identifier(session_id);identifier(job_id)
        with self.connection() as db:r=db.execute('SELECT * FROM jobs WHERE id=? AND session_id=?',(job_id,session_id)).fetchone()
        if r is None or not r['mode'].startswith('EXTRACT_'):raise ValueError('Extraction task not found in conversation')
        return self.job_dict(r)

    def resume_extraction(self,session_id,job_id):
        job=self.extraction_job(session_id,job_id)
        if job.get('parent_id'):raise ValueError('Resubmit the parent task to process attachments')
        run=(job['result'] or {}).get('extraction',{})
        if job['state'] not in {'FAILED','SUCCEEDED','CANCELLED'} or not run or run.get('budget_exhausted'):
            raise ValueError('Task cannot be resumed')
        if run.get('cycle_complete') and not run.get('failed_pages'):raise ValueError('Extraction cycle already complete')
        from .core_plan import verify_originals
        f=self.get_file(job['file_ids'][0]);verify_originals([f])
        if f['sha256']!=run.get('source_sha256') or f['session_id']!=session_id:raise ValueError('Original identity changed')
        from .analysis_identity import parser_identity
        if run.get('parser_identity')!=parser_identity(run['backend']):raise ValueError('Parser identity changed; create a new extraction task')
        try:
            with self.connection() as db:
                db.execute('BEGIN IMMEDIATE')
                if db.execute("UPDATE jobs SET state='QUEUED',error=NULL,updated=? WHERE id=? AND state=?",(time.time(),job_id,job['state'])).rowcount!=1:raise ValueError('Task state changed')
        except sqlite3.IntegrityError:raise ValueError('Conversation already has an active task') from None
        return self.extraction_job(session_id,job_id)

    def extraction_totals(self,job_id):
        with self.connection() as db:
            r=db.execute("SELECT count(*) processed_pages,coalesce(sum(json_extract(record,'$.stored_chars')),0) stored_chars,coalesce(sum(json_extract(record,'$.execution')='FAILED'),0) failed_pages,coalesce(sum(json_extract(record,'$.status')='BLOCK'),0) blocked_pages FROM extraction_pages WHERE job_id=?",(job_id,)).fetchone()
        return dict(r)

    def extraction_completed(self,job_id,page):
        with self.connection() as db:r=db.execute("SELECT json_extract(record,'$.execution') execution FROM extraction_pages WHERE job_id=? AND page=?",(job_id,page)).fetchone()
        return r is not None and r['execution']=='COMPLETED'

    def save_extraction_page(self,job_id,record):
        with self.connection() as db:
            db.execute('BEGIN IMMEDIATE')
            r=db.execute('SELECT state FROM jobs WHERE id=?',(job_id,)).fetchone()
            if r is None or r['state'] not in {'RUNNING','ATTACHMENT'}:raise ValueError('Task is not running')
            db.execute('INSERT INTO extraction_pages VALUES(?,?,?) ON CONFLICT(job_id,page) DO UPDATE SET record=excluded.record',(job_id,record['page'],json.dumps(record,ensure_ascii=False)))

    def extraction_pages(self,session_id,job_id,*,offset=0,limit=50):
        self.extraction_job(session_id,job_id)
        if type(offset) is not int or offset<0 or type(limit) is not int or not 1<=limit<=50:raise ValueError('Invalid journal window')
        with self.connection() as db:
            rows=db.execute('SELECT record FROM extraction_pages WHERE job_id=? ORDER BY page LIMIT ? OFFSET ?',(job_id,limit,offset)).fetchall()
            total=db.execute('SELECT count(*) FROM extraction_pages WHERE job_id=?',(job_id,)).fetchone()[0]
        pages=[]
        for row in rows:
            record=json.loads(row['record']);blocks=record.pop('blocks');record['blocks_count']=len(blocks);pages.append(record)
        return dict(pages=pages,total=total,offset=offset,has_more=offset+len(pages)<total)

    def extraction_page(self,session_id,job_id,page):
        self.extraction_job(session_id,job_id)
        if type(page) is not int or page<1:raise ValueError('Invalid page')
        with self.connection() as db:r=db.execute('SELECT record FROM extraction_pages WHERE job_id=? AND page=?',(job_id,page)).fetchone()
        if r is None:raise ValueError('Extraction page not found')
        return json.loads(r['record'])

    def claim(self):
        with self.connection() as db:
            db.execute('BEGIN IMMEDIATE')
            r=db.execute("SELECT * FROM jobs WHERE state='QUEUED' ORDER BY created LIMIT 1").fetchone()
            if r is None:return None
            db.execute("UPDATE jobs SET state='RUNNING',updated=? WHERE id=?",(time.time(),r['id']))
            return self.job_dict(dict(r,state='RUNNING'))

    def cancel(self,session_id,job_id):
        identifier(session_id);identifier(job_id)
        with self.connection() as db:
            db.execute('BEGIN IMMEDIATE')
            row=db.execute('SELECT * FROM jobs WHERE id=? AND session_id=?',(job_id,session_id)).fetchone()
            if row is None or row['parent_id'] or row['state'] not in {'QUEUED','RUNNING'}:raise ValueError('Task cannot be cancelled')
            state='CANCELLED' if row['state']=='QUEUED' else 'RUNNING'
            db.execute('UPDATE jobs SET state=?,error=?,updated=? WHERE id=?',(state,'CANCEL_REQUESTED' if state=='RUNNING' else 'Отменено пользователем до начала выполнения.',time.time(),job_id))
        return dict(id=job_id,state=state,cancel_requested=True)

    def cancellation_requested(self,job_id):
        with self.connection() as db:
            row=db.execute('SELECT error FROM jobs WHERE id=?',(job_id,)).fetchone()
        return bool(row and row['error']=='CANCEL_REQUESTED')

    def retry(self,session_id,job_id):
        identifier(session_id);identifier(job_id)
        with self.connection() as db:
            row=db.execute('SELECT * FROM jobs WHERE id=? AND session_id=?',(job_id,session_id)).fetchone()
        if row is None or row['parent_id'] or row['mode'].startswith('EXTRACT_') or row['state'] not in {'FAILED','CANCELLED'}:raise ValueError('Task cannot be retried; extraction uses its preserved journal')
        job=self.job_dict(row)
        return self.enqueue(session_id,job['prompt'],job['file_ids'],mode=job['mode'],requested_checks=job['requested_checks'])

    def checkpoint(self,job_id,result):
        identifier(job_id)
        if not isinstance(result,dict) or not isinstance(result.get('text'),str):raise ValueError('Invalid progress result')
        status=(result.get('core_run') or {}).get('status','UNCERTAINTY')
        if (result.get('specialist_checks') or {}).get('status')=='BLOCK':
            status='ERROR' if (result.get('core_run') or {}).get('status')=='ERROR' else 'BLOCK'
        result=dict(result,engineering_status=status,evidentiary_status='NOT_EVIDENCE',acceptance_granted=False,final_audit='NOT_RUN')
        with self.connection() as db:
            previous=db.execute('SELECT result FROM jobs WHERE id=?',(job_id,)).fetchone()
            prior=json.loads(previous['result']) if previous and previous['result'] else {}
            if 'document_analysis' in prior:result['document_analysis']=prior['document_analysis']
            if db.execute("UPDATE jobs SET result=?,updated=? WHERE id=? AND state IN ('RUNNING','ATTACHMENT')",(json.dumps(result,ensure_ascii=False),time.time(),job_id)).rowcount!=1:raise ValueError('Task is not running')

    def finish(self,job_id,result):
        identifier(job_id)
        if not isinstance(result,dict) or not isinstance(result.get('text'),str) or not result['text'].strip():raise ValueError('Nonempty model response required')
        status=(result.get('core_run') or {}).get('status','UNCERTAINTY')
        if (result.get('specialist_checks') or {}).get('status')=='BLOCK':
            status='ERROR' if (result.get('core_run') or {}).get('status')=='ERROR' else 'BLOCK'
        result=dict(result,engineering_status=status,evidentiary_status='NOT_EVIDENCE',acceptance_granted=False,final_audit='NOT_RUN')
        with self.connection() as db:
            db.execute('BEGIN IMMEDIATE')
            r=db.execute("SELECT * FROM jobs WHERE id=? AND state='RUNNING' AND (error IS NULL OR error!='CANCEL_REQUESTED')",(job_id,)).fetchone()
            if r is None:raise ValueError('Task is not running')
            prior=json.loads(r['result']) if r['result'] else {}
            if 'document_analysis' in prior:
                if db.execute("SELECT 1 FROM analysis_receipts WHERE job_id=? AND json_extract(record,'$.status')='RUNNING' LIMIT 1",(job_id,)).fetchone():
                    raise ValueError('Incomplete model receipt; cannot finish analysis')
                result['document_analysis']=prior['document_analysis']
            now=time.time();db.execute("UPDATE jobs SET state='SUCCEEDED',result=?,updated=? WHERE id=?",(json.dumps(result,ensure_ascii=False),now,job_id))
            db.execute('INSERT INTO messages(session_id,role,content,created) VALUES(?,?,?,?)',(r['session_id'],'assistant',result['text'],now))

    def fail(self,job_id,error):
        identifier(job_id)
        with self.connection() as db:
            db.execute('BEGIN IMMEDIATE')
            row=db.execute("SELECT result,error FROM jobs WHERE id=? AND state IN ('RUNNING','ATTACHMENT')",(job_id,)).fetchone()
            if row is None:return
            result=json.loads(row['result']) if row['result'] else None
            if result and 'document_analysis' in result:
                result['document_analysis'].update(stage='PARTIAL',all_batches_completed=False)
                run=result.get('core_run')
                if run:
                    for role,progress in result['document_analysis'].get('roles',{}).items():
                        if progress.get('block_seen'):
                            run['status']='BLOCK'
                            for r in run['results']:
                                if r['agent']==role:r.update(status='BLOCK',execution='INTERRUPTED' if r['execution']=='RUNNING' else r['execution'])
            cancelled=row['error']=='CANCEL_REQUESTED'
            db.execute("UPDATE jobs SET state=?,error=?,result=?,updated=? WHERE id=?",('CANCELLED' if cancelled else 'FAILED','Отменено пользователем; сохранённые материалы оставлены.' if cancelled else str(error)[:500],json.dumps(result,ensure_ascii=False) if result else None,time.time(),job_id))

    def interrupt_running(self):
        # The caller must own the exclusive data-directory lock.
        with self.connection() as db:ids=[r['id'] for r in db.execute("SELECT id FROM jobs WHERE state IN ('RUNNING','ATTACHMENT')")]
        for job_id in ids:self.fail(job_id,'Execution interrupted; submit again to retry.')

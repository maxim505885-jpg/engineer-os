"""Transactional, disk-backed conversations and single-claim jobs."""
from contextlib import contextmanager
import json
import hashlib
from pathlib import Path
import sqlite3
import time
import uuid
from .coverage import unknown_coverage


def identifier(value):
    if not isinstance(value,str):raise ValueError('Invalid identifier')
    try:valid=str(uuid.UUID(value))==value
    except ValueError:valid=False
    if not valid:raise ValueError('Invalid identifier')
    return value


class ReviewConflict(ValueError):
    pass


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
            CREATE TABLE IF NOT EXISTS local_evidence(id TEXT PRIMARY KEY,session_id TEXT NOT NULL REFERENCES sessions(id),file_id TEXT NOT NULL REFERENCES files(id),record TEXT NOT NULL,created REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS analysis_receipts(seq INTEGER PRIMARY KEY AUTOINCREMENT,job_id TEXT NOT NULL REFERENCES jobs(id),record TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS extraction_pages(job_id TEXT NOT NULL REFERENCES jobs(id),page INTEGER NOT NULL,record TEXT NOT NULL,PRIMARY KEY(job_id,page));
            CREATE TABLE IF NOT EXISTS source_reviews(id TEXT PRIMARY KEY,candidate_id TEXT NOT NULL REFERENCES local_evidence(id),session_id TEXT NOT NULL REFERENCES sessions(id),revision INTEGER NOT NULL,record TEXT NOT NULL,created REAL NOT NULL,UNIQUE(candidate_id,revision));
            CREATE UNIQUE INDEX IF NOT EXISTS one_active_job ON jobs(session_id) WHERE state IN ('QUEUED','RUNNING');
            ''')
            columns={r['name'] for r in db.execute('PRAGMA table_info(jobs)')}
            if 'parent_id' not in columns:db.execute('ALTER TABLE jobs ADD COLUMN parent_id TEXT')
            if 'mode' not in columns:db.execute("ALTER TABLE jobs ADD COLUMN mode TEXT NOT NULL DEFAULT 'CHAT'")
            if 'requested_checks' not in columns:db.execute("ALTER TABLE jobs ADD COLUMN requested_checks TEXT NOT NULL DEFAULT '[]'")
            file_columns={r['name'] for r in db.execute('PRAGMA table_info(files)')}
            if 'source_metadata' not in file_columns:db.execute("ALTER TABLE files ADD COLUMN source_metadata TEXT NOT NULL DEFAULT '{}'")
            if 'extraction_coverage' not in file_columns:db.execute("ALTER TABLE files ADD COLUMN extraction_coverage TEXT NOT NULL DEFAULT '{}'")

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
        if not isinstance(mode,str) or mode not in {'CHAT','CORE_PLAN','CORE_RUN','EXTRACT_NATIVE','EXTRACT_DOCLING'}:raise ValueError('Unknown task mode')
        checks=requested_checks if requested_checks is not None else (['report','normative'] if mode in {'CORE_PLAN','CORE_RUN'} else [])
        from engineering.core.engineer_core import CHECK_REGISTRY
        if not isinstance(checks,list) or len(checks)>5 or any(not isinstance(c,str) or c not in CHECK_REGISTRY for c in checks) or len(set(checks))!=len(checks):raise ValueError('Invalid requested engineering checks')
        if mode not in {'CORE_PLAN','CORE_RUN'} and checks:raise ValueError('Engineering checks require a CORE mode')
        if mode in {'CORE_PLAN','CORE_RUN'} and (not file_ids or not checks):raise ValueError('ТЗ, selected originals and checks required for CORE')
        if mode.startswith('EXTRACT_'):
            if len(file_ids)!=1:raise ValueError('Extraction requires one PDF')
            original=self.get_file(file_ids[0])
            if Path(original['name']).suffix.lower()!='.pdf':raise ValueError('Extraction requires a PDF original')
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

    def automatic_extraction(self,parent,file_id,backend):
        from .core_plan import verify_originals
        f=self.get_file(file_id);verify_originals([f])
        if f['session_id']!=parent['session_id'] or file_id not in parent['file_ids']:raise ValueError('Attachment isolation failure')
        with self.connection() as db:
            existing=db.execute("SELECT * FROM jobs WHERE session_id=? AND mode=? AND file_ids=? AND state='SUCCEEDED' ORDER BY created DESC LIMIT 20",(parent['session_id'],'EXTRACT_'+backend.upper(),json.dumps([file_id]))).fetchall()
            for row in existing:
                job=self.job_dict(row);r=(job['result'] or {}).get('extraction',{})
                if r.get('source_sha256')==f['sha256'] and r.get('cycle_complete') and not r.get('failed_pages') and not r.get('budget_exhausted'):return job,False
            db.execute('BEGIN IMMEDIATE')
            current=db.execute("SELECT id FROM jobs WHERE id=? AND state='RUNNING'",(parent['id'],)).fetchone()
            if current is None:raise ValueError('Parent task not running')
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

    def save_analysis_receipt(self,job_id,record):
        with self.connection() as db:
            db.execute('BEGIN IMMEDIATE')
            row=db.execute("SELECT result FROM jobs WHERE id=? AND state='RUNNING'",(job_id,)).fetchone()
            if row is None:raise ValueError('Task not running')
            cur=db.execute('INSERT INTO analysis_receipts(job_id,record) VALUES(?,?)',(job_id,json.dumps(dict(record,acceptance_granted=False,scope='PRELIMINARY_ANALYSIS'),ensure_ascii=False)))
            if record.get('role')!='CHAT' and record.get('status')=='COMPLETED' and json.loads(record['text']).get('status')=='BLOCK':
                result=json.loads(row['result'])
                result['document_analysis']['roles'][record['role']]['block_seen']=True
                db.execute('UPDATE jobs SET result=? WHERE id=?',(json.dumps(result,ensure_ascii=False),job_id))
            return cur.lastrowid

    def analysis_receipts(self,session_id,job_id,*,offset=0,limit=50):
        identifier(session_id);identifier(job_id)
        if type(offset) is not int or offset<0 or type(limit) is not int or not 1<=limit<=50:raise ValueError('Invalid analysis window')
        with self.connection() as db:
            if db.execute('SELECT id FROM jobs WHERE id=? AND session_id=? AND parent_id IS NULL',(job_id,session_id)).fetchone() is None:raise ValueError('Analysis not found in conversation')
            rows=db.execute('SELECT seq,record FROM analysis_receipts WHERE job_id=? ORDER BY seq LIMIT ? OFFSET ?',(job_id,limit,offset)).fetchall()
            total=db.execute('SELECT count(*) FROM analysis_receipts WHERE job_id=?',(job_id,)).fetchone()[0]
        return dict(records=[dict(json.loads(r['record']),receipt_id=r['seq']) for r in rows],total=total,has_more=offset+len(rows)<total)

    def enqueue_extraction(self,session_id,file_id,backend):
        if not isinstance(backend,str) or backend not in {'native','docling'}:raise ValueError('Unknown extraction backend')
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
        if job['state'] not in {'FAILED','SUCCEEDED'} or not run or run.get('budget_exhausted'):
            raise ValueError('Task cannot be resumed')
        if run.get('cycle_complete') and not run.get('failed_pages'):raise ValueError('Extraction cycle already complete')
        from .core_plan import verify_originals
        f=self.get_file(job['file_ids'][0]);verify_originals([f])
        if f['sha256']!=run.get('source_sha256') or f['session_id']!=session_id:raise ValueError('Original identity changed')
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

    def checkpoint(self,job_id,result):
        identifier(job_id)
        if not isinstance(result,dict) or not isinstance(result.get('text'),str):raise ValueError('Invalid progress result')
        result=dict(result,engineering_status='UNCERTAINTY',evidentiary_status='NOT_EVIDENCE',acceptance_granted=False,final_audit='NOT_RUN')
        with self.connection() as db:
            previous=db.execute('SELECT result FROM jobs WHERE id=?',(job_id,)).fetchone()
            prior=json.loads(previous['result']) if previous and previous['result'] else {}
            if 'document_analysis' in prior:result['document_analysis']=prior['document_analysis']
            if db.execute("UPDATE jobs SET result=?,updated=? WHERE id=? AND state IN ('RUNNING','ATTACHMENT')",(json.dumps(result,ensure_ascii=False),time.time(),job_id)).rowcount!=1:raise ValueError('Task is not running')

    def finish(self,job_id,result):
        identifier(job_id)
        if not isinstance(result,dict) or not isinstance(result.get('text'),str) or not result['text'].strip():raise ValueError('Nonempty model response required')
        result=dict(result,engineering_status='UNCERTAINTY',evidentiary_status='NOT_EVIDENCE',acceptance_granted=False,final_audit='NOT_RUN')
        with self.connection() as db:
            db.execute('BEGIN IMMEDIATE')
            r=db.execute("SELECT * FROM jobs WHERE id=? AND state='RUNNING'",(job_id,)).fetchone()
            if r is None:raise ValueError('Task is not running')
            prior=json.loads(r['result']) if r['result'] else {}
            if 'document_analysis' in prior:result['document_analysis']=prior['document_analysis']
            now=time.time();db.execute("UPDATE jobs SET state='SUCCEEDED',result=?,updated=? WHERE id=?",(json.dumps(result,ensure_ascii=False),now,job_id))
            db.execute('INSERT INTO messages(session_id,role,content,created) VALUES(?,?,?,?)',(r['session_id'],'assistant',result['text'],now))

    def fail(self,job_id,error):
        identifier(job_id)
        with self.connection() as db:
            db.execute('BEGIN IMMEDIATE')
            row=db.execute("SELECT result FROM jobs WHERE id=? AND state IN ('RUNNING','ATTACHMENT')",(job_id,)).fetchone()
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
            db.execute("UPDATE jobs SET state='FAILED',error=?,result=?,updated=? WHERE id=?",(str(error)[:500],json.dumps(result,ensure_ascii=False) if result else None,time.time(),job_id))

    def interrupt_running(self):
        # The caller must own the exclusive data-directory lock.
        with self.connection() as db:ids=[r['id'] for r in db.execute("SELECT id FROM jobs WHERE state IN ('RUNNING','ATTACHMENT')")]
        for job_id in ids:self.fail(job_id,'Execution interrupted; submit again to retry.')

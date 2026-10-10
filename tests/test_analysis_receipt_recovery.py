"""Regression: resumed jobs never silently reuse uncommitted model responses."""
import json
import sqlite3
import unittest
from unittest.mock import MagicMock

from engineering.local_app.store import Store
from engineering.local_app.automatic_analysis import DocumentModel


class ReceiptRecoveryTests(unittest.TestCase):
    def test_stale_running_receipt_becomes_interrupted_and_is_idempotent(self):
        db=sqlite3.connect(':memory:')
        db.row_factory=sqlite3.Row
        db.execute("CREATE TABLE jobs(id TEXT PRIMARY KEY,state TEXT)")
        db.execute("CREATE TABLE analysis_receipts(seq INTEGER PRIMARY KEY,job_id TEXT,record TEXT)")
        db.execute("INSERT INTO jobs VALUES('j','RUNNING')")
        db.execute("INSERT INTO analysis_receipts VALUES(1,'j',?)",
                   (json.dumps(dict(status='RUNNING',attempted=True,part_key='a',role='CHAT',kind='SOURCE_PART')),))
        db.execute("INSERT INTO analysis_receipts VALUES(2,'j',?)",
                   (json.dumps(dict(status='COMPLETED',attempted=True,part_key='b',text='verified')),))
        db.commit()
        store=Store.__new__(Store)
        store.connection=lambda: db
        self.assertEqual(store.reconcile_interrupted_analysis_receipts('j'),1)
        self.assertEqual(store.reconcile_interrupted_analysis_receipts('j'),0)
        values=[json.loads(x[0]) for x in db.execute('SELECT record FROM analysis_receipts ORDER BY seq')]
        self.assertEqual([x['status'] for x in values],['INTERRUPTED','COMPLETED'])
        self.assertTrue(values[0]['attempted'])
        self.assertNotIn('text',values[0])
        self.assertFalse(values[0]['acceptance_granted'])
        self.assertEqual(values[1]['text'],'verified')
        db.execute("UPDATE jobs SET state='FAILED' WHERE id='j'")
        db.commit()
        with self.assertRaises(ValueError):
            store.reconcile_interrupted_analysis_receipts('j')
        db.close()

    def test_document_model_reports_interrupted_attempt_without_reuse(self):
        store=MagicMock()
        store.reconcile_interrupted_analysis_receipts.return_value=1
        store.analysis_receipts.return_value=dict(records=[
            dict(status='INTERRUPTED',attempted=True,part_key='x',receipt_id=1),
            dict(status='COMPLETED',attempted=True,part_key='y',receipt_id=2,elapsed_seconds=3)],
            has_more=False)
        report={}
        model=DocumentModel(store,dict(id='j',session_id='s'),None,None,
                            dict(pdf_ids=set(),report=report))
        store.reconcile_interrupted_analysis_receipts.assert_called_once_with('j')
        self.assertEqual(model.attempts,2)
        self.assertEqual(report['interrupted_calls'],1)
        self.assertTrue(report['model_elapsed_estimated'])
        self.assertEqual(report['model_elapsed_seconds'],183)


    def test_finish_rejects_unfinished_receipt(self):
        db=sqlite3.connect(':memory:')
        db.row_factory=sqlite3.Row
        db.execute("CREATE TABLE jobs(id TEXT PRIMARY KEY,state TEXT,error TEXT,result TEXT,session_id TEXT,updated REAL)")
        db.execute("CREATE TABLE analysis_receipts(seq INTEGER PRIMARY KEY,job_id TEXT,record TEXT)")
        db.execute("CREATE TABLE messages(session_id TEXT,role TEXT,content TEXT,created REAL)")
        db.execute("INSERT INTO jobs(id,state,result,session_id) VALUES('00000000-0000-4000-8000-000000000001','RUNNING',?,'s')",
                   (json.dumps({'document_analysis':{'stage':'COMPLETED'}}),))
        db.execute("INSERT INTO analysis_receipts VALUES(1,'00000000-0000-4000-8000-000000000001',?)",
                   (json.dumps({'status':'RUNNING','attempted':True}),))
        db.commit()
        store=Store.__new__(Store)
        store.connection=lambda: db
        with self.assertRaisesRegex(ValueError,'Incomplete model receipt'):
            store.finish('00000000-0000-4000-8000-000000000001',{'text':'draft'})
        db.rollback()
        self.assertEqual(db.execute("SELECT state FROM jobs WHERE id='00000000-0000-4000-8000-000000000001'").fetchone()[0],'RUNNING')
        db.execute("UPDATE analysis_receipts SET record=? WHERE seq=1",(json.dumps({'status':'INTERRUPTED'}),))
        db.commit()
        store.finish('00000000-0000-4000-8000-000000000001',{'text':'draft'})
        self.assertEqual(db.execute("SELECT state FROM jobs WHERE id='00000000-0000-4000-8000-000000000001'").fetchone()[0],'SUCCEEDED')
        db.close()


if __name__=='__main__':
    unittest.main()

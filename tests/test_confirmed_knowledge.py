"""Controlled lifecycle fixtures are software tests, never a real ACCEPTED case."""
import tempfile
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch
from engineering.local_app.store import Store, ReviewConflict

class ConfirmedKnowledgeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.store=Store(self.root/'data')
        (self.store.root/'engineering-verification.key').write_bytes(b'0123456789abcdef0123456789abcdef')
        self.sid=self.store.create_session()['id'];self.target=self.store.create_session()['id']
        self.audit_id=str(uuid.uuid4());self.case_id=str(uuid.uuid4());self.eid=str(uuid.uuid4())
        # Only the unavoidable authoritative accepted-report dependency is mocked.
        # These identifiers are not persisted fake engineering acceptance.
        self.audit=dict(id=self.audit_id,case_id=self.case_id,case_sha256='a'*64,audit_sha256='b'*64,
                        effective_acceptance_granted=True, fresh=True, effective_decision='ACCEPTED')
        self.authority=dict(status='ACCEPTED',acceptance_granted=True,current_fresh=True,
                            current_audit_id=self.audit_id,audits=[self.audit])
        self.case=dict(id=self.case_id,current=True,case_sha256='a'*64,evidence=[dict(
            id=self.eid,candidate_id=self.eid,statement='Controlled checked statement',quote='Controlled source quotation',
            engineering_verified=True,source_sha256='c'*64)])
        self.patches=[patch('engineering.local_app.final_audit.report',return_value=self.authority),
                      patch('engineering.local_app.real_case.report',return_value=dict(cases=[self.case]))]
        for p in self.patches:p.start();self.addCleanup(p.stop)
    def module(self):
        from engineering.local_app import knowledge
        return knowledge
    def promote(self,**kw):
        args=dict(expected_audit_id=self.audit_id,title='Controlled reference',evidence_ids=[self.eid],actor='test reviewer')
        args.update(kw)
        return self.module().promote(self.store,self.sid,**args)
    def test_module_and_blocked_promotion_are_fail_closed(self):
        self.authority.update(status='BLOCK',acceptance_granted=False)
        with self.assertRaises(ValueError):self.promote()
        self.assertEqual(self.module().report(self.store,self.sid)['records'],[])
    def test_explicit_scope_recall_never_accepts_target(self):
        row=self.promote(scope_session_ids=[self.sid,self.target])
        recalled=self.module().recall(self.store,self.target,query='checked')['records']
        self.assertEqual(recalled[0]['id'],row['id']);self.assertEqual(row['revision'],1)
        self.assertEqual(recalled[0]['evidentiary_status'],'NOT_EVIDENCE')
        self.assertFalse(recalled[0]['acceptance_granted']);self.assertTrue(recalled[0]['mandatory_reverification'])
        other=self.store.create_session()['id'];self.assertEqual(self.module().recall(self.store,other)['records'],[])
    def test_default_scope_is_source_only_and_invalid_scope_is_rejected(self):
        self.promote();self.assertEqual(self.module().recall(self.store,self.target)['records'],[])
        with self.assertRaises(ValueError):self.promote(scope_session_ids=[str(uuid.uuid4())])
    def test_forged_or_stale_audit_and_wrong_evidence_are_rejected(self):
        with self.assertRaises(ValueError):self.promote(expected_audit_id=str(uuid.uuid4()))
        with self.assertRaises(ValueError):self.promote(evidence_ids=[str(uuid.uuid4())])
        self.authority['current_fresh']=False
        with self.assertRaises(ValueError):self.promote()
    def test_live_origin_change_excludes_recall(self):
        self.promote();self.audit['audit_sha256']='d'*64
        self.assertEqual(self.module().recall(self.store,self.sid)['records'],[])
    def test_revision_supersession_and_revoke(self):
        first=self.promote();second=self.promote(knowledge_id=first['id'],expected_revision=1,title='Revised')
        self.assertEqual(second['revision'],2)
        with self.assertRaises(ReviewConflict):self.promote(knowledge_id=first['id'],expected_revision=1)
        revoked=self.module().revoke(self.store,self.sid,first['id'],expected_revision=2,actor='reviewer',reason='Withdrawn')
        self.assertEqual(revoked['revision'],3);self.assertEqual(self.module().recall(self.store,self.sid)['records'],[])
        history=self.module().export(self.store,self.sid)['records'];self.assertEqual(len(history),3)
    def test_delete_redacts_exports_without_mutating_revision_history(self):
        first=self.promote()
        deleted=self.module().delete(self.store,self.sid,first['id'],expected_revision=1,actor='reviewer',reason='Remove content')
        self.assertEqual(deleted['state'],'DELETED');self.assertEqual(self.module().recall(self.store,self.sid)['records'],[])
        exported=self.module().export(self.store,self.sid)['records']
        self.assertEqual([x['revision'] for x in exported],[1,2])
        self.assertTrue(all(x['title']=='' and x['evidence']==[] for x in exported))
        with self.assertRaises(ValueError):self.promote(knowledge_id=first['id'],expected_revision=2)
    def test_wrong_owner_cannot_change_or_read_lifecycle(self):
        first=self.promote(scope_session_ids=[self.target])
        with self.assertRaises(ValueError):self.module().revoke(self.store,self.target,first['id'],expected_revision=1,actor='reviewer',reason='Wrong owner')
        self.assertEqual(self.module().report(self.store,self.target)['records'],[])
    def test_missing_key_blocks_promotion_recall_and_export_but_allows_delete(self):
        module=self.module();row=self.promote()
        (self.store.root/'engineering-verification.key').unlink()
        with self.assertRaises(ValueError):self.promote()
        self.assertEqual(module.recall(self.store,self.sid)['records'],[])
        with self.assertRaises(ValueError):module.export(self.store,self.sid)
        deleted=module.delete(self.store,self.sid,row['id'],expected_revision=1,actor='reviewer',reason='Key lost; remove content')
        self.assertEqual(deleted['state'],'DELETED')
        with self.store.connection() as db:self.assertEqual(db.execute('SELECT count(*) FROM knowledge_content').fetchone()[0],0)
    def test_corrupt_key_blocks_promotion_and_recall(self):
        module=self.module();self.promote()
        (self.store.root/'engineering-verification.key').write_bytes(b'invalid')
        with self.assertRaises(ValueError):self.promote()
        self.assertEqual(module.recall(self.store,self.sid)['records'],[])
    def test_export_rejects_unauthenticated_metadata(self):
        import json
        module=self.module();row=self.promote()
        with self.store.connection() as db:
            meta=json.loads(db.execute('SELECT record FROM knowledge_revisions WHERE id=?',(row['id'],)).fetchone()[0])
            meta['actor']='Altered metadata'
            db.execute('UPDATE knowledge_revisions SET record=? WHERE id=?',(json.dumps(meta),row['id']))
        with self.assertRaises(ValueError):module.export(self.store,self.sid)
    def test_valid_mac_cannot_substitute_for_exact_accepted_evidence(self):
        import json
        module=self.module();row=self.promote(scope_session_ids=[self.target])
        with self.store.connection() as db:
            payload=json.loads(db.execute('SELECT content FROM knowledge_content WHERE id=?',(row['id'],)).fetchone()[0])
            payload['evidence'][0]['statement']='Valid storage MAC, unsupported engineering statement'
            meta=json.loads(db.execute('SELECT record FROM knowledge_revisions WHERE id=?',(row['id'],)).fetchone()[0])
            meta['content_sha256']=module._digest(payload)
            # Deliberately sign a controlled wrong storage payload to ensure
            # recall compares the authoritative case, independently of its MAC.
            meta['metadata_mac']=module._metadata_mac(meta,self.store.verification_key())
            db.execute('UPDATE knowledge_content SET content=? WHERE id=?',(json.dumps(payload),row['id']))
            db.execute('UPDATE knowledge_revisions SET record=? WHERE id=?',(json.dumps(meta),row['id']))
        self.assertEqual(module.recall(self.store,self.target)['records'],[])
    def test_unsigned_scope_change_cannot_leak_reference_to_target(self):
        import json
        module=self.module();row=self.promote()  # Source session only.
        with self.store.connection() as db:
            meta=json.loads(db.execute('SELECT record FROM knowledge_revisions WHERE id=?',(row['id'],)).fetchone()[0])
            meta['scope_session_ids'].append(self.target)
            db.execute('UPDATE knowledge_revisions SET record=? WHERE id=?',(json.dumps(meta),row['id']))
        self.assertEqual(module.recall(self.store,self.target)['records'],[])
    def test_recomputed_payload_digest_cannot_confirm_changed_evidence(self):
        import json
        module=self.module();row=self.promote(scope_session_ids=[self.target])
        with self.store.connection() as db:
            payload=json.loads(db.execute('SELECT content FROM knowledge_content WHERE id=?',(row['id'],)).fetchone()[0])
            payload['evidence'][0]['statement']='Forged confirmed statement'
            meta=json.loads(db.execute('SELECT record FROM knowledge_revisions WHERE id=?',(row['id'],)).fetchone()[0])
            meta['content_sha256']=module._digest(payload)
            db.execute('UPDATE knowledge_content SET content=? WHERE id=?',(json.dumps(payload),row['id']))
            db.execute('UPDATE knowledge_revisions SET record=? WHERE id=?',(json.dumps(meta),row['id']))
        self.assertEqual(module.recall(self.store,self.target)['records'],[])
    def test_duplicate_revoke_is_rejected_without_another_revision(self):
        first=self.promote()
        self.module().revoke(self.store,self.sid,first['id'],expected_revision=1,actor='reviewer',reason='Withdraw')
        with self.assertRaises(ValueError):self.module().revoke(self.store,self.sid,first['id'],expected_revision=2,actor='reviewer',reason='Repeat')
        self.assertEqual(self.module().report(self.store,self.sid)['history_count'],2)
    def test_promotion_quota_reserves_complete_withdrawal_history(self):
        module=self.module()
        with patch.object(module,'MAX_PROMOTIONS',2,create=True),patch.object(module,'MAX_HISTORY',6,create=True):
            first=self.promote()
            module.revoke(self.store,self.sid,first['id'],expected_revision=1,actor='reviewer',reason='Withdraw first')
            second=self.promote(knowledge_id=first['id'],expected_revision=2)
            with self.assertRaises(ValueError):self.promote()
            module.revoke(self.store,self.sid,first['id'],expected_revision=3,actor='reviewer',reason='Withdraw renewed')
            deleted=module.delete(self.store,self.sid,first['id'],expected_revision=4,actor='reviewer',reason='Remove')
            self.assertEqual(deleted['revision'],5)
            self.assertEqual(len(module.export(self.store,self.sid)['records']),5)
            self.assertEqual(module.recall(self.store,self.sid)['records'],[])
    def test_full_quota_allows_every_item_to_be_revoked_and_deleted(self):
        module=self.module()
        with patch.object(module,'MAX_PROMOTIONS',2,create=True),patch.object(module,'MAX_HISTORY',6,create=True):
            rows=[self.promote(),self.promote()]
            with self.assertRaises(ValueError):self.promote()
            for row in rows:
                module.revoke(self.store,self.sid,row['id'],expected_revision=1,actor='reviewer',reason='Withdraw')
                module.delete(self.store,self.sid,row['id'],expected_revision=2,actor='reviewer',reason='Remove')
            self.assertEqual(len(module.export(self.store,self.sid)['records']),6)
            self.assertEqual(module.report(self.store,self.sid)['history_count'],6)
    def test_corrupt_other_source_cannot_disable_healthy_scoped_recall(self):
        module=self.module();healthy=self.promote(scope_session_ids=[self.target])
        other=self.store.create_session()['id']
        self.authority['current_audit_id']=self.audit_id
        bad=module.promote(self.store,other,expected_audit_id=self.audit_id,title='Other source',evidence_ids=[self.eid],actor='reviewer')
        with self.store.connection() as db:db.execute('DELETE FROM knowledge_content WHERE id=?',(bad['id'],))
        recalled=module.recall(self.store,self.target)
        self.assertEqual([row['id'] for row in recalled['records']],[healthy['id']])
        self.assertEqual(recalled['blocked_source_count'],1)
    def test_invalid_other_metadata_type_cannot_disable_healthy_recall(self):
        module=self.module();healthy=self.promote(scope_session_ids=[self.target]);other=self.store.create_session()['id']
        bad=module.promote(self.store,other,expected_audit_id=self.audit_id,title='Other source',evidence_ids=[self.eid],actor='reviewer')
        with self.store.connection() as db:db.execute("UPDATE knowledge_revisions SET record='[]' WHERE id=?",(bad['id'],))
        self.assertEqual([row['id'] for row in module.recall(self.store,self.target)['records']],[healthy['id']])
    def test_oversized_other_history_cannot_disable_healthy_recall(self):
        module=self.module();healthy=self.promote(scope_session_ids=[self.target]);other=self.store.create_session()['id']
        import json
        bad=module.promote(self.store,other,expected_audit_id=self.audit_id,title='Other source',evidence_ids=[self.eid],actor='reviewer')
        with self.store.connection() as db:
            # Simulate an old or damaged database exceeding the supported bound.
            for revision in range(2,8):
                row=dict(bad,revision=revision,state='REVOKED');row.pop('title');row.pop('evidence')
                db.execute('INSERT INTO knowledge_revisions VALUES(?,?,?,?)',(row['id'],revision,other,json.dumps(row)))
        with patch.object(module,'MAX_HISTORY',6,create=True),patch.object(module,'MAX_RECORDS',6):
            recalled=module.recall(self.store,self.target)
            self.assertEqual([row['id'] for row in recalled['records']],[healthy['id']])
    def test_malformed_scope_and_evidence_raise_validation_errors(self):
        with self.assertRaises(ValueError):self.promote(evidence_ids=[{}])
        with self.assertRaises(ValueError):self.promote(scope_session_ids=[{}])
    def test_missing_active_content_fails_closed(self):
        first=self.promote()
        with self.store.connection() as db:db.execute('DELETE FROM knowledge_content WHERE id=?',(first['id'],))
        self.assertEqual(self.module().recall(self.store,self.sid)['records'],[])
        with self.assertRaises(ValueError):self.module().report(self.store,self.sid)
    def test_actual_unaccepted_session_cannot_train_memory(self):
        for p in self.patches:p.stop()
        with self.assertRaises(ValueError):self.promote()
        self.assertEqual(self.module().report(self.store,self.sid)['records'],[])
    def test_deleted_payload_is_absent_from_database(self):
        first=self.promote()
        self.module().delete(self.store,self.sid,first['id'],expected_revision=1,actor='reviewer',reason='Remove')
        with self.store.connection() as db:
            self.assertEqual(db.execute('SELECT count(*) FROM knowledge_content WHERE id=?',(first['id'],)).fetchone()[0],0)
            self.assertEqual(db.execute('SELECT count(*) FROM knowledge_revisions WHERE id=?',(first['id'],)).fetchone()[0],2)
    def test_backup_restore_preserves_lifecycle(self):
        first=self.promote();self.module().revoke(self.store,self.sid,first['id'],expected_revision=1,actor='reviewer',reason='Withdrawn')
        other=self.promote();self.module().delete(self.store,self.sid,other['id'],expected_revision=1,actor='reviewer',reason='Remove')
        from engineering.local_app.backup import create_backup,restore_backup
        archive=self.root/'backup.zip';create_backup(self.store.root,archive);restore_backup(archive,self.root/'restored')
        restored=Store(self.root/'restored')
        self.assertEqual(self.module().export(restored,self.sid),self.module().export(self.store,self.sid))
        self.assertEqual(self.module().recall(restored,self.sid)['records'],[])

class SignedFinalAuditKnowledgeIntegrationTests(unittest.TestCase):
    """Production issuer/audit/memory over controlled PROJECT plaintext inputs.

    No mocked authority, manually signed case, real-object acceptance or actual
    measurement is involved. Source corruption affects only temporary fixtures.
    """
    def test_real_final_audit_authority_rechecks_signed_origin_and_latest_revision(self):
        import tests.test_engineering_verification as fixtures
        from engineering.local_app import knowledge,final_audit
        from engineering.local_app.real_case import build
        setup=fixtures.EngineeringVerificationTests();setup.setUp();self.addCleanup(setup.doCleanups)
        store=setup.store;sid=setup.sid;job,tor_file=setup.setup_reviewed_core();target=store.create_session()['id']
        for role in job['result']['core_run']['results']:setup.issue(subject_kind='SPECIALIST',subject_id=job['id']+':'+role['agent'])
        case=build(store,sid,job_id=job['id'],expected_revision=0,manifest={'TOR':[tor_file],'REPORT':[setup.file['id']]})
        audit=final_audit.build(store,sid,case_id=case['id'],expected_revision=0)
        authoritative=final_audit.report(store,sid);eid=setup.candidate['id']
        self.assertEqual(authoritative['status'],'ACCEPTED');self.assertEqual(authoritative['current_audit_id'],audit['id'])
        self.assertEqual(authoritative['review_scope'],'PROJECT_PLAINTEXT_REPORT_REVIEW_ONLY');self.assertFalse(authoritative['actual_structure_verified'])
        row=knowledge.promote(store,sid,expected_audit_id=audit['id'],title='Controlled PROJECT reference',evidence_ids=[eid],scope_session_ids=[target],actor='fixture reviewer')
        recalled=knowledge.recall(store,target)['records']
        self.assertEqual(recalled[0]['evidence'],[item for item in case['evidence'] if item['candidate_id']==eid])
        self.assertEqual(recalled[0]['evidence'][0]['data_class'],'P');self.assertEqual(recalled[0]['audit_id'],audit['id'])
        self.assertEqual(recalled[0]['origin_review_scope'],'PROJECT_PLAINTEXT_REPORT_REVIEW_ONLY');self.assertFalse(recalled[0]['origin_actual_structure_verified'])
        self.assertFalse(recalled[0]['acceptance_granted']);self.assertTrue(recalled[0]['mandatory_reverification'])
        source=Path(store.get_file(setup.file['id'])['path']);original=source.read_bytes();source.write_bytes(b'Controlled source corruption')
        self.assertEqual(final_audit.report(store,sid)['status'],'BLOCK');self.assertEqual(knowledge.recall(store,target)['records'],[])
        with self.assertRaises(ValueError):knowledge.promote(store,sid,expected_audit_id=audit['id'],title='Invalid',evidence_ids=[eid],actor='fixture')
        blocked=final_audit.build(store,sid,case_id=case['id'],expected_revision=1);self.assertEqual(blocked['decision'],'BLOCK')
        source.write_bytes(original);self.assertEqual(final_audit.report(store,sid)['status'],'BLOCK')
        renewed=final_audit.build(store,sid,case_id=case['id'],expected_revision=2)
        self.assertEqual(final_audit.report(store,sid)['current_audit_id'],renewed['id']);self.assertEqual([item['revision'] for item in store.final_audit_state(sid)],[1,2,3])
        self.assertEqual(knowledge.recall(store,target)['records'],[])
        with self.assertRaises(ReviewConflict):knowledge.promote(store,sid,expected_audit_id=audit['id'],title='Stale',evidence_ids=[eid],actor='fixture')
        revised=knowledge.promote(store,sid,expected_audit_id=renewed['id'],title='Renewed PROJECT reference',evidence_ids=[eid],scope_session_ids=[target],actor='fixture',knowledge_id=row['id'],expected_revision=1)
        self.assertEqual(revised['revision'],2);self.assertEqual(knowledge.recall(store,target)['records'][0]['audit_id'],renewed['id'])

if __name__=='__main__':unittest.main()

"""Local responsible-review issuance, distinct from model/import assertions."""
import tempfile
import unittest
from pathlib import Path


class EngineeringVerificationTests(unittest.TestCase):
    def setUp(self):
        from engineering.local_app.store import Store
        from engineering.local_app.files import preserve_file
        from engineering.local_app.evidence import register
        from engineering.local_app.review import record_review
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.store=Store(Path(self.tmp.name));self.sid=self.store.create_session()['id']
        self.file=preserve_file(self.store,self.sid,'source.txt',b'Height: 4 m. Document declaration only.')
        self.candidate=register(self.store,self.sid,file_id=self.file['id'],quote='Height: 4 m.',statement='Declared height',data_class='P')
        record_review(self.store,self.sid,self.candidate['id'],expected_revision=0,decision='SOURCE_CONFIRMED',note='Exact source quotation',actor='Source reader')

    def provision(self):
        from engineering.local_app.verification import provision_key
        return provision_key(self.store,review_intent='PROVISION_LOCAL_REVIEW_AUTHORITY')

    def issue(self,**changes):
        from engineering.local_app.verification import issue_verification,review_subject
        kind=changes.get('subject_kind','EVIDENCE');subject_id=changes.get('subject_id',self.candidate['id'])
        state=review_subject(self.store,self.sid,kind,subject_id)
        request=dict(subject_kind=kind,subject_id=subject_id,
            expected_revision=state['expected_revision'],
            decision='ACCEPTED',reviewer='Responsible local reviewer',method='Exact quotation and PROJECT data-class review',
            source_refs=state['source_refs'],reason='Accepted only as the document declaration, not a measured actual height.',
            review_intent='RESPONSIBLE_ENGINEERING_REVIEW')
        request.update(changes)
        return issue_verification(self.store,self.sid,**request)

    def test_missing_key_never_mints_or_grants_acceptance(self):
        with self.assertRaises(ValueError):self.issue()
        self.assertIsNone(self.store.verification_key())

    def test_explicit_review_issues_mac_bound_to_exact_source_and_class(self):
        from engineering.local_app.final_audit import _verified_record
        from engineering.local_app.verification import review_subject
        self.provision();self.issue()
        reviewed=review_subject(self.store,self.sid,'EVIDENCE',self.candidate['id'])['verified_subject']
        self.assertTrue(_verified_record(reviewed,self.store.verification_key()))
        self.assertTrue(reviewed['data_class_verified']);self.assertEqual(reviewed['data_class'],'P')

    def test_model_or_import_cannot_self_issue(self):
        self.provision()
        for intent in (None,'MODEL','IMPORT',True):
            with self.subTest(intent=intent),self.assertRaises(ValueError):self.issue(review_intent=intent)
        with self.assertRaises(ValueError):self.issue(subject_kind='MODEL_OUTPUT')

    def test_foreign_subject_wrong_revision_and_missing_refs_refused(self):
        self.provision()
        with self.assertRaises(ValueError):self.issue(expected_revision='0'*64)
        with self.assertRaises(ValueError):self.issue(source_refs=[])
        from engineering.local_app.verification import review_subject
        other=self.store.create_session()['id']
        with self.assertRaises(ValueError):review_subject(self.store,other,'EVIDENCE',self.candidate['id'])

    def test_source_or_review_change_revokes_overlay(self):
        from engineering.local_app.verification import review_subject
        from engineering.local_app.review import record_review
        self.provision();self.issue()
        record_review(self.store,self.sid,self.candidate['id'],expected_revision=1,decision='NEEDS_DATA',note='Further review required',actor='Second reviewer')
        self.assertIsNone(review_subject(self.store,self.sid,'EVIDENCE',self.candidate['id'])['verified_subject'])

    def test_revoke_is_append_only_and_key_loss_does_not_recreate_authority(self):
        from engineering.local_app.verification import review_subject
        self.provision();self.issue();self.issue(decision='REVOKED',reason='Review withdrawn')
        self.assertIsNone(review_subject(self.store,self.sid,'EVIDENCE',self.candidate['id'])['verified_subject'])
        with self.store.connection() as db:self.assertEqual(db.execute('SELECT count(*) FROM engineering_verifications').fetchone()[0],2)
        (self.store.root/'engineering-verification.key').unlink()
        with self.assertRaises(ValueError):self.provision()

    def test_unqualified_source_cannot_be_reviewed_into_acceptance(self):
        from engineering.local_app.review import record_review
        self.provision()
        record_review(self.store,self.sid,self.candidate['id'],expected_revision=1,decision='NEEDS_DATA',note='Insufficient original data',actor='Reader')
        with self.assertRaises(ValueError):self.issue()

    def test_original_bytes_change_invalidates_existing_review(self):
        from engineering.local_app.verification import review_subject
        self.provision();self.issue()
        Path(self.store.get_file(self.file['id'])['path']).write_bytes(b'Changed original')
        self.assertIsNone(review_subject(self.store,self.sid,'EVIDENCE',self.candidate['id'])['verified_subject'])

    def test_case_overlay_revalidates_and_never_upgrades_unsigned_candidate(self):
        from engineering.local_app.real_case import _selected_candidates
        rows=_selected_candidates(self.store,self.sid,self.store.snapshot(self.sid),[self.file['id']])
        self.assertNotIn('engineering_verified',rows[0])
        self.provision();self.issue()
        rows=_selected_candidates(self.store,self.sid,self.store.snapshot(self.sid),[self.file['id']])
        self.assertTrue(rows[0]['engineering_verified']);self.assertEqual(rows[0]['data_class'],'P')
        self.assertNotIn('engineering_verified',self.store.get_evidence(self.sid,self.candidate['id']))

    def test_tampered_journal_mac_is_not_a_valid_overlay(self):
        import json
        from engineering.local_app.verification import review_subject,revalidate_verification
        self.provision();event=self.issue()
        event['subject']['engineering_verification']['reviewer']='Forged reviewer'
        with self.store.connection() as db:db.execute('UPDATE engineering_verifications SET record=? WHERE id=?',(json.dumps(event),event['id']))
        self.assertIsNone(review_subject(self.store,self.sid,'EVIDENCE',self.candidate['id'])['verified_subject'])
        self.assertEqual(revalidate_verification(self.store,event)['status'],'BLOCK')

    def setup_plaintext_requirements(self):
        from engineering.local_app.files import preserve_file
        from engineering.local_app.evidence import register
        from engineering.local_app.review import record_review
        from engineering.local_app.requirements import create_set,assess
        text='Check the height declared in the supplied report.'
        tor=preserve_file(self.store,self.sid,'TOR.txt',text.encode())
        candidate=register(self.store,self.sid,file_id=tor['id'],quote=text,statement='Complete plaintext TOR',data_class='P')
        record_review(self.store,self.sid,candidate['id'],expected_revision=0,decision='SOURCE_CONFIRMED',note='Complete original text',actor='Reader')
        requirements=create_set(self.store,self.sid,text=text,source_evidence_ids=[candidate['id']])
        assess(self.store,self.sid,set_id=requirements['id'],requirement_id=requirements['requirements'][0]['id'],expected_revision=0,
            conclusion='The document declares 4 m; no actual measurement is claimed.',evidence_ids=[self.candidate['id']],relation='SUPPORTS',actor='Responsible reviewer')
        return requirements,candidate

    def test_requirements_need_all_verified_sources_and_complete_plaintext_tor(self):
        from engineering.local_app.requirements import report
        self.provision();requirements,tor=self.setup_plaintext_requirements()
        with self.assertRaises(ValueError):self.issue(subject_kind='REQUIREMENTS',subject_id=requirements['id'])
        self.issue();self.issue(subject_id=tor['id'])
        self.issue(subject_kind='REQUIREMENTS',subject_id=requirements['id'])
        result=report(self.store,self.sid)
        self.assertTrue(result['engineering_verified']);self.assertTrue(result['tor_transcription_verified'])
        self.assertEqual(result['requirements'][0]['status'],'ACCEPTED')

    def test_source_reverification_invalidates_dependent_requirements(self):
        from engineering.local_app.requirements import report
        self.provision();requirements,tor=self.setup_plaintext_requirements()
        self.issue();self.issue(subject_id=tor['id']);self.issue(subject_kind='REQUIREMENTS',subject_id=requirements['id'])
        self.issue(reason='Fresh review of the same source: prior dependent review must be repeated.')
        self.assertFalse(report(self.store,self.sid)['engineering_verified'])

    def test_quote_review_cannot_bypass_unqualified_measurement_class(self):
        from engineering.local_app.evidence import register
        from engineering.local_app.review import record_review
        self.provision()
        for data_class in ('F','M','T','C'):
            candidate=register(self.store,self.sid,file_id=self.file['id'],quote='Height: 4 m.',statement='Unqualified actual/test/calculation claim',data_class=data_class)
            record_review(self.store,self.sid,candidate['id'],expected_revision=0,decision='SOURCE_CONFIRMED',note='Only quotation checked',actor='Reader')
            with self.subTest(data_class=data_class),self.assertRaises(ValueError):self.issue(subject_id=candidate['id'])

    def test_analysis_context_changes_on_review_issuance_and_key_loss(self):
        from engineering.local_app.analysis_identity import context_identity
        self.provision();job=dict(session_id=self.sid,file_ids=[self.file['id']])
        before=context_identity(self.store,job);self.issue();after=context_identity(self.store,job)
        self.assertNotEqual(before,after)
        (self.store.root/'engineering-verification.key').unlink()
        self.assertNotEqual(after,context_identity(self.store,job))

    def test_persisted_analysis_identity_cannot_reuse_old_review_authority(self):
        from engineering.local_app.analysis_identity import identity
        self.provision();job=self.store.enqueue(self.sid,'Read project declaration',[self.file['id']])
        class Model:
            def checkpoint_identity(inner):return {'fixture':'stable-model-identity'}
        before=identity(self.store,job,Model())[1];self.issue();after=identity(self.store,job,Model())[1]
        self.assertNotEqual(before,after)

    def setup_reviewed_core(self):
        import json
        from engineering.local_app.worker import Worker
        self.provision();requirements,tor=self.setup_plaintext_requirements()
        self.issue();self.issue(subject_id=tor['id']);self.issue(subject_kind='REQUIREMENTS',subject_id=requirements['id'])
        source_id=self.candidate['id'];requirement_id=requirements['requirements'][0]['id']
        class Model:
            def chat(inner,messages):return json.dumps(dict(status='UNCERTAINTY',summary='Controlled PROJECT document review',observations=[dict(text='The supplied document declares height 4 m.',source_ids=[source_id],requirement_ids=[requirement_id],relation='SUPPORTS')],limitations=['PROJECT declarations only; no physical inspection.']))
        tor_file=self.store.get_evidence(self.sid,tor['id'])['file_id']
        job=self.store.enqueue(self.sid,'Check only the supplied PROJECT declaration against the complete plaintext TOR.',[self.file['id'],tor_file],mode='CORE_RUN',requested_checks=['report'])
        Worker(self.store,Model()).run_once()
        saved=next(row for row in self.store.snapshot(self.sid)['jobs'] if row['id']==job['id'])
        self.assertEqual(saved['state'],'SUCCEEDED',saved)
        return saved,tor_file

    def test_specialist_review_binds_current_core_and_final_case(self):
        from engineering.local_app.real_case import build
        from engineering.local_app.final_audit import build as audit_build
        job,tor_file=self.setup_reviewed_core()
        for role in job['result']['core_run']['results']:
            self.issue(subject_kind='SPECIALIST',subject_id=job['id']+':'+role['agent'],method='Controlled PROJECT role/source review')
        case=build(self.store,self.sid,job_id=job['id'],expected_revision=0,manifest={'TOR':[tor_file],'REPORT':[self.file['id']]})
        audit=audit_build(self.store,self.sid,case_id=case['id'],expected_revision=0)
        self.assertEqual(audit['decision'],'ACCEPTED',audit)
        self.assertTrue(audit['acceptance_granted'])

    def test_specialist_revocation_invalidates_case_and_audit(self):
        from engineering.local_app.real_case import build,report
        from engineering.local_app.final_audit import build as audit_build,acceptance_gate
        job,tor_file=self.setup_reviewed_core()
        for role in job['result']['core_run']['results']:self.issue(subject_kind='SPECIALIST',subject_id=job['id']+':'+role['agent'])
        case=build(self.store,self.sid,job_id=job['id'],expected_revision=0,manifest={'TOR':[tor_file],'REPORT':[self.file['id']]})
        audit_build(self.store,self.sid,case_id=case['id'],expected_revision=0)
        self.issue(subject_kind='SPECIALIST',subject_id=job['id']+':'+job['result']['core_run']['results'][0]['agent'],decision='REVOKED',reason='Controlled review withdrawal')
        self.assertFalse(report(self.store,self.sid)['current_fresh'])
        self.assertFalse(acceptance_gate(self.store,self.sid))

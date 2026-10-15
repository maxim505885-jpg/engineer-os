import json
import tempfile
import unittest
from pathlib import Path
from test_office_documents import docx,xlsx,Model
from engineering.local_app.store import Store
from engineering.local_app.files import preserve_file
from engineering.local_app.worker import Worker
from engineering.local_app.evidence import register
from engineering.local_app.review import record_review


class SourceBindingTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.store=Store(Path(self.temp.name));self.session=self.store.create_session()['id']

    def source(self,name='report.docx',data=None):
        f=preserve_file(self.store,self.session,name,data or docx());j=self.store.enqueue(self.session,'Read',[f['id']]);Worker(self.store,Model()).run_once()
        ref=self.store.analysis_receipts(self.session,j['id'])['records'][0]['refs'][0]
        return f,ref

    def candidate(self,f,ref,quote='Высота 4 м'):
        try:return register(self.store,self.session,file_id=f['id'],quote=quote,statement='Высота по источнику',source_job=ref['source_job'],logical_unit=ref['logical_unit'],data_class='P')
        except TypeError as e:self.fail('Office logical source binding unavailable: '+str(e))

    def confirm(self,candidate):
        return record_review(self.store,self.session,candidate['id'],expected_revision=0,decision='SOURCE_CONFIRMED',note='Цитата и абзац сверены',actor='Test')

    def test_docx_quote_location_confirmed_without_engineering_acceptance(self):
        f,ref=self.source();r=self.candidate(f,ref)
        self.assertEqual(r['source_match'],'MATCH');self.assertIsNone(r['page']);self.assertEqual(r['locator']['paragraph'],1)
        self.assertEqual(self.confirm(r)['scope'],'SOURCE_REVIEW_ONLY');self.assertFalse(r['acceptance_granted'])

    def test_foreign_unit_wrong_quote_and_changed_original_rejected(self):
        f,ref=self.source()
        with self.assertRaises(ValueError):self.candidate(f,ref,'Высота 8 м')
        other=self.store.create_session()['id']
        with self.assertRaises(ValueError):register(self.store,other,file_id=f['id'],quote='Высота 4 м',statement='Test',source_job=ref['source_job'],logical_unit=1)
        r=self.candidate(f,ref);Path(self.store.get_file(f['id'])['path']).write_bytes(b'changed')
        with self.assertRaises(ValueError):self.confirm(r)

    def test_repeated_quote_cannot_be_source_confirmed(self):
        f,ref=self.source(data=docx(text='Высота 4 м; Высота 4 м'));r=self.candidate(f,ref)
        self.assertFalse(r['source_confirmable'])
        with self.assertRaises(ValueError):self.confirm(r)

    def test_blocked_word_unit_remains_blocked_for_confirmation(self):
        f,ref=self.source(data=docx(text='Высота 4 м</w:t><w:drawing/><w:t>'))
        r=self.candidate(f,ref);self.assertFalse(r['source_confirmable'])
        with self.assertRaises(ValueError):self.confirm(r)

    def test_xlsx_cell_uses_original_address_and_exact_value(self):
        f,ref=self.source('table.xlsx',xlsx());r=self.candidate(f,ref,'Снег')
        self.assertEqual(r['locator']['cell'],'A1');self.assertEqual(r['locator']['sheet'],'Нагрузки');self.confirm(r)

    def test_tampered_checkpoint_text_rejected_even_if_quote_is_present(self):
        f,ref=self.source();record=self.store.extraction_page(self.session,ref['source_job'],1);record['blocks'][0]['text']='Высота 4 м fabricated'
        with self.store.connection() as db:db.execute('UPDATE extraction_pages SET record=? WHERE job_id=? AND page=1',(json.dumps(record),ref['source_job']))
        with self.assertRaises(ValueError):self.candidate(f,ref)

    def test_doc_derived_quote_cannot_confirm_original(self):
        import hashlib
        from unittest.mock import patch
        data=b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'+b'controlled';derived=docx()
        conversion=dict(original_sha256=hashlib.sha256(data).hexdigest(),derived_sha256=hashlib.sha256(derived).hexdigest(),scope='DERIVED_UNVERIFIED')
        with patch('engineering.local_app.office.convert_doc',return_value=(derived,conversion)):f,ref=self.source('report.doc',data)
        r=self.candidate(f,ref);self.assertEqual(r['source_binding']['scope'],'DERIVED_UNVERIFIED');self.assertFalse(r['source_confirmable'])
        from engineering.local_app.requirements import source_check
        current=self.store.snapshot(self.session)['evidence'][0];checked=source_check(self.store,self.session,current)
        self.assertIn('SOURCE_LOCATION_UNVERIFIED',checked['reasons']);self.assertNotIn('SOURCE_IDENTITY_OR_LOCATION_CHANGED',checked['reasons'])
        with self.assertRaises(ValueError):self.confirm(r)
        (self.store.root/'derived'/(ref['source_job']+'.docx')).write_bytes(docx(text='Changed'))
        with self.assertRaises(ValueError):self.candidate(f,ref)

    def test_original_bytes_read_are_hashed_even_when_selected_quote_unchanged(self):
        from unittest.mock import patch
        f,ref=self.source();path=Path(self.store.get_file(f['id'])['path']);original_read=Path.read_bytes
        def raced_read(p):return docx(extra='<w:p><w:r><w:t>Changed elsewhere</w:t></w:r></w:p>') if p==path else original_read(p)
        with patch.object(Path,'read_bytes',raced_read):
            with self.assertRaises(ValueError):self.candidate(f,ref)


class RequirementTests(unittest.TestCase):
    setUp=SourceBindingTests.setUp
    source=SourceBindingTests.source
    candidate=SourceBindingTests.candidate
    confirm=SourceBindingTests.confirm
    def api(self):
        try:from engineering.local_app import requirements
        except ImportError:self.fail('Durable ТЗ checklist and source gates unavailable')
        return requirements

    def setup_requirement(self):
        api=self.api();s=api.create_set(self.store,self.session,text='Проверить высоту\nПроверить нагрузки')
        return api,s,s['requirements'][0]['id']

    def assess(self,api,s,rid,candidates=(),relation='SUPPORTS',revision=0):
        return api.assess(self.store,self.session,set_id=s['id'],requirement_id=rid,expected_revision=revision,conclusion='Высота 4 м по источнику',evidence_ids=list(candidates),relation=relation)

    def test_checklist_and_history_survive_restart_with_unchecked_requirements(self):
        api,s,rid=self.setup_requirement();self.assess(api,s,rid)
        result=api.report(Store(self.store.root),self.session)
        self.assertEqual(len(result['requirements']),2);self.assertEqual(result['requirements'][0]['status'],'BLOCK')
        self.assertEqual(result['requirements'][1]['reasons'],['NOT_ASSESSED']);self.assertFalse(result['acceptance_granted'])

    def test_reviewed_quote_links_requirement_without_claiming_engineering_pass(self):
        api,s,rid=self.setup_requirement();f,ref=self.source();r=self.candidate(f,ref);self.confirm(r);self.assess(api,s,rid,[r['id']])
        row=api.report(self.store,self.session)['requirements'][0]
        self.assertEqual(row['traceability'],'SOURCE_LINKED');self.assertEqual(row['status'],'UNCERTAINTY')
        self.assertEqual(row['sources'][0]['quote'],'Высота 4 м');self.assertEqual(row['sources'][0]['data_class'],'P')
        self.assertEqual(row['sources'][0]['locator']['paragraph'],1)
        self.assertIn('ENGINEERING_VERIFICATION_REQUIRED',row['reasons']);self.assertFalse(row['acceptance_granted'])

    def test_later_rejection_invalidates_old_assessment_and_keeps_history(self):
        api,s,rid=self.setup_requirement();f,ref=self.source();r=self.candidate(f,ref);self.confirm(r);self.assess(api,s,rid,[r['id']])
        record_review(self.store,self.session,r['id'],expected_revision=1,decision='REJECTED',note='Источник пересмотрен',actor='Test')
        row=api.report(self.store,self.session)['requirements'][0];self.assertEqual(row['status'],'BLOCK');self.assertIn('SOURCE_REVIEW_CHANGED',row['reasons'])
        self.assertEqual(len(row['history']),1)

    def test_contradiction_is_visible_even_with_confirmed_quote(self):
        api,s,rid=self.setup_requirement();f,ref=self.source();r=self.candidate(f,ref);self.confirm(r);self.assess(api,s,rid,[r['id']],relation='CONTRADICTS')
        row=api.report(self.store,self.session)['requirements'][0];self.assertEqual(row['status'],'BLOCK');self.assertIn('DECLARED_CONTRADICTION',row['reasons'])

    def test_foreign_candidates_and_stale_revision_are_rejected(self):
        api,s,rid=self.setup_requirement();f,ref=self.source();r=self.candidate(f,ref)
        other=self.store.create_session()['id']
        with self.assertRaises(ValueError):api.assess(self.store,other,set_id=s['id'],requirement_id=rid,expected_revision=0,conclusion='Test',evidence_ids=[r['id']],relation='SUPPORTS')
        self.assess(api,s,rid,[r['id']])
        with self.assertRaises(ValueError):self.assess(api,s,rid,[r['id']])

    def test_missing_or_unselected_source_fails_closed(self):
        api,s,rid=self.setup_requirement();f,ref=self.source();r=self.candidate(f,ref);self.confirm(r);self.assess(api,s,rid,[r['id']])
        row=api.report(self.store,self.session,selected_files=[])['requirements'][0]
        self.assertEqual(row['status'],'BLOCK');self.assertIn('SOURCE_NOT_SELECTED',row['reasons'])
        Path(self.store.get_file(f['id'])['path']).write_bytes(b'changed')
        self.assertIn('SOURCE_IDENTITY_OR_LOCATION_CHANGED',api.report(self.store,self.session)['requirements'][0]['reasons'])

    def test_new_checklist_preserves_old_assessment_without_carrying_status(self):
        api,s,rid=self.setup_requirement();self.assess(api,s,rid)
        current=api.create_set(self.store,self.session,text='Другая задача')
        row=api.report(self.store,self.session)['requirements'][0];self.assertEqual(row['reasons'],['NOT_ASSESSED'])
        self.assertEqual(api.report(self.store,self.session)['set_id'],current['id'])

    def test_core_context_and_result_show_requirement_gates(self):
        api,s,rid=self.setup_requirement();f,ref=self.source();r=self.candidate(f,ref);self.confirm(r);self.assess(api,s,rid,[r['id']])
        job=self.store.enqueue(self.session,'Проверить по ТЗ',[f['id']],mode='CORE_RUN',requested_checks=['report']);model=Model();Worker(self.store,model).run_once()
        result=self.store.snapshot(self.session)['jobs'][0]['result']
        self.assertIn('requirements_report',result,'CORE result must retain deterministic checklist gates')
        self.assertIn('Проверить высоту',str(model.calls));self.assertIn('SOURCE_LINKED',str(model.calls))
        self.assertEqual(result['requirements_report']['requirements'][1]['status'],'BLOCK')

    def test_chat_sees_checklist_and_persists_source_gates(self):
        api,s,rid=self.setup_requirement();f,ref=self.source();self.store.enqueue(self.session,'Проверить по ТЗ',[f['id']]);model=Model();Worker(self.store,model).run_once()
        result=self.store.snapshot(self.session)['jobs'][0]['result']
        self.assertIn('requirements_report',result,'CHAT result must preserve requirements separately from model output')
        self.assertIn('Проверить нагрузки',str(model.calls));self.assertFalse(result['requirements_report']['acceptance_granted'])

    def test_requirement_change_invalidates_failed_analysis_resume(self):
        api,s,rid=self.setup_requirement();f=preserve_file(self.store,self.session,'test.docx',docx());job=self.store.enqueue(self.session,'Read',[f['id']]);Worker(self.store,Model(fail=1)).run_once()
        api.create_set(self.store,self.session,text='Другая проверка')
        with self.assertRaises(ValueError):self.store.resume_analysis(self.session,job['id'],Model())

    def test_requirement_edit_during_model_call_rejects_result(self):
        api,s,rid=self.setup_requirement();f=preserve_file(self.store,self.session,'test.docx',docx());job=self.store.enqueue(self.session,'Read',[f['id']])
        store=self.store;session=self.session
        class EditingModel(Model):
            def chat(self,messages):
                api.create_set(store,session,text='Изменено во время анализа')
                return super().chat(messages)
        Worker(self.store,EditingModel()).run_once()
        result=self.store.snapshot(self.session)['jobs'][0]
        self.assertEqual(result['state'],'FAILED','Changed ТЗ must not yield completed result')
        self.assertFalse(any(r['status']=='COMPLETED' for r in self.store.analysis_receipts(self.session,job['id'])['records']))

    def test_bare_file_reference_is_not_reviewed_evidence(self):
        api,s,rid=self.setup_requirement();f,ref=self.source()
        row=api.finding_gates(self.store,self.session,[dict(text='Высота 4 м',source_ids=[f['id']])],[f['id']])[0]
        self.assertEqual(row['status'],'BLOCK');self.assertIn('ORIGINAL_REFERENCE_ONLY',row['reasons'])

    def test_candidate_reference_preserves_source_gate_and_unverified_type(self):
        api,s,rid=self.setup_requirement();f,ref=self.source();r=self.candidate(f,ref);self.confirm(r)
        row=api.finding_gates(self.store,self.session,[dict(text='Высота 4 м',source_ids=[r['id']])],[f['id']])[0]
        self.assertEqual(row['traceability'],'SOURCE_LINKED');self.assertFalse(row['sources'][0]['data_class_verified'])
        self.assertFalse(row['acceptance_granted'])

    def test_core_candidate_context_keeps_office_locator_and_data_class(self):
        from engineering.local_app.core_run import source_context
        api,s,rid=self.setup_requirement();f,ref=self.source();r=self.candidate(f,ref)
        context,_=source_context(self.store,dict(session_id=self.session,file_ids=[f['id']]),[self.store.get_file(f['id'])])
        self.assertEqual(context['candidates'][0].get('locator'),{'kind':'paragraph','part':'word/document.xml','paragraph':1})
        self.assertEqual(context['candidates'][0].get('data_class'),'P')

    def test_unselected_requirement_source_review_change_rejects_chat(self):
        api,s,rid=self.setup_requirement();f,ref=self.source();r=self.candidate(f,ref);self.confirm(r);self.assess(api,s,rid,[r['id']])
        store=self.store;session=self.session
        class ReReviewModel(Model):
            def chat(self,messages):
                record_review(store,session,r['id'],expected_revision=1,decision='REJECTED',note='Пересмотр',actor='QA')
                return super().chat(messages)
        job=self.store.enqueue(self.session,'Проверить требования',[]);Worker(self.store,ReReviewModel()).run_once()
        result=self.store.snapshot(self.session)['jobs'][0];self.assertEqual(result['state'],'FAILED')

    def test_unselected_requirement_source_review_change_blocks_resume(self):
        api,s,rid=self.setup_requirement();f,ref=self.source();r=self.candidate(f,ref);self.confirm(r);self.assess(api,s,rid,[r['id']])
        selected=preserve_file(self.store,self.session,'other.docx',docx(text='Другой источник'));job=self.store.enqueue(self.session,'Проверить требования',[selected['id']]);Worker(self.store,Model(fail=1)).run_once()
        record_review(self.store,self.session,r['id'],expected_revision=1,decision='REJECTED',note='Пересмотр',actor='QA')
        with self.assertRaises(ValueError):self.store.resume_analysis(self.session,job['id'],Model())

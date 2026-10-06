import tempfile
import unittest
from pathlib import Path
from engineering.local_app.store import Store,ReviewConflict
from engineering.local_app.files import preserve_file
from engineering.local_app.evidence import register
from engineering.local_app.review import record_review


class DomainPacketTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.store=Store(Path(self.tmp.name));self.sid=self.store.create_session()['id']
        self.norm=preserve_file(self.store,self.sid,'norm.txt',b'TEST 2026 clause1 Limit 2.5 m')
        self.actual=preserve_file(self.store,self.sid,'actual.txt',b'Height 2500 mm')
        self.n=self.candidate(self.norm,'TEST 2026 clause1 Limit 2.5 m')
        self.a=self.candidate(self.actual,'Height 2500 mm')

    def module(self):
        try:from engineering.local_app import domain_packets
        except ImportError:self.fail('Source-bound domain packets unavailable')
        return domain_packets

    def candidate(self,f,q):
        r=register(self.store,self.sid,file_id=f['id'],quote=q,statement='Source statement')
        record_review(self.store,self.sid,r['id'],expected_revision=0,decision='SOURCE_CONFIRMED',note='Checked source',actor='Test')
        return r

    def packet(self):
        return dict(kind='NORMATIVE',chain=dict(document='TEST',edition='2026',scope='Scope declaration',clause='clause1',requirement='Limit 2.5 m',actual_condition='Height 2500 mm',comparison='Compare height',conclusion='Arithmetic matches'),norm_ids=[self.n['id']],actual_ids=[self.a['id']],quantities=dict(actual=dict(candidate_id=self.a['id'],value='2500',unit='mm',fragment='2500 mm'),limit=dict(candidate_id=self.n['id'],value='2.5',unit='m',fragment='2.5 m'),operator='<='))

    def save(self,p=None,revision=0):return self.module().save(self.store,self.sid,packet=p or self.packet(),expected_revision=revision)

    def report(self,selected=None):return self.module().report(self.store,self.sid,selected_files=selected)

    def test_bound_arithmetic_survives_restart_without_normative_acceptance(self):
        self.save();r=self.report()['packets'][0]
        self.assertTrue(r['arithmetic']['satisfied']);self.assertEqual(r['traceability'],'SOURCE_LINKED')
        self.assertEqual(r['status'],'BLOCK');self.assertFalse(r['acceptance_granted'])
        self.assertIn('NORMATIVE_APPLICABILITY_NOT_VERIFIED',r['reasons'])
        self.assertEqual(self.module().report(Store(self.store.root),self.sid),self.report())

    def test_changed_review_blocks_previous_packet(self):
        self.save();record_review(self.store,self.sid,self.a['id'],expected_revision=1,decision='REJECTED',note='Changed review',actor='Test')
        r=self.report()['packets'][0];self.assertEqual(r['traceability'],'NOT_ESTABLISHED')
        self.assertIn('SOURCE_REVIEW_CHANGED',r['reasons']);self.assertIsNone(r['arithmetic'])

    def test_revision_conflict_and_foreign_source_rejected(self):
        self.save()
        with self.assertRaises(ReviewConflict):self.save()
        other=self.store.create_session()['id']
        with self.assertRaises(ValueError):self.module().save(self.store,other,packet=self.packet(),expected_revision=0)
        self.assertEqual(self.module().report(self.store,other)['packets'],[])

    def test_quantity_cannot_borrow_unit_or_candidate_from_other_field(self):
        for field,value in [('unit','m'),('value','25'),('candidate_id',self.n['id'])]:
            p=self.packet();p['quantities']['actual'][field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):self.save(p)

    def test_unselected_or_changed_original_disables_arithmetic(self):
        self.save();r=self.report([self.norm['id']])['packets'][0]
        self.assertIn('SOURCE_NOT_SELECTED',r['reasons']);self.assertIsNone(r['arithmetic'])
        Path(self.store.get_file(self.actual['id'])['path']).write_bytes(b'changed')
        self.assertIn('SOURCE_IDENTITY_OR_LOCATION_CHANGED',self.report()['packets'][0]['reasons'])

    def test_calculation_roles_bound_but_solver_and_semantics_remain_open(self):
        from engineering.calculation.model_intake import CalculationArtifactRole
        p=dict(kind='CALCULATION',bindings=[dict(role=r.value,file_id=self.actual['id'],candidate_ids=[self.a['id']]) for r in CalculationArtifactRole])
        self.save(p);r=self.report()['packets'][0]
        self.assertEqual(r['intake']['missing_roles'],[]);self.assertEqual(r['intake']['status'],'READY_FOR_SEMANTIC_REVIEW')
        self.assertIn('SOLVER_NOT_RUN',r['reasons']);self.assertIn('CALCULATION_SEMANTICS_NOT_VERIFIED',r['reasons'])
        self.assertFalse(r['acceptance_granted'])

    def test_packet_change_and_unselected_dependencies_invalidate_context(self):
        from engineering.local_app.analysis_identity import context_identity
        job=dict(session_id=self.sid,file_ids=[self.norm['id']])
        before=context_identity(self.store,job);self.save();after=context_identity(self.store,job)
        self.assertNotEqual(before,after)
        record_review(self.store,self.sid,self.a['id'],expected_revision=1,decision='REJECTED',note='Changed',actor='Test')
        self.assertNotEqual(after,context_identity(self.store,job))

    def test_core_forwards_bound_arithmetic_to_audit_without_acceptance(self):
        import json
        from engineering.local_app.worker import Worker
        self.save();calls=[]
        class Model:
            def chat(inner,messages):
                calls.append(messages)
                return json.dumps(dict(status='UNCERTAINTY',summary='Draft',observations=[],limitations=[]))
        self.store.enqueue(self.sid,'Check',[self.norm['id'],self.actual['id']],mode='CORE_RUN',requested_checks=['normative'])
        Worker(self.store,Model()).run_once()
        result=self.store.snapshot(self.sid)['jobs'][0]['result']
        self.assertIn('domain_packets',result)
        self.assertTrue(result['domain_packets']['packets'][0]['arithmetic']['satisfied'])
        self.assertIn('actual_si',str(calls[-1]));self.assertEqual(result['engineering_status'],'BLOCK')

    def test_domain_packet_change_invalidates_resumable_identity(self):
        from engineering.local_app.analysis_identity import identity
        class Model:
            def checkpoint_identity(inner):return dict(model='test')
        job=self.store.enqueue(self.sid,'Check',[self.norm['id']],mode='CORE_RUN',requested_checks=['normative'])
        before=identity(self.store,job,Model())[1];self.save()
        self.assertNotEqual(before,identity(self.store,job,Model())[1])

    def test_russian_decimal_fragment_and_unit_preserved_before_arithmetic(self):
        f=preserve_file(self.store,self.sid,'decimal.txt','Высота 2,5 м'.encode());c=self.candidate(f,'Высота 2,5 м')
        p=self.packet();p['actual_ids']=[c['id']];p['chain']['actual_condition']='Высота 2,5 м'
        p['quantities']['actual']=dict(candidate_id=c['id'],value='2,5',unit='м',fragment='2,5 м')
        self.save(p);r=self.report()['packets'][0]
        self.assertTrue(r['arithmetic']['satisfied']);self.assertEqual(r['packet']['quantities']['actual']['fragment'],'2,5 м')

    def test_partial_numeric_unit_sign_exponent_or_power_tokens_rejected(self):
        for text in ['Height 12500 mm','Height -2500 mm','Height 0.2500 mm','Height 1e2500 mm','Height 2500 mm2','Height 2500 mm^2','Height 12 2500 mm']:
            f=preserve_file(self.store,self.sid,'token.txt',text.encode());c=self.candidate(f,text)
            p=self.packet();p['actual_ids']=[c['id']];p['chain']['actual_condition']=text;p['quantities']['actual']['candidate_id']=c['id']
            with self.subTest(text=text),self.assertRaises(ValueError):self.save(p)
        p=self.packet();p['quantities']['actual'].update(unit='m',fragment='2500 m')
        with self.assertRaises(ValueError):self.save(p)

    def test_quantity_must_belong_to_declared_chain_field(self):
        f=preserve_file(self.store,self.sid,'fields.txt',b'Height 12500 mm; Width 100 mm');c=self.candidate(f,'Height 12500 mm; Width 100 mm')
        p=self.packet();p['actual_ids']=[c['id']];p['chain']['actual_condition']='Height 12500 mm';p['quantities']['actual']=dict(candidate_id=c['id'],value='100',unit='mm',fragment='100 mm')
        with self.assertRaises(ValueError):self.save(p)

    def test_report_revalidates_quantity_binding(self):
        event=self.save();event['packet']['quantities']['actual'].update(value='500',fragment='500 mm')
        import json
        with self.store.connection() as db:db.execute('UPDATE domain_packets SET record=? WHERE id=?',(json.dumps(event),event['id']))
        r=self.report()['packets'][0];self.assertIsNone(r['arithmetic']);self.assertIn('QUANTITY_BINDING_INVALID',r['reasons'])

    def test_normative_authority_review_is_bound_but_not_acceptance(self):
        p=self.packet()
        p['authority_review']=dict(
            document='TEST',edition='2026',clause='clause1',
            authority='Controlled authority source',
            source_ref='authority:test:2026:clause1',
            applicability_basis='Scope was reviewed against the declared test case',
            decision='VERIFIED')
        self.save(p);r=self.report()['packets'][0]
        self.assertEqual(r['authority_review']['status'],'READY_FOR_EXPERT_APPLICABILITY_REVIEW')
        self.assertIn('AUTHORITY_RECEIPT_NOT_SELF_AUTHENTICATING',r['reasons'])
        self.assertIn('NORMATIVE_APPLICABILITY_NOT_VERIFIED',r['reasons'])
        self.assertEqual(r['status'],'BLOCK');self.assertFalse(r['acceptance_granted'])

    def test_normative_authority_identity_must_match_chain(self):
        p=self.packet()
        p['authority_review']=dict(
            document='OTHER',edition='2026',clause='clause1',
            authority='Controlled authority source',source_ref='authority:test',
            applicability_basis='Controlled basis',decision='VERIFIED')
        with self.assertRaises(ValueError):self.save(p)

    def test_complete_calculation_semantic_review_advances_only_to_solver_verification(self):
        from engineering.calculation.model_intake import CalculationArtifactRole
        bindings=[dict(role=r.value,file_id=self.actual['id'],candidate_ids=[self.a['id']]) for r in CalculationArtifactRole]
        semantic=[dict(role=r.value,statement='Controlled semantic statement',candidate_ids=[self.a['id']],
                       decision='VERIFIED',basis='Controlled source review basis') for r in CalculationArtifactRole]
        p=dict(kind='CALCULATION',bindings=bindings,semantic_reviews=semantic)
        self.save(p);r=self.report()['packets'][0]
        self.assertEqual(r['semantic_review']['status'],'READY_FOR_SOLVER_VERIFICATION')
        self.assertIn('SOLVER_EXECUTION_NOT_PROVEN',r['reasons'])
        self.assertIn('SOLVER_NOT_RUN',r['reasons'])
        self.assertEqual(r['status'],'BLOCK');self.assertFalse(r['acceptance_granted'])

    def test_calculation_semantic_review_cannot_borrow_other_role_source(self):
        from engineering.calculation.model_intake import CalculationArtifactRole
        other=preserve_file(self.store,self.sid,'other.txt',b'Other source')
        other_candidate=self.candidate(other,'Other source')
        bindings=[
            dict(role='MODEL',file_id=self.actual['id'],candidate_ids=[self.a['id']]),
            dict(role='GEOMETRY',file_id=other['id'],candidate_ids=[other_candidate['id']])]
        semantic=[dict(role='MODEL',statement='Model statement',candidate_ids=[other_candidate['id']],
                       decision='VERIFIED',basis='Wrong source')]
        with self.assertRaises(ValueError):
            self.save(dict(kind='CALCULATION',bindings=bindings,semantic_reviews=semantic))

    def test_calculation_exchange_and_solver_receipt_still_do_not_accept(self):
        from engineering.calculation.model_intake import CalculationArtifactRole
        bindings=[dict(role=r.value,file_id=self.actual['id'],candidate_ids=[self.a['id']]) for r in CalculationArtifactRole]
        semantic=[dict(role=r.value,statement='Controlled semantic statement',candidate_ids=[self.a['id']],
                       decision='VERIFIED',basis='Controlled source review basis') for r in CalculationArtifactRole]
        sha='a'*64
        exchange=dict(format='ENGINEER_OS_CALC_EXCHANGE',version=1,source_sha256=sha,sections=[
            dict(name='GEOMETRY',source_sha256=sha,records=[{'node':1}]),
            dict(name='MATERIALS_SECTIONS',source_sha256=sha,records=[{'material':'test'}]),
            dict(name='LOADS_COMBINATIONS',source_sha256=sha,records=[{'case':'LC1'}]),
            dict(name='SUPPORTS_RELEASES',source_sha256=sha,records=[{'node':1}]),
            dict(name='UNITS',source_sha256=sha,records=[{'length':'m'}]),
        ])
        receipt=dict(solver_name='TEST_SOLVER',solver_version='1.0',input_sha256='a'*64,
                     output_sha256='b'*64,log_sha256='c'*64,exit_code=0,
                     started_at='2026-10-06T20:00:00Z',finished_at='2026-10-06T20:01:00Z')
        self.save(dict(kind='CALCULATION',bindings=bindings,semantic_reviews=semantic,
                       exchange_manifest=exchange,solver_receipt=receipt))
        r=self.report()['packets'][0]
        self.assertEqual(r['exchange_review']['status'],'READY_FOR_SEMANTIC_CROSSCHECK')
        self.assertEqual(r['solver_review']['status'],'READY_FOR_RESULT_VERIFICATION')
        self.assertIn('SOLVER_EXECUTION_NOT_ACCEPTED',r['reasons'])
        self.assertNotIn('SOLVER_NOT_RUN',r['reasons'])
        self.assertEqual(r['status'],'BLOCK');self.assertFalse(r['acceptance_granted'])


if __name__=='__main__':unittest.main()

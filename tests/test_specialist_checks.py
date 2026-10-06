import json
import tempfile
import unittest
from pathlib import Path

from engineering.calculation.model_intake import CalculationArtifact, audit_calculation_model_intake
from engineering.normative.verification import NormativeVerificationRecord, gate_normative_verification


class ContractTests(unittest.TestCase):
    def test_unknown_calculation_role_cannot_count_as_complete_intake(self):
        with self.assertRaises(ValueError):
            CalculationArtifact('a', 'MODEL', 'a'*64, 'source:1')

    def test_intake_rejects_untyped_artifact_instead_of_crashing(self):
        with self.assertRaises(ValueError): audit_calculation_model_intake(('fake',))

    def test_normative_strings_cannot_masquerade_as_evidence_id_array(self):
        record=NormativeVerificationRecord('Test','2026','scope','1','req','actual','ev-1','comparison','conclusion')
        self.assertEqual(gate_normative_verification(record).status,'BLOCK')

    def test_invalid_normative_scalar_blocks_without_attribute_error(self):
        record=NormativeVerificationRecord('Test',None,'scope','1','req','actual',('e1',),'comparison','conclusion')
        self.assertEqual(gate_normative_verification(record).status,'BLOCK')


class NumericChecksTests(unittest.TestCase):
    def numeric(self, **changes):
        from engineering.normative.numeric_comparison import compare_quantity
        values=dict(actual='2500',actual_unit='mm',limit='2.5',limit_unit='m',operator='<=')
        values.update(changes)
        return compare_quantity(**values)

    def test_units_converted_before_comparison_without_acceptance(self):
        r=self.numeric();self.assertTrue(r['satisfied']);self.assertEqual(r['actual_si'],'2.500')
        self.assertEqual(r['status'],'UNCERTAINTY');self.assertFalse(r['acceptance_granted'])

    def test_exceeded_limit_is_arithmetic_mismatch_not_proven_object_error(self):
        r=self.numeric(actual='2501');self.assertFalse(r['satisfied'])
        self.assertEqual(r['status'],'UNCERTAINTY');self.assertIn('INPUT_TRUTH_NOT_VERIFIED',r['reasons'])

    def test_dimension_mismatch_unknown_units_and_nonfinite_numbers_block(self):
        for changes in ({'actual_unit':'kN'},{'actual_unit':'kgf'},{'actual':'NaN'}, {'actual':True},{'actual':'1e999999'}, {'operator':'eval'}):
            with self.subTest(changes=changes):self.assertEqual(self.numeric(**changes)['status'],'BLOCK')

    def test_pressure_conversion_and_equality_boundary(self):
        self.assertTrue(self.numeric(actual='2000',actual_unit='kPa',limit='2',limit_unit='MPa',operator='>=' )['satisfied'])
        self.assertFalse(self.numeric(operator='<')['satisfied'])


class LocalSpecialistChecksTests(unittest.TestCase):
    def test_core_plan_text_and_saved_status_preserve_prerequisite_block(self):
        from engineering.local_app.store import Store
        from engineering.local_app.files import preserve_file
        from engineering.local_app.worker import Worker
        with tempfile.TemporaryDirectory() as folder:
            store=Store(Path(folder));sid=store.create_session()['id']
            source=preserve_file(store,sid,'report.txt',b'Unverified input')
            store.enqueue(sid,'Plan',[source['id']],mode='CORE_PLAN',requested_checks=['normative'])
            Worker(store,object()).run_once()
            result=store.snapshot(sid)['jobs'][0]['result']
            self.assertEqual(result['core_plan']['status'],'BLOCK')
            self.assertIn('Статус: BLOCK.',result['text'])
            self.assertEqual(result['engineering_status'],'BLOCK')

    def test_normative_and_calculation_gaps_reach_audit_and_survive_restart(self):
        from engineering.local_app.store import Store
        from engineering.local_app.files import preserve_file
        from engineering.local_app.worker import Worker
        with tempfile.TemporaryDirectory() as folder:
            store=Store(Path(folder));sid=store.create_session()['id']
            source=preserve_file(store,sid,'report.txt',b'Unverified input')
            job=store.enqueue(sid,'Review inputs',[source['id']],mode='CORE_RUN',requested_checks=['normative','calculation'])
            calls=[]
            class Model:
                def chat(self,messages):
                    calls.append(messages)
                    return json.dumps(dict(status='UNCERTAINTY',summary='Draft',observations=[],limitations=[]))
            Worker(store,Model()).run_once()
            result=store.snapshot(sid)['jobs'][0]['result']
            self.assertIn('specialist_checks',result)
            checks=result['specialist_checks'];self.assertEqual(checks['status'],'BLOCK')
            self.assertFalse(checks['acceptance_granted'])
            self.assertIn('NORMATIVE_EDITION_NOT_VERIFIED',str(calls[-1]))
            self.assertIn('SOLVER_NOT_RUN',str(calls[-1]))
            self.assertEqual(result['core_run']['status'],'BLOCK')
            self.assertEqual(result['engineering_status'],'BLOCK')
            self.assertEqual(Store(Path(folder)).snapshot(sid)['jobs'][0]['result']['specialist_checks'],checks)


if __name__=='__main__':unittest.main()

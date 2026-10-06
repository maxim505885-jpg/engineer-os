import json
import unittest

from engineering.calculation.exchange_manifest import parse_exchange_manifest,audit_exchange_manifest
from engineering.calculation.solver_receipt import SolverReceipt,audit_solver_receipt


class CalculationExchangeTests(unittest.TestCase):
    def manifest(self):
        sha='a'*64
        return dict(
            format='ENGINEER_OS_CALC_EXCHANGE',
            version=1,
            source_sha256=sha,
            sections=[
                dict(name='GEOMETRY',source_sha256=sha,records=[{'node':1,'x':0,'y':0,'z':0}]),
                dict(name='MATERIALS_SECTIONS',source_sha256=sha,records=[{'material':'C25/30'}]),
                dict(name='LOADS_COMBINATIONS',source_sha256=sha,records=[{'case':'LC1'}]),
                dict(name='SUPPORTS_RELEASES',source_sha256=sha,records=[{'node':1,'ux':True}]),
                dict(name='UNITS',source_sha256=sha,records=[{'length':'m','force':'kN'}]),
            ])

    def test_complete_manifest_is_only_ready_for_semantic_crosscheck(self):
        m=parse_exchange_manifest(json.dumps(self.manifest()))
        r=audit_exchange_manifest(m)
        self.assertEqual(r['status'],'READY_FOR_SEMANTIC_CROSSCHECK')
        self.assertIn('NATIVE_SOLVER_INPUT_NOT_PROVEN',r['reasons'])
        self.assertFalse(r['acceptance_granted'])

    def test_missing_or_empty_sections_block(self):
        body=self.manifest()
        body['sections']=body['sections'][:-1]
        r=audit_exchange_manifest(parse_exchange_manifest(json.dumps(body)))
        self.assertEqual(r['status'],'BLOCK')
        self.assertIn('UNITS',r['missing_sections'])
        body=self.manifest();body['sections'][0]['records']=[]
        r=audit_exchange_manifest(parse_exchange_manifest(json.dumps(body)))
        self.assertIn('GEOMETRY',r['empty_sections'])

    def test_duplicate_or_unknown_section_rejected(self):
        body=self.manifest();body['sections'].append(body['sections'][0])
        with self.assertRaises(ValueError):parse_exchange_manifest(json.dumps(body))
        body=self.manifest();body['sections'][0]['name']='RESULTS'
        with self.assertRaises(ValueError):parse_exchange_manifest(json.dumps(body))

    def test_nonzero_solver_exit_blocks(self):
        r=audit_solver_receipt(SolverReceipt(
            solver_name='TEST_SOLVER',solver_version='1.0',
            input_sha256='a'*64,output_sha256='b'*64,log_sha256='c'*64,
            exit_code=1,started_at='2026-10-06T20:00:00Z',finished_at='2026-10-06T20:01:00Z'))
        self.assertEqual(r['status'],'BLOCK')
        self.assertIn('SOLVER_EXIT_NONZERO',r['reasons'])

    def test_zero_exit_is_only_ready_for_result_verification(self):
        r=audit_solver_receipt(SolverReceipt(
            solver_name='TEST_SOLVER',solver_version='1.0',
            input_sha256='a'*64,output_sha256='b'*64,log_sha256='c'*64,
            exit_code=0,started_at='2026-10-06T20:00:00Z',finished_at='2026-10-06T20:01:00Z'))
        self.assertEqual(r['status'],'READY_FOR_RESULT_VERIFICATION')
        self.assertIn('SOLVER_OUTPUT_NOT_SEMANTICALLY_VERIFIED',r['reasons'])
        self.assertFalse(r['acceptance_granted'])


if __name__=='__main__':
    unittest.main()

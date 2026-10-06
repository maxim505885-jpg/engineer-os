import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

from engineering.calculation.vendor_adapters import (
    SolverSourceSnapshot,audit_documented_source,to_exchange_manifest,
)
from engineering.calculation.exchange_manifest import parse_exchange_manifest,audit_exchange_manifest
from engineering.calculation.solver_bridge import SolverCommand,execute_solver
from engineering.calculation.solver_receipt import audit_solver_receipt


class VendorAdapterTests(unittest.TestCase):
    def snapshot(self):
        sha='a'*64
        return SolverSourceSnapshot(
            source_kind='LIRA_FEM_API',
            source_version='documented-api-test',
            source_sha256=sha,
            sections={
                'GEOMETRY':[{'node':1,'x':0,'y':0,'z':0},{'element':1,'type':10,'nodes':[1,2]}],
                'MATERIALS_SECTIONS':[{'element':1,'section':'TEST'}],
                'LOADS_COMBINATIONS':[{'case':'LC1','factor':1}],
                'SUPPORTS_RELEASES':[{'node':1,'ux':True,'uy':True,'uz':True}],
                'UNITS':[{'length':'m','force':'kN'}],
            },
        )

    def test_documented_snapshot_normalizes_without_acceptance(self):
        s=self.snapshot()
        r=audit_documented_source(s)
        self.assertEqual(r['status'],'READY_FOR_EXCHANGE_NORMALIZATION')
        self.assertFalse(r['acceptance_granted'])
        exchange=to_exchange_manifest(s)
        er=audit_exchange_manifest(parse_exchange_manifest(json.dumps(exchange)))
        self.assertEqual(er['status'],'READY_FOR_SEMANTIC_CROSSCHECK')
        self.assertFalse(er['acceptance_granted'])

    def test_missing_documented_section_blocks(self):
        s=self.snapshot()
        sections=dict(s.sections);sections.pop('UNITS')
        r=audit_documented_source(SolverSourceSnapshot(s.source_kind,s.source_version,s.source_sha256,sections))
        self.assertEqual(r['status'],'BLOCK')
        self.assertIn('UNITS',r['missing_sections'])

    def test_unrecognized_vendor_section_blocks(self):
        s=self.snapshot()
        sections=dict(s.sections);sections['MAGIC_BINARY_GUESS']=[{'x':1}]
        r=audit_documented_source(SolverSourceSnapshot(s.source_kind,s.source_version,s.source_sha256,sections))
        self.assertEqual(r['status'],'BLOCK')
        self.assertIn('MAGIC_BINARY_GUESS',r['extra_sections'])


class SolverBridgeTests(unittest.TestCase):
    def test_external_runner_hashes_input_output_and_log(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td).resolve()
            inp=root/'input.json';out=root/'output.json';log=root/'solver.log';script=root/'solver.py'
            inp.write_text('{"case":"test"}',encoding='utf-8')
            script.write_text(
                "from pathlib import Path\n"
                "Path('output.json').write_text('RESULT OK',encoding='utf-8')\n"
                "print('controlled solver log')\n",
                encoding='utf-8',
            )
            receipt=execute_solver(SolverCommand(
                executable=str(Path(sys.executable).resolve()),
                args=(str(script),),
                cwd=str(root),input_path=str(inp),output_path=str(out),log_path=str(log),
                solver_name='CONTROLLED_TEST_SOLVER',solver_version='1',
                timeout_seconds=30,
            ))
            self.assertEqual(receipt.exit_code,0)
            self.assertEqual(receipt.input_sha256,hashlib.sha256(inp.read_bytes()).hexdigest())
            self.assertEqual(receipt.output_sha256,hashlib.sha256(out.read_bytes()).hexdigest())
            self.assertEqual(receipt.log_sha256,hashlib.sha256(log.read_bytes()).hexdigest())
            r=audit_solver_receipt(receipt)
            self.assertEqual(r['status'],'READY_FOR_RESULT_VERIFICATION')
            self.assertFalse(r['acceptance_granted'])

    def test_runner_rejects_paths_outside_workdir(self):
        with tempfile.TemporaryDirectory() as td, tempfile.TemporaryDirectory() as other:
            root=Path(td).resolve();outside=Path(other).resolve()
            inp=root/'input';inp.write_bytes(b'x')
            with self.assertRaises(ValueError):
                execute_solver(SolverCommand(
                    executable=str(Path(sys.executable).resolve()),args=(),cwd=str(root),
                    input_path=str(inp),output_path=str(outside/'out'),log_path=str(root/'log'),
                    solver_name='TEST',solver_version='1',timeout_seconds=1,
                ))

    def test_zero_exit_without_expected_output_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td).resolve()
            inp=root/'input';log=root/'solver.log';script=root/'solver.py';out=root/'missing.out'
            inp.write_bytes(b'x')
            script.write_text("print('no output produced')\n",encoding='utf-8')
            with self.assertRaises(RuntimeError):
                execute_solver(SolverCommand(
                    executable=str(Path(sys.executable).resolve()),args=(str(script),),cwd=str(root),
                    input_path=str(inp),output_path=str(out),log_path=str(log),
                    solver_name='CONTROLLED_TEST_SOLVER',solver_version='1',timeout_seconds=30,
                ))


if __name__=='__main__':
    unittest.main()

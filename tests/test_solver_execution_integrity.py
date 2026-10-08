import sys,tempfile,unittest,subprocess
from pathlib import Path
from engineering.calculation.solver_bridge import SolverCommand,execute_solver

class SolverExecutionIntegrityTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name).resolve()
  self.inp=self.root/'input';self.inp.write_bytes(b'original');self.out=self.root/'output';self.log=self.root/'log';self.script=self.root/'solver.py'
 def command(self,code,**changes):
  self.script.write_text(code)
  fields=dict(executable=str(Path(sys.executable).resolve()),args=(str(self.script),),cwd=str(self.root),input_path=str(self.inp),output_path=str(self.out),log_path=str(self.log),solver_name='TEST',solver_version='1',timeout_seconds=2)
  fields.update(changes);return SolverCommand(**fields)
 def test_stale_output_is_rejected_before_launch(self):
  self.out.write_bytes(b'old result')
  with self.assertRaisesRegex(ValueError,'exist'):execute_solver(self.command("from pathlib import Path;Path('launched').write_text('yes')"))
  self.assertEqual(self.out.read_bytes(),b'old result');self.assertFalse((self.root/'launched').exists())
 def test_output_cannot_overwrite_original_input(self):
  with self.assertRaises(ValueError):execute_solver(self.command("from pathlib import Path;Path('input').write_text('destroyed')",output_path=str(self.inp)))
  self.assertEqual(self.inp.read_bytes(),b'original')
 def test_log_cannot_overwrite_input_or_output(self):
  for alias in [self.inp,self.out]:
   with self.subTest(alias=alias),self.assertRaises(ValueError):execute_solver(self.command("from pathlib import Path;Path('output').write_text('result')",log_path=str(alias)))
  self.assertEqual(self.inp.read_bytes(),b'original')
 def test_symlink_parent_cannot_escape_workdir(self):
  with tempfile.TemporaryDirectory() as other:
   outside=Path(other);(self.root/'escape').symlink_to(outside,target_is_directory=True)
   with self.assertRaises(ValueError):execute_solver(self.command("from pathlib import Path;Path('escape/result').write_text('outside')",output_path=str(self.root/'escape/result')))
   self.assertFalse((outside/'result').exists())
 def test_changed_input_cannot_receive_execution_receipt(self):
  with self.assertRaisesRegex(RuntimeError,'input'):execute_solver(self.command("from pathlib import Path;Path('input').write_text('changed');Path('output').write_text('result')"))
 def test_timeout_preserves_diagnostic_output(self):
  with self.assertRaises(subprocess.TimeoutExpired):execute_solver(self.command("import time;print('diagnostic before timeout',flush=True);time.sleep(5)",timeout_seconds=1))
  self.assertIn(b'diagnostic before timeout',self.log.read_bytes())
 def test_existing_log_not_replaced(self):
  self.log.write_bytes(b'prior evidence')
  with self.assertRaises(ValueError):execute_solver(self.command("from pathlib import Path;Path('output').write_text('new')"))
  self.assertEqual(self.log.read_bytes(),b'prior evidence')

 def test_broken_output_symlink_is_not_reused(self):
  self.out.symlink_to(self.root/'new-target')
  with self.assertRaises(ValueError):execute_solver(self.command("from pathlib import Path;Path('output').write_text('result')"))
  self.assertFalse((self.root/'new-target').exists())
 def test_empty_output_cannot_be_a_solver_result(self):
  with self.assertRaises(RuntimeError):execute_solver(self.command("from pathlib import Path;Path('output').touch()"))
 def test_output_symlink_created_by_process_is_rejected(self):
  with self.assertRaises(RuntimeError):execute_solver(self.command("from pathlib import Path;Path('output').symlink_to(Path('input'))"))

 def test_output_hardlink_to_input_is_rejected(self):
  with self.assertRaises(RuntimeError):execute_solver(self.command("import os;os.link('input','output')"))
 def test_output_hardlink_to_captured_log_is_rejected(self):
  with self.assertRaises(RuntimeError):execute_solver(self.command("import os;print('diagnostic',flush=True);os.link('log','output')"))
 def test_replaced_log_symlink_cannot_substitute_outside_evidence(self):
  with tempfile.TemporaryDirectory() as other:
   outside=Path(other)/'evidence';outside.write_bytes(b'old evidence')
   code="from pathlib import Path;print('captured',flush=True);Path('log').unlink();Path('log').symlink_to("+repr(str(outside))+");Path('output').write_text('result')"
   with self.assertRaises(RuntimeError):execute_solver(self.command(code))
   self.assertEqual(outside.read_bytes(),b'old evidence')
 def test_replaced_regular_log_is_rejected(self):
  code="from pathlib import Path;print('captured',flush=True);Path('log').unlink();Path('log').write_text('fake log');Path('output').write_text('result')"
  with self.assertRaises(RuntimeError):execute_solver(self.command(code))

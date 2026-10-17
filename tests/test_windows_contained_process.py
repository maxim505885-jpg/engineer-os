"""Preflight contracts; native execution is qualified separately on Windows."""
from pathlib import Path
import tempfile
import unittest
from runtime.windows_contained_process import validate_launch, ContainmentError

class WindowsContainmentContractTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.engine=self.root/'engine';self.stage=self.root/'stage'
        self.engine.mkdir();self.stage.mkdir();self.exe=self.engine/'owned.exe';self.exe.write_bytes(b'owned fixture')
    def test_exact_owned_executable_and_disjoint_directories(self):
        exe,engine,stage=validate_launch([str(self.exe),'--version'],self.engine,self.stage,30,1024,['out/result.log'])
        self.assertEqual(exe,self.exe.resolve());self.assertEqual(engine,self.engine.resolve());self.assertEqual(stage,self.stage.resolve())
    def test_outside_or_missing_executable_rejected(self):
        outside=self.root/'other.exe';outside.write_bytes(b'owned')
        for cmd in [[str(outside)],[str(self.engine/'missing.exe')],[],['relative.exe'],[str(self.exe),None]]:
            with self.subTest(cmd=cmd),self.assertRaises(ContainmentError):validate_launch(cmd,self.engine,self.stage,30,1024,['out/result.log'])
    def test_shared_or_nested_runtime_staging_rejected(self):
        nested=self.engine/'nested';nested.mkdir()
        for stage in [self.engine,nested,self.root]:
            with self.subTest(stage=stage),self.assertRaises(ContainmentError):validate_launch([str(self.exe)],self.engine,stage,30,1024,['out/result.log'])
    def test_limits_and_output_paths_rejected_before_launch(self):
        for timeout,limit,paths in [(0,1024,['x']), (True,1024,['x']), (601,1024,['x']), (30,0,['x']), (30,64*1024**2+1,['x']), (30,1024,['../outside']), (30,1024,['out/../x']), (30,1024,['C:/outside']), (30,1024,['x','x']), (30,1024,['process.log'])]:
            with self.subTest(paths=paths,timeout=timeout),self.assertRaises(ContainmentError):validate_launch([str(self.exe)],self.engine,self.stage,timeout,limit,paths)

class JobTerminationTests(unittest.TestCase):
    def test_waits_for_all_descendants_not_only_leader(self):
        from runtime.windows_contained_process import _terminate_job
        class API:
            JobObjectBasicAccountingInformation=1
            def __init__(self):self.counts=[2,1,0];self.terminated=False
            def TerminateJobObject(self,job,code):self.terminated=True
            def QueryInformationJobObject(self,job,kind):return {"ActiveProcesses":self.counts.pop(0)}
        api=API()
        _terminate_job(object(),api)
        self.assertTrue(api.terminated)
        self.assertEqual(api.counts,[])

    def test_unconfirmed_descendant_termination_fails_closed(self):
        from runtime.windows_contained_process import _terminate_job
        class API:
            JobObjectBasicAccountingInformation=1
            def TerminateJobObject(self,job,code):pass
            def QueryInformationJobObject(self,job,kind):return {"ActiveProcesses":1}
        with self.assertRaises(ContainmentError):_terminate_job(object(),API(),timeout=0)

if __name__=='__main__':unittest.main()

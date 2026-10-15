import hashlib
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from engineering.cad.conversion import convert_dwg

class CadConversionTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.source=self.root/'source.dwg'
        self.source.write_bytes(b'AC1032fixture')
        self.sha=hashlib.sha256(self.source.read_bytes()).hexdigest()
        self.exe=self.root/'ODAFileConverter.exe';self.exe.write_bytes(b'fixture converter')
    def run_conversion(self, runner):
        with patch('engineering.cad.conversion.subprocess.run',runner):
            return convert_dwg(self.source,self.root/'derived',converter=self.exe,source_sha256=self.sha)
    def test_isolated_copy_no_audit_and_source_bound_ledger(self):
        def runner(command,**kwargs):
            import ezdxf
            self.assertNotEqual(Path(command[1]),self.source.parent)
            self.assertEqual(command[5:8],['0','0','source.dwg'])
            ezdxf.new('R2018',units=4).saveas(Path(command[2])/'source.dxf')
            return subprocess.CompletedProcess(command,0,'warning: proxy objects','')
        result=self.run_conversion(runner)
        self.assertEqual(result['conversion_status'],'PASS')
        self.assertEqual(result['status'],'BLOCK')
        self.assertFalse(result['dwg_equivalence_verified'])
        self.assertEqual(result['source_sha256'],self.sha)
        self.assertEqual(result['ledger'][0]['code'],'DWG_SOURCE_CENSUS_UNAVAILABLE')
        self.assertTrue(any(x['code']=='CONVERTER_DIAGNOSTICS' for x in result['ledger']))
        self.assertEqual(hashlib.sha256(self.source.read_bytes()).hexdigest(),self.sha)
    def test_nonzero_exit_and_missing_output_are_blocked(self):
        for code in (0,1):
            with self.subTest(code=code):
                destination=self.root/('attempt'+str(code))
                with patch('engineering.cad.conversion.subprocess.run',return_value=subprocess.CompletedProcess([],code,'','failure')):
                    result=convert_dwg(self.source,destination,converter=self.exe,source_sha256=self.sha)
                self.assertEqual(result['conversion_status'],'BLOCK')
    def test_bad_hash_rejected_before_process(self):
        with patch('engineering.cad.conversion.subprocess.run') as runner:
            with self.assertRaises(ValueError):
                convert_dwg(self.source,self.root/'derived',converter=self.exe,source_sha256='0'*64)
            runner.assert_not_called()
    def test_existing_destination_never_overwritten(self):
        with self.assertRaises(FileExistsError):
            convert_dwg(self.source,self.root,converter=self.exe,source_sha256=self.sha)
    def test_timeout_recorded(self):
        result=self.run_conversion(lambda *a,**k: (_ for _ in ()).throw(subprocess.TimeoutExpired(a[0],1)))
        self.assertEqual(result['conversion_status'],'BLOCK')
        self.assertTrue(any(x['code']=='CONVERTER_TIMEOUT' for x in result['ledger']))
    def test_oversized_derivative_preserves_ledger(self):
        def runner(command,**kwargs):
            with (Path(command[2])/'source.dxf').open('wb') as stream:stream.truncate(21*1024*1024)
            return subprocess.CompletedProcess(command,0,b'',b'')
        result=self.run_conversion(runner)
        self.assertEqual(result['conversion_status'],'BLOCK')
        self.assertTrue(any(x['code']=='CONVERTER_OUTPUT_UNREADABLE' for x in result['ledger']))
    def test_zero_exit_with_truncated_ascii_dxf_is_explicitly_blocked(self):
        def runner(command,**kwargs):
            (Path(command[2])/'source.dxf').write_bytes(b'0\nSECTION\n2\nENTITIES\n0\nINSERT\n')
            return subprocess.CompletedProcess(command,0,b'',b'')
        result=self.run_conversion(runner)
        self.assertEqual(result['conversion_status'],'BLOCK')
        self.assertTrue(any(x['code']=='CONVERTER_OUTPUT_INCOMPLETE' for x in result['ledger']))

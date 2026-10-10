import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from subprocess import TimeoutExpired, CompletedProcess

from scripts.pdf_ocr_bounded_batch import run_batch


class ProcessBoundedOCRTests(unittest.TestCase):
    def test_timeout_is_recorded_without_losing_ledger(self):
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)/'source.pdf'
            source.write_bytes(b'%PDF-1.4 fake source')
            output=Path(folder)/'ledger.json'
            with patch('subprocess.run',side_effect=TimeoutExpired('worker',2)):
                result=run_batch(source,output,[492,493],timeout=2)
            self.assertEqual([x['reason'] for x in result['page_results']],
                             ['PROCESS_TIMEOUT','PROCESS_TIMEOUT'])
            self.assertFalse(result['qualified'])
            self.assertFalse(result['all_pages_completed'])
            self.assertTrue(output.is_file())

    def test_worker_failure_never_claims_completed(self):
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)/'source.pdf';source.write_bytes(b'%PDF test')
            output=Path(folder)/'ledger.json'
            with patch('subprocess.run',return_value=CompletedProcess([],1,'','worker error')):
                result=run_batch(source,output,[492],timeout=2)
            self.assertEqual(result['page_results'][0]['status'],'ERROR')
            self.assertFalse(result['all_pages_completed'])


if __name__=='__main__':
    unittest.main()

import hashlib
import tempfile
import unittest
from pathlib import Path

class NormativeReviewReplayTests(unittest.TestCase):
    def test_source_identity_mismatch_stops_before_review(self):
        from scripts.replay_normative_review import replay
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'norm.txt').write_text('wrong')
            data={'sources':[{'key':'norm','name':'norm.txt','sha256':'a'*64}],'candidates':[],'packets':[]}
            with self.assertRaisesRegex(ValueError,'identity'):replay(data,root,root/'out')
            self.assertFalse((root/'out').exists())

    def test_documented_negative_result_survives_reload(self):
        from scripts.replay_normative_review import replay
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);text=b'TEST 2026 clause1 actual';(root/'source.txt').write_bytes(text)
            data={'sources':[{'key':'s','name':'source.txt','sha256':hashlib.sha256(text).hexdigest()}],
                  'candidates':[{'key':'c','source':'s','quote':text.decode(),'statement':'Recorded text','page':None,'data_class':'U','decision':'SOURCE_CONFIRMED','note':'Text only'}],
                  'packets':[{'kind':'NORMATIVE','chain':dict(document='TEST',edition='2026',scope='Test',clause='clause1',requirement='clause1',actual_condition='actual',comparison='Missing calibration',conclusion='Blocked'),
                              'norm_ids':['c'],'actual_ids':['c'],'quantities':None,'substantive_review':dict(reviewer='Test',reviewed_at='2026-10-08',assessment_date='2026-07-28',edition_basis='Test only',applicability='APPLIES',applicability_basis='Test only',input_status='MISSING',outcome='BLOCK',rationale='Calibration missing',limitations=['Not field verified'])}]}
            result=replay(data,root,root/'out')
            self.assertTrue(result['saved_reload_equal']);self.assertFalse(result['acceptance_granted'])
            self.assertEqual(result['report']['packets'][0]['substantive_decision']['rationale'],'Calibration missing')

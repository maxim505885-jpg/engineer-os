import unittest
from types import SimpleNamespace
from scripts.pdf_table_candidates import classify

class PDFTableCandidateTests(unittest.TestCase):
    def test_page_frame_requires_review(self):
        page=SimpleNamespace(width=600,height=840)
        t=SimpleNamespace(bbox=(10,10,590,830),row_count=8,col_count=10,extract=lambda:[['x']*10 for _ in range(8)])
        item=classify(t,page)
        self.assertEqual(item['review_status'],'FRAME_SUSPECT_REVIEW_REQUIRED')
        self.assertFalse(item['content_verified'])

    def test_inner_table_is_unverified_candidate(self):
        page=SimpleNamespace(width=600,height=840)
        t=SimpleNamespace(bbox=(63,343,573,694),row_count=8,col_count=3,extract=lambda:[['a','b','c'] for _ in range(8)])
        item=classify(t,page)
        self.assertEqual(item['review_status'],'TABLE_CANDIDATE_UNVERIFIED')
        self.assertEqual(item['nonempty_cells'],24)

if __name__=='__main__':
    unittest.main()

import unittest
from engineering.document_intelligence.vector_ocr_review_routing import route_candidates


class VectorOCRReviewRoutingTests(unittest.TestCase):
    def test_preserves_all_tokens_and_marks_review_not_accept(self):
        words=['План','Трещины','SSS','===','Р']
        tokens=[dict(text=word,bbox_pdf=[0,0,20,8],confidence=90) for word in words]
        routed,counts=route_candidates(tokens)
        self.assertEqual(len(routed),len(words))
        self.assertEqual(routed[0]['review_route'],'TEXT_CANDIDATE_VISUAL_REVIEW')
        self.assertEqual(routed[2]['review_route'],'PROBABLE_GRAPHIC_NOISE')
        self.assertEqual(routed[3]['review_route'],'PROBABLE_GRAPHIC_NOISE')
        self.assertEqual(routed[4]['review_route'],'AMBIGUOUS_SINGLE_GLYPH')
        self.assertTrue(all(t['verified'] is False for t in routed))
        self.assertEqual(sum(counts.values()),len(words))

    def test_invalid_geometry_is_kept_for_review(self):
        routed,_=route_candidates([dict(text='A1',bbox_pdf=[1,2,0,3])])
        self.assertEqual(routed[0]['review_route'],'GEOMETRY_REVIEW_REQUIRED')
        self.assertFalse(routed[0]['verified'])


if __name__=='__main__':
    unittest.main()

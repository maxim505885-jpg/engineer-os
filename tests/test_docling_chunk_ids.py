import unittest
from engineering.document_intelligence.docling_adapter import DoclingDocumentParser


class DoclingChunkIdentityTests(unittest.TestCase):
    def test_independent_original_pages_have_distinct_block_ids(self):
        def export(page):
            return dict(texts=[dict(text='Same text', label='text', prov=[dict(page_no=page)])])
        first = DoclingDocumentParser._normalize(export(15))[0]
        second = DoclingDocumentParser._normalize(export(16))[0]
        self.assertNotEqual(first.block_id, second.block_id)
        self.assertEqual(first.text, second.text)
        self.assertEqual(first.provenance[0].page_no, 15)
        self.assertEqual(second.provenance[0].page_no, 16)

    def test_two_distinct_blocks_on_one_page_keep_distinct_ids(self):
        blocks = DoclingDocumentParser._normalize(dict(texts=[
            dict(text=t, prov=[dict(page_no=15)]) for t in ['one','two']]))
        self.assertEqual(len(blocks),2)
        self.assertEqual(len({b.block_id for b in blocks}),2)

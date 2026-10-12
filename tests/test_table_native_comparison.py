"""Keep independently extracted native alternatives, never silently fix OCR."""
import unittest
import fitz
from types import SimpleNamespace
from tests.test_table_readback import ruled_table
from engineering.local_app import table_worker as worker


class NativeComparisonTests(unittest.TestCase):
    def compare(self, text, box=None):
        tables=[{'cells':[{'source_bbox':box or [40,40,200,120],'text':text}]}]
        with fitz.open(stream=ruled_table(),filetype='pdf') as document:
            worker.compare_native_text(document[0],[30,30,530,370],tables)
        return tables[0]

    def test_conflicting_native_text_is_visible_without_replacing_ocr(self):
        table=self.compare('Nurnber')
        cell=table['cells'][0]
        self.assertEqual(cell['text'],'Nurnber')
        self.assertEqual(cell['native_text_alternative']['text'],'Number')
        self.assertEqual(cell['text_comparison'],'OCR_NATIVE_CONFLICT')
        self.assertEqual(table['text_conflict_count'],1)
        self.assertFalse(cell['native_text_alternative']['quality_verified'])

    def test_agreement_is_still_unverified(self):
        table=self.compare('Number')
        self.assertEqual(table['cells'][0]['text_comparison'],'AGREEMENT_UNVERIFIED')
        self.assertEqual(table['text_conflict_count'],0)

    def test_nearby_cell_never_receives_wrong_native_text(self):
        table=self.compare('Nurnber',[41.1,40,200,120])
        self.assertEqual(table['cells'][0]['text_comparison'],'NO_UNIQUE_NATIVE_CELL')
        self.assertNotIn('native_text_alternative',table['cells'][0])

    def test_large_optional_comparison_does_not_discard_valid_ocr(self):
        import json
        boxes=[(i*2,0,i*2+1,1) for i in range(1100)]
        native=SimpleNamespace(rows=[SimpleNamespace(cells=boxes)],extract=lambda:[['x'*4096]*1100])
        page=SimpleNamespace(find_tables=lambda **kwargs:SimpleNamespace(tables=[native]))
        tables=[{'cells':[{'source_bbox':list(box),'text':'OCR'} for box in boxes]}]
        worker.compare_native_text(page,[0,0,2300,10],tables)
        self.assertEqual(tables[0]['native_comparison'],'UNAVAILABLE')
        self.assertTrue(all(c['text']=='OCR' and 'native_text_alternative' not in c for c in tables[0]['cells']))
        self.assertLess(len(json.dumps(tables).encode()),worker.MAX_OUTPUT_BYTES)

    def test_ambiguous_geometry_never_selects_one_native_reader_value(self):
        box=(40,40,200,120)
        native=[SimpleNamespace(rows=[SimpleNamespace(cells=[box])],extract=lambda:[[text]]) for text in ['A','B']]
        # Bind each value separately instead of late-bound lambdas.
        native[0].extract=lambda:[['A']];native[1].extract=lambda:[['B']]
        page=SimpleNamespace(find_tables=lambda **kwargs:SimpleNamespace(tables=native))
        tables=[{'cells':[{'source_bbox':list(box),'text':'OCR'}]}]
        worker.compare_native_text(page,[30,30,530,370],tables)
        self.assertEqual(tables[0]['cells'][0]['text_comparison'],'NO_UNIQUE_NATIVE_CELL')
        self.assertNotIn('native_text_alternative',tables[0]['cells'][0])

    def test_repeated_candidates_cannot_multiply_native_payload_without_bound(self):
        box=(40,40,200,120)
        native=SimpleNamespace(rows=[SimpleNamespace(cells=[box])],extract=lambda:[['x'*4096]])
        page=SimpleNamespace(find_tables=lambda **kwargs:SimpleNamespace(tables=[native]))
        tables=[{'cells':[{'source_bbox':list(box),'text':'OCR'} for _ in range(1100)]}]
        worker.compare_native_text(page,[30,30,530,370],tables)
        self.assertEqual(tables[0]['native_comparison'],'UNAVAILABLE')
        self.assertTrue(all(c['text']=='OCR' and 'native_text_alternative' not in c for c in tables[0]['cells']))

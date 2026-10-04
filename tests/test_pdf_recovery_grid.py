import copy
import hashlib
import tempfile
import unittest
from pathlib import Path
from scripts.verify_pdf_recovery import recover, verify


class ReviewedGridTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.source = Path(self.temp.name) / 'source.pdf'
        self.source.write_bytes(b'source')
        sha = hashlib.sha256(b'source').hexdigest()
        def f(box, text):
            return dict(source_sha256=sha, source_page=1, bbox=box,
                        coordinate_origin='TOPLEFT', text=text)
        self.manifest = dict(schema_version=2, source_sha256=sha,
            status='UNCERTAINTY', evidentiary_status='NOT_EVIDENCE', acceptance_granted=False,
            review=dict(reviewer='test', reviewed_at='2026-10-04T12:00:00Z', scope='grid binding'),
            context_fragments=[f([0, 0, 30, 5], 'Context')],
            tables=[dict(table_id='table-1', source_page=1,
                x_boundaries=[0, 10, 20, 30], y_boundaries=[10, 20, 30], cells=[
                    dict(cell_id='merged', row_start=0, row_end=1, col_start=0, col_end=3,
                         source_fragment=f([0, 10, 30, 20], 'Header')),
                    *[dict(cell_id=f'cell-{i}', row_start=1, row_end=2, col_start=i, col_end=i+1,
                           source_fragment=f([i*10, 20, (i+1)*10, 30], 'Value' if i == 1 else ''))
                      for i in range(3)]])])
        self.text = {tuple(f['bbox']):f['text'] for f in self.manifest['context_fragments']}
        self.text.update({tuple(c['source_fragment']['bbox']):c['source_fragment']['text']
                          for c in self.manifest['tables'][0]['cells']})

    def audit(self, manifest=None):
        return verify(self.source, manifest or self.manifest, page_sizes={1:(100,100)},
                      read_text=lambda p,b:self.text.get(tuple(b), 'WRONG'))

    def test_preserves_merged_grid_without_acceptance(self):
        result = self.audit()
        self.assertEqual(result['verified_cells'], 4)
        self.assertEqual(result['verified_grid_slots'], 6)
        self.assertEqual(result['status'], 'PASS')
        self.assertEqual(result['document_status'], 'BLOCK')
        candidate = recover(self.source, self.manifest, project_id='p', document_id='d',
                            page_sizes={1:(100,100)}, read_text=lambda p,b:self.text[tuple(b)])
        self.assertEqual(candidate['tables'], self.manifest['tables'])
        self.assertEqual(len(candidate['blocks']), 5)
        self.assertEqual(candidate['blocks'][1]['grid_span']['col_end'], 3)
        self.assertFalse(candidate['complete_document'])
        self.assertFalse(candidate['acceptance_granted'])

    def test_rejects_invalid_grid_and_source(self):
        mutations = [
            lambda m:m['tables'][0]['cells'].pop(),
            lambda m:m['tables'][0]['cells'].append(copy.deepcopy(m['tables'][0]['cells'][0])),
            lambda m:m['tables'][0]['cells'][0].update(col_start=True),
            lambda m:m['tables'][0]['cells'][0].update(col_end=4),
            lambda m:m['tables'][0]['cells'][0]['source_fragment'].update(text='altered'),
            lambda m:m['tables'][0]['cells'][0]['source_fragment'].update(source_page=2),
            lambda m:m['tables'][0]['cells'][0]['source_fragment'].update(bbox=[1,10,30,20]),
            lambda m:m['tables'][0].update(x_boundaries=[0,10,float('nan'),30]),
            lambda m:m['tables'][0].update(x_boundaries=[0,20,10,30]),
            lambda m:m.update(acceptance_granted=True),
            lambda m:m.update(schema_version=99),
            lambda m:m.update(source_sha256='0'*64),
            lambda m:m.update(context_fragments=[]),
        ]
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                manifest = copy.deepcopy(self.manifest)
                mutation(manifest)
                with self.assertRaises(ValueError):
                    self.audit(manifest)

    def test_export_identity_is_unambiguous(self):
        manifest = copy.deepcopy(self.manifest)
        first = manifest['tables'][0]
        first['table_id'] = 'a:b'
        first['cells'][0]['cell_id'] = 'c'
        second = copy.deepcopy(first)
        second['table_id'] = 'a'
        second['cells'][0]['cell_id'] = 'b:c'
        manifest['tables'].append(second)
        result = recover(self.source, manifest, project_id='p', document_id='d',
                         page_sizes={1:(100,100)}, read_text=lambda p,b:self.text[tuple(b)])
        self.assertEqual(len(result['blocks']), len({b['block_id'] for b in result['blocks']}))

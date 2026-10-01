import copy
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from scripts.v4_region_archive_check import inspect_archive


class RegionArchiveTests(unittest.TestCase):
    def setUp(self):
        self.review = {'source_sha256': 'a' * 64, 'status': 'BLOCK', 'page_count': 534,
                       'blocked_reasons': {'MERGED_TABLE_CELL': [18]}}
        self.manifest = {'source_sha256': 'a' * 64, 'status': 'BLOCK', 'selected_pages': [18],
                         'exported_pages': [{'page': 18, 'reason': 'MERGED_TABLE_CELL'}],
                         'failed_pages': [], 'reused_pages': []}
        self.page = {'source_sha256': 'a' * 64, 'page_start': 18, 'page_end': 18,
                     'text_blocks': [], 'tables': [{'num_rows': 1, 'num_cols': 2,
                     'provenance': [{'page_no': 18}], 'cells': [
                         {'text': 'A', 'start_row_offset_idx': 0, 'end_row_offset_idx': 1,
                          'start_col_offset_idx': 0, 'end_col_offset_idx': 2}]}]}

    def run_archive(self, page=None, manifest=None, extra=None, candidates=None):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / 'regions.zip'
            with zipfile.ZipFile(path, 'w') as z:
                z.writestr('manifest.json', json.dumps(manifest or self.manifest))
                z.writestr('page-0018.json', json.dumps(page or self.page))
                if extra:
                    z.writestr(extra, '{}')
            return inspect_archive(path, self.review, candidates)

    def test_complete_export_is_diagnostic_and_merged_cells_are_preserved(self):
        result = self.run_archive()
        self.assertEqual(result['status'], 'BLOCK')
        self.assertTrue(result['archive_complete'])
        self.assertEqual(result['pages'][0]['tables'][0]['merged_cells'], 1)
        self.assertEqual(result['pages'][0]['tables'][0]['missing_positions'], 0)

    def test_missing_grid_cell_is_reported_without_acceptance(self):
        page = copy.deepcopy(self.page)
        page['tables'][0]['cells'][0]['end_col_offset_idx'] = 1
        result = self.run_archive(page)
        self.assertEqual(result['pages'][0]['tables'][0]['missing_positions'], 1)
        self.assertEqual(result['status'], 'BLOCK')

    def test_overlap_and_out_of_bounds_are_reported(self):
        page = copy.deepcopy(self.page)
        page['tables'][0]['cells'] *= 2
        result = self.run_archive(page)
        self.assertEqual(result['pages'][0]['tables'][0]['overlapping_positions'], 2)
        page['tables'][0]['cells'][0]['end_col_offset_idx'] = 3
        result = self.run_archive(page)
        self.assertIn('INVALID_CELL_SPAN', result['pages'][0]['tables'][0]['issues'])

    def test_foreign_hash_missing_provenance_and_dimensions_fail_closed(self):
        for mutation in ('hash', 'provenance', 'dimensions'):
            page = copy.deepcopy(self.page)
            if mutation == 'hash': page['source_sha256'] = 'b' * 64
            if mutation == 'provenance': page['tables'][0]['provenance'] = []
            if mutation == 'dimensions': page['tables'][0]['num_rows'] = 0
            result = self.run_archive(page)
            self.assertEqual(result['status'], 'BLOCK')
            self.assertTrue(result['pages'][0]['issues'] or result['pages'][0]['tables'][0]['issues'])

    def test_foreign_members_and_missing_selected_page_rejected(self):
        with self.assertRaises(ValueError): self.run_archive(extra='../escape.json')
        manifest = copy.deepcopy(self.manifest)
        manifest['selected_pages'] = []
        with self.assertRaises(ValueError): self.run_archive(manifest=manifest)

    def test_candidates_compare_text_and_shape_without_claiming_visual_match(self):
        candidates = {'source_sha256': 'a' * 64, 'status': 'BLOCK', 'pages': [
            {'page': 18, 'candidates': [{'rows': 1, 'columns': 2, 'raw_grid': [['A', None]]}]}]}
        result = self.run_archive(candidates=candidates)
        compare = result['pages'][0]['tables'][0]['candidate_comparisons'][0]
        self.assertTrue(compare['shape_matches'])
        self.assertTrue(compare['nonempty_text_matches'])
        self.assertEqual(result['status'], 'BLOCK')


if __name__ == '__main__': unittest.main()

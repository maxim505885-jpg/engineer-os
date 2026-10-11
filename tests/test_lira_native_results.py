"""Synthetic R4 packages following PR102 results-reader.cs; no vendor execution."""
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from engineering.calculation.native_results import HEADER, KIND, METHODS
from engineering.calculation.upload_analysis import analyze_upload, report_note
from engineering.local_app.files import preserve_file
from engineering.local_app.store import Store

DEFAULT_ROWS = ['1\t41\t7\t0\t0\t0\tGetNodeX\t0\tEXPORTED\t',
                '2\t901\t7\t0\t0\t1\tGetBarN\t-12.5\tEXPORTED\t',
                '1\t41\t7\t0\t0\t0\tGetNodeY\t\tUNAVAILABLE\t0x80004005',
                '8\t0\t7\t0\t0\t0\tGetPeriods\t1.2\tEXPORTED\t']


def package(rows=None, change=None, tamper=None, extra=None, diagnostic=False, tsv=None):
    rows = DEFAULT_ROWS if rows is None else rows
    data = ('\t'.join(HEADER) + '\n' + '\n'.join(rows) + ('\n' if rows else '')).encode()
    if tsv is not None: data = tsv
    manifest = dict(schema=1, kind=KIND, document_name='Synthetic', source_sha256='a'*64,
        scope='PRIMARY_SHAPE0_HISTORY0_AND_REQUEST_AVAILABILITY', status='PARTIAL_RESULT_EXPORT',
        counts_scope='WHOLE_RUN_NOT_PART', attempted_values=120, value_rows=100,
        unavailable_values=20, parts=3, part_number=2, result_values_exported=True,
        requests=[dict(type_id=i, method=METHODS[i],
            status='PRIMARY_VALUES_PARTIAL' if i in {1,2,3,4,8} else 'AVAILABILITY_ONLY',
            attempted_values=0, value_rows=0) for i in [10,1,2,3,4,5,6,7,8,9]],
        files=[dict(file='values_00003.tsv', bytes=len(data), rows=len(rows),
                    sha256=hashlib.sha256(data).hexdigest())])
    # Whole-run per-request counters may include rows in other parts, but must
    # cover every observed value/diagnostic in this synthetic part.
    counts = {typ: [0, 0] for typ in [1, 2, 3, 4, 8]}
    for row in rows:
        cells = row.split('\t')
        if len(cells) == 10 and cells[0].isdigit() and int(cells[0]) in counts:
            counts[int(cells[0])][0 if cells[8] == 'EXPORTED' else 1] += 1
    numerical = sum(item[0] for item in counts.values())
    whole_values = max(100, numerical)
    counts[1][0] += whole_values - numerical
    counts[1][1] += max(0, 20-sum(item[1] for item in counts.values()))
    manifest.update(value_rows=whole_values, attempted_values=whole_values+20)
    for request in manifest['requests']:
        if request['type_id'] in counts:
            exported, unavailable = counts[request['type_id']]
            request.update(value_rows=exported, attempted_values=exported+unavailable)
    if diagnostic:
        manifest.update(parts=0, files=[], attempted_values=0, value_rows=0, unavailable_values=0,
                        status='RESULT_ACCESS_UNAVAILABLE', result_values_exported=False)
        manifest.pop('part_number')
        for request in manifest['requests']: request.update(status='UNAVAILABLE', attempted_values=0, value_rows=0)
    if change: change(manifest)
    output = io.BytesIO()
    with zipfile.ZipFile(output, 'w') as archive:
        archive.writestr('manifest.json', json.dumps(manifest))
        archive.writestr('api-contract.json', '{}')
        if not diagnostic: archive.writestr('values_00003.tsv', data if tamper is None else tamper)
        for name, content in (extra or {}).items(): archive.writestr(name, content)
    return output.getvalue()


class NativeResultTests(unittest.TestCase):
    def report(self, **kwargs):
        return analyze_upload('result.zip', package(**kwargs))

    def invalid(self, **kwargs):
        report = self.report(**kwargs)
        self.assertEqual(report['kind'], 'LIRA_NATIVE_RESULT_PACKAGE')
        self.assertIn('NATIVE_RESULT_PACKAGE_INVALID', report['reasons'])
        self.assertFalse(report['results_exported'])
        self.assertNotIn('part_value_rows', report['observations'])
        self.assertTrue(all(item['report'] is None for item in report['members']))

    def test_observed_part_values_are_not_whole_run_claims(self):
        report = self.report(); obs = report['observations']
        self.assertEqual(report['kind'], 'LIRA_NATIVE_RESULT_PACKAGE')
        self.assertEqual((obs['part_value_rows'], obs['part_unavailable_rows']), (3, 1))
        self.assertEqual(obs['whole_run_value_rows_claim'], 100)
        self.assertEqual(obs['whole_run_parts_claim'], 3)
        self.assertEqual(obs['value_samples'][0]['subject_id'], 41)
        self.assertEqual(obs['value_samples'][1]['subject_id'], 901)
        self.assertEqual(obs['value_samples'][0]['value'], 0)
        self.assertEqual(obs['value_samples'][2]['subject_id'], 0)
        self.assertEqual(obs['component_summaries'][0]['minimum'], 0)
        self.assertTrue(report['results_exported'])
        self.assertTrue(obs['result_values_available'])
        self.assertFalse(report['acceptance_granted'])
        self.assertFalse(report['engineering_verified'])
        self.assertFalse(report['full_information_extracted'])
        self.assertFalse(report['completed_solver_run_verified'])
        self.assertEqual(obs['model_result_association'], 'UNVERIFIED')
        self.assertIn('численных значений 3', report_note(report))

    def test_availability_only_is_not_numerical_result(self):
        report = self.report(diagnostic=True)
        self.assertEqual(report['observations']['part_value_rows'], 0)
        self.assertFalse(report['results_exported'])
        self.assertFalse(report['observations']['file_hashes_verified'])
        self.assertIn('NO_NUMERICAL_VALUES_EXPORTED', report['reasons'])

    def test_unavailable_only_part_preserves_diagnostic(self):
        report = self.report(rows=[DEFAULT_ROWS[2]])
        self.assertEqual(report['observations']['part_unavailable_rows'], 1)
        self.assertFalse(report['results_exported'])
        self.assertEqual(report['observations']['value_samples'], [])

    def test_samples_bounded_and_component_summary_complete(self):
        rows = [f'1\t{i+1}\t7\t0\t0\t0\tGetNodeX\t{i}\tEXPORTED\t' for i in range(130)]
        report = self.report(rows=rows, change=lambda m:m.update(value_rows=130, attempted_values=150))
        obs = report['observations']
        self.assertEqual(len(obs['value_samples']), 100)
        self.assertEqual(obs['value_samples_omitted'], 30)
        self.assertEqual(obs['component_summaries'][0]['maximum'], 129)

    def test_manifest_cannot_escalate_trust(self):
        report = self.report(change=lambda m:m.update(acceptance_granted=True,
            engineering_verified=True, source_result_binding_verified=True,
            completed_solver_run_verified=True, full_information_extracted=True, solver_execution='SUCCESS'))
        for key in ['acceptance_granted','engineering_verified','source_result_binding_verified',
                    'completed_solver_run_verified','full_information_extracted']:
            self.assertFalse(report[key])
        self.assertEqual(report['solver_execution'], 'NOT_RUN_BY_ENGINEER_OS')

    def test_bad_manifest_contracts_are_rejected(self):
        changes = [lambda m:m.update(schema=True), lambda m:m.update(schema=2),
            lambda m:m.update(counts_scope='PART'), lambda m:m.update(source_sha256='bad'),
            lambda m:m.update(part_number=4), lambda m:m['files'][0].update(rows=5),
            lambda m:m['files'][0].update(bytes=True), lambda m:m['files'][0].update(sha256='b'*64),
            lambda m:m['files'].append(m['files'][0].copy()),
            lambda m:m['requests'][0].update(status='PRIMARY_VALUES_PARTIAL'),
            lambda m:m['requests'][0].update(method='Unknown'),
            lambda m:m['requests'].append(m['requests'][0].copy()),
            lambda m:m.update(value_rows=1), lambda m:m.update(attempted_values=1),
            lambda m:m.update(scope='UNBOUNDED'), lambda m:m['requests'].pop(),
            lambda m:m['requests'][0].update(value_rows=1)]
        for change in changes:
            with self.subTest(change=change): self.invalid(change=change)

    def test_exact_row_types_components_context_and_finite_values(self):
        bad_rows = ['1\t41\t7\t0\t0\t0\tGetNodeX\tNaN\tEXPORTED\t',
                    '1\t41\t7\t0\t0\t0\tGetNodeX\t1e999\tEXPORTED\t',
                    '1\t41\t7\t0\t0\t0\tGetNodeX\t0\tUNAVAILABLE\t0x80004005',
                    '1\t41\t7\t0\t0\t0\tGetNodeX\t\tUNAVAILABLE\t',
                    '10\t41\t7\t0\t0\t0\tGetNodeCount\t0\tEXPORTED\t',
                    '1\t0\t7\t0\t0\t0\tGetNodeX\t0\tEXPORTED\t',
                    '1\t41\t7\t1\t0\t0\tGetNodeX\t0\tEXPORTED\t',
                    '2\t901\t7\t0\t0\t0\tGetBarN\t0\tEXPORTED\t',
                    '1\t41\t7\t0\t0\t0\tGetBarN\t0\tEXPORTED\t',
                    DEFAULT_ROWS[0]+'\textra']
        for row in bad_rows:
            with self.subTest(row=row): self.invalid(rows=[row])
        self.invalid(rows=[DEFAULT_ROWS[0], DEFAULT_ROWS[0]])

    def test_per_request_claims_bound_part_rows_even_with_unavailable_status(self):
        def zero_claim(m):
            request = next(r for r in m['requests'] if r['type_id'] == 1)
            request.update(status='UNAVAILABLE', attempted_values=0, value_rows=0)
        self.invalid(change=zero_claim)
        self.invalid(change=lambda m:next(r for r in m['requests'] if r['type_id']==1).update(value_rows=0))
        self.invalid(change=lambda m:next(r for r in m['requests'] if r['type_id']==1).update(attempted_values=98))
        self.invalid(change=lambda m:next(r for r in m['requests'] if r['type_id']==1).update(status='NOT_ATTEMPTED'))
        self.invalid(change=lambda m:next(r for r in m['requests'] if r['type_id']==1).update(status='NO_SUBJECTS'))
        # The C# exporter can write earlier chunks before a later chunk fails.
        report = self.report(change=lambda m:next(r for r in m['requests'] if r['type_id']==1).update(status='UNAVAILABLE'))
        self.assertEqual(report['observations']['part_value_rows'], 3)
        self.assertTrue(report['results_exported'])
        self.assertEqual(next(r for r in report['observations']['request_diagnostics'] if r['type_id']==1)['status'], 'UNAVAILABLE')

    def test_hash_extra_files_and_no_generic_fallback(self):
        self.invalid(tamper=b'(0/ )(1/10 1 1/)(3/1 100/)(4/0 0 0/)')
        self.invalid(extra={'values_00004.tsv': b'unknown'})
        self.invalid(extra={'note.txt': b'unknown'})

    def test_original_bytes_and_hashes_survive_store_flow(self):
        data = package()
        with tempfile.TemporaryDirectory() as directory:
            store = Store(Path(directory)); session = store.create_session()['id']
            stored = preserve_file(store, session, 'result.zip', data)
            result = store.get_file(stored['id'])
            report = result['extraction_coverage']['calculation_report']
            self.assertEqual(report['source_sha256'], hashlib.sha256(data).hexdigest())
            member = next(m for m in report['members'] if m['name']=='values_00003.tsv')
            self.assertEqual(member['report']['kind'], 'LIRA_NATIVE_RESULT_TABLE')
            self.assertEqual(member['report']['source_sha256'], member['source_sha256'])
            self.assertEqual(member['report']['observations']['rows'], 4)
            self.assertFalse(member['report']['acceptance_granted'])
            # preserve_file's recorded original path is the uploaded ZIP, not a reconstructed package.
            original = Path(result['storage_path']) if 'storage_path' in result else Path(result['path'])
            self.assertEqual(original.read_bytes(), data)

    def test_invalid_encoding_header_and_line_bombs(self):
        self.invalid(rows=['x'*5000])
        self.invalid(rows=['\x00'])
        self.invalid(rows=['request_type\tsubject_id'])
        for data in [b'bad_header\n' + DEFAULT_ROWS[0].encode() + b'\n',
                     ('\t'.join(HEADER)+'\n').encode() + b'\xff\n',
                     ('\t'.join(HEADER)+'\n'+DEFAULT_ROWS[0]).encode(),
                     ('\t'.join(HEADER)+'\n'+DEFAULT_ROWS[0]+'\n\n').encode()]:
            with self.subTest(data=data): self.invalid(rows=[DEFAULT_ROWS[0]], tsv=data)

    def test_zip_framing_duplicates_paths_and_expansion_limits(self):
        data = package()
        for framed in [b'prefix'+data, data+b'trailing']:
            with self.subTest(length=len(framed)):
                report = analyze_upload('bad.zip', framed)
                self.assertIn('ARCHIVE_INVENTORY_LIMIT_OR_INVALID', report['reasons'])
        report = self.report(extra={'../values_00003.tsv': b'bad'})
        self.assertIn('UNSAFE_ARCHIVE_MEMBER', report['reasons'])
        with patch('engineering.calculation.upload_analysis.MAX_EXPANDED', 10):
            self.assertIn('ARCHIVE_EXPANSION_LIMIT_OR_ENCRYPTED', self.report()['reasons'])
        with patch('engineering.calculation.native_results.MAX_ROWS', 2):
            self.invalid()
        with zipfile.ZipFile(io.BytesIO(data)) as source:
            output = io.BytesIO()
            with zipfile.ZipFile(output, 'w') as target:
                for info in source.infolist(): target.writestr(info.filename, source.read(info))
                import warnings
                with warnings.catch_warnings():
                    warnings.simplefilter('ignore', UserWarning)
                    target.writestr('manifest.json', source.read('manifest.json'))
            self.assertIn('ARCHIVE_UNREADABLE', analyze_upload('duplicate.zip', output.getvalue())['reasons'])

    def test_duplicate_json_keys_fail_before_native_or_generic_children(self):
        data = package()
        with zipfile.ZipFile(io.BytesIO(data)) as source:
            output = io.BytesIO()
            with zipfile.ZipFile(output, 'w') as target:
                for info in source.infolist():
                    payload = source.read(info)
                    if info.filename == 'manifest.json': payload = payload.replace(b'"schema": 1', b'"schema": 1, "schema": 1')
                    target.writestr(info.filename, payload)
        report = analyze_upload('duplicate-json.zip', output.getvalue())
        self.assertIn('NATIVE_RESULT_PACKAGE_INVALID', report['reasons'])
        self.assertTrue(all(member['report'] is None for member in report['members']))

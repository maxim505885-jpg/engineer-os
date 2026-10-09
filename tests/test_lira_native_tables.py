import hashlib
import io
import json
import unittest
import zipfile
import tempfile
from pathlib import Path

from engineering.calculation.upload_analysis import analyze_upload, report_note
from engineering.local_app.files import extract_preview, preserve_file
from engineering.local_app.store import Store


def package(tables=None, change=None, tamper=None):
    tables = tables or {2: '1\t0\t0\t0\t\n2\t1,5\t0\t0\t\n',
                        3: '1\t10\t1,2\t\n2\t57\t2\t\n',
                        9: '1\tbeam\t\n', 10: '1\t1\t\n2\t0\t\n',
                        25: '1\tСобственный вес\t\n', 8: ''}
    manifest = dict(schema=2, kind='ENGINEER_OS_LIRA_MODEL_TABLE_EXPORT',
                    source_name='model.lir', source_sha256='a'*64,
                    source_bytes=123, units={'Geometry': 0}, tables=[])
    for ident, content in tables.items():
        data = content.encode()
        manifest['tables'].append(dict(type_id=ident, file=f'table_{ident:02}.tsv',
            status='EXPORTED', sha256=hashlib.sha256(data).hexdigest(), bytes=len(data),
            model_part=0, parameter_status='READ'))
    if change: change(manifest)
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, 'w') as z:
        z.writestr('manifest.json', json.dumps(manifest, ensure_ascii=False))
        for ident, content in tables.items():
            name = f'table_{ident:02}.tsv'
            if tamper and name in tamper:
                if tamper[name] is None: continue
                content = tamper[name]
            z.writestr(name, content)
    return stream.getvalue()


class NativeTableTests(unittest.TestCase):
    def test_native_archive_reaches_app_upload_report(self):
        report = extract_preview('native.zip', package())[4]['calculation_report']
        self.assertEqual(report['kind'], 'LIRA_NATIVE_TABLE_PACKAGE')
        obs = report['observations']
        self.assertTrue(obs['table_hashes_verified'])
        self.assertEqual((obs['nodes'], obs['elements'], obs['load_cases']), (2, 2, 1))
        self.assertEqual(obs['element_types'], {'10': 1, '57': 1})
        self.assertEqual(obs['node_bounds']['X'], [0.0, 1.5])
        self.assertEqual(obs['ke57_auxiliary_stiffness_not_extracted'], 1)
        self.assertEqual(obs['invalid_node_references'], 0)
        self.assertIn('KE57_AUXILIARY_STIFFNESS_NOT_EXTRACTED', report['reasons'])
        self.assertIn('Узлов: 2', report_note(report))

    def test_manifest_cannot_grant_acceptance_or_verify_original(self):
        report = analyze_upload('x.zip', package(change=lambda m:m.update(
            acceptance_granted=True, full_information_extracted=True, results_exported=True,
            solver_execution='SUCCESS', original_unchanged=True)))
        self.assertFalse(report['acceptance_granted'])
        self.assertFalse(report['engineering_verified'])
        self.assertFalse(report['full_information_extracted'])
        self.assertFalse(report['results_exported'])
        self.assertFalse(report['observations']['original_source_hash_verified'])
        self.assertEqual(report['solver_execution'], 'NOT_RUN_BY_ENGINEER_OS')

    def test_modified_table_and_missing_table_fail_closed(self):
        for replacement in ['1\t9\t9\t9\t\n', None]:
            with self.subTest(replacement=replacement):
                report = analyze_upload('x.zip', package(tamper={'table_02.tsv': replacement}))
                self.assertIn('NATIVE_PACKAGE_INVALID', report['reasons'])
                self.assertNotIn('nodes', report['observations'])

    def test_duplicate_ids_unknown_types_and_scope_are_rejected(self):
        mutations = [lambda m:m['tables'].append(m['tables'][0].copy()),
                     lambda m:m['tables'][0].update(type_id=99),
                     lambda m:m['tables'][0].update(model_part=1),
                     lambda m:m['tables'][0].update(bytes=True),
                     lambda m:m.update(schema=99),
                     lambda m:m.update(source_sha256='invalid')]
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                self.assertIn('NATIVE_PACKAGE_INVALID', analyze_upload('x.zip', package(change=mutation))['reasons'])

    def test_invalid_numeric_geometry_is_rejected_after_valid_hash(self):
        for rows in ['1\tNaN\t0\t0\t\n', '1\t0\t0\t0\t\n1\t1\t0\t0\t\n']:
            with self.subTest(rows=rows):
                report = analyze_upload('x.zip', package(tables={2: rows}))
                self.assertIn('NATIVE_PACKAGE_INVALID', report['reasons'])

    def test_reference_discrepancy_is_observation_not_acceptance(self):
        report = analyze_upload('x.zip', package(tables={2:'1\t0\t0\t0\t\n',
            3:'1\t10\t1,9\t\n',9:'1\tbeam\t\n',10:'1\t8\t\n'}))
        self.assertEqual(report['observations']['invalid_node_references'], 1)
        self.assertEqual(report['observations']['ordinary_stiffness_references_not_in_table'], 1)
        self.assertFalse(report['acceptance_granted'])

    def test_failed_and_empty_tables_preserve_partial_inventory(self):
        def change(m):
            m['tables'].append(dict(type_id=7, status='FAILED', model_part=0))
            m['tables'][0]['parameter_status']='UNAVAILABLE: vendor error'
        report = analyze_upload('x.zip', package(change=change))
        self.assertIn(7, report['observations']['failed_table_types'])
        self.assertIn(8, report['observations']['empty_table_types'])
        self.assertIn(2, report['observations']['parameter_unavailable_types'])
        self.assertIn('DEFAULT_TABLE_COVERAGE_ONLY', report['reasons'])

    def test_generic_archive_still_uses_existing_reader(self):
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, 'w') as z:z.writestr('note.txt', 'hello')
        self.assertEqual(analyze_upload('x.zip', stream.getvalue())['kind'], 'LIRA_EXPORT_PACKAGE')

    def test_table_member_is_recognized_and_report_survives_storage(self):
        data = package()
        with tempfile.TemporaryDirectory() as directory:
            store = Store(Path(directory)); session = store.create_session()['id']
            stored = preserve_file(store, session, 'native.zip', data)
            report = store.get_file(stored['id'])['extraction_coverage']['calculation_report']
            table = next(m for m in report['members'] if m['name']=='table_02.tsv')
            self.assertEqual(table['status'], 'OBSERVATIONS_RECORDED')
            self.assertEqual(table['report']['observations']['rows'], 2)
            self.assertFalse(table['report']['acceptance_granted'])

    def test_all_failed_manifest_does_not_claim_table_hashes_verified(self):
        def change(m):
            for t in m['tables']:t.update(status='FAILED')
        # Remove TSVs: a zero-table failed exporter writes only its manifest.
        data = package(change=change)
        with zipfile.ZipFile(io.BytesIO(data)) as source:
            stream = io.BytesIO()
            with zipfile.ZipFile(stream, 'w') as target:
                target.writestr('manifest.json', source.read('manifest.json'))
        report = analyze_upload('failed.zip', stream.getvalue())
        self.assertFalse(report['observations']['table_hashes_verified'])
        self.assertIn('TABLE_EXPORT_INCOMPLETE', report['reasons'])

    def test_real_exporter_unavailable_and_not_attempted_statuses_preserve_read_tables(self):
        for status in ['UNAVAILABLE', 'NOT_ATTEMPTED']:
            with self.subTest(status=status):
                def change(m):
                    m['tables'].append(dict(type_id=7, status=status, model_part=0,
                        file=None, bytes=0, sha256=None))
                report = analyze_upload('partial.zip', package(change=change))
                self.assertEqual(report['observations'].get('nodes'), 2)
                self.assertIn(7, report['observations']['failed_table_types'])

    def test_invalid_native_package_cannot_publish_generic_child_counts(self):
        content = '(0/ )(1/10 1 1/)(3/1 100/)(4/0 0 0/)'
        report = analyze_upload('bad.zip', package(tamper={'table_02.tsv':content}))
        self.assertIn('NATIVE_PACKAGE_INVALID', report['reasons'])
        self.assertTrue(all(member['report'] is None for member in report['members']))

    def test_tsv_delimiter_and_line_bombs_are_rejected_before_observations(self):
        for content in ['\t'*2000+'\n', 'a'*70000+'\n']:
            with self.subTest(length=len(content)):
                report = analyze_upload('oversized-row.zip', package(tables={8:content}))
                self.assertIn('NATIVE_PACKAGE_INVALID', report['reasons'])

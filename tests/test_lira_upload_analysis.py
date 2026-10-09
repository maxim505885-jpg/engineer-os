import io
import struct
import tempfile
import unittest
import zipfile
from pathlib import Path

from engineering.local_app.files import extract_preview, preserve_file
from engineering.local_app.store import Store


MODEL = b'(0/1; TEST/33;M 1 CM 100 T 1 C 1/)(1/10 1 1 2/)(3/1 100/)(4/0 0 0/1 0 0/)(6/1 1 1 1 1/)(7/1 5/)'


class LiraUploadAnalysisTests(unittest.TestCase):
    def report(self, name, data):
        coverage = extract_preview(name, data)[4]
        self.assertIn('calculation_report', coverage)
        return coverage['calculation_report']

    def test_model_is_analyzed_beyond_preview_limit(self):
        data = MODEL.replace(b'(4/', b'(4/' + b'0 0 0/' * 20000)
        report = self.report('model.txt', data)
        self.assertEqual(report['observations']['nodes'], 20002)
        self.assertEqual(report['observations']['elements'], 1)
        self.assertFalse(report['acceptance_granted'])
        self.assertIn('RESULTS_REQUIRED', report['reasons'])

    def test_invalid_node_reference_is_reported(self):
        report = self.report('model.txt', MODEL.replace(b'10 1 1 2', b'10 1 1 9'))
        self.assertEqual(report['observations']['invalid_node_references'], 1)

    def test_interrupted_log_does_not_claim_a_successful_run(self):
        data = 'Протокол расчета\nFESolver.exe 2024.2.3.0\nКоличество узлов = 42\nКонтроль решения\nРасчет прерван пользователем'.encode()
        report = self.report('run.log', data)
        self.assertEqual(report['solver_execution'], 'INTERRUPTED_BY_USER')
        self.assertEqual(report['observations']['nodes'], 42)
        self.assertFalse(report['acceptance_granted'])

    def test_static_step_is_not_full_completion(self):
        report = self.report('run.txt', 'Протокол расчета\nКонтроль решения'.encode())
        self.assertEqual(report['solver_execution'], 'NOT_CONFIRMED')

    def test_regular_text_is_not_misidentified_as_model(self):
        self.assertNotIn('calculation_report', extract_preview('note.txt', b'hello (1/2)')[4])

    def test_zip_analyzes_members_without_extracting_paths(self):
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, 'w') as z:
            z.writestr('model.txt', MODEL)
            z.writestr('run.log', 'Протокол расчета\nРасчет прерван пользователем')
        report = self.report('lira.zip', stream.getvalue())
        self.assertEqual(len(report['members']), 2)
        self.assertEqual(report['members'][1]['report']['solver_execution'], 'INTERRUPTED_BY_USER')
        with tempfile.TemporaryDirectory() as temp:
            store = Store(Path(temp)); session = store.create_session()['id']
            f = preserve_file(store, session, 'lira.zip', stream.getvalue())
            self.assertEqual(store.get_file(f['id'])['extraction_coverage']['calculation_report'], report)

    def test_unsafe_zip_member_is_refused(self):
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, 'w') as z: z.writestr('../model.txt', MODEL)
        report = self.report('lira.zip', stream.getvalue())
        self.assertIn('UNSAFE_ARCHIVE_MEMBER', report['reasons'])
        self.assertEqual(report['members'], [])

    def test_malformed_model_does_not_get_partial_counts(self):
        report = self.report('model.txt', MODEL[:-1])
        self.assertIn('INVALID_DOCUMENT_FRAMING', report['reasons'])
        self.assertEqual(report['observations'], {})

    def test_cop_is_capacity_not_actual_forces(self):
        report = self.report('piles.cop', b';capacity of piles\n[Capacity of piles]\n12=212.2\n')
        self.assertEqual(report['kind'], 'LIRA_PILE_CAPACITY')
        self.assertIn('ACTUAL_PILE_FORCES_NOT_PROVIDED', report['reasons'])

    def test_ald_identity_is_not_results(self):
        report = self.report('model.ald', b'<LIRA_Project Title="section"><RigidArray><Rigid/></RigidArray></LIRA_Project>')
        self.assertEqual(report['observations']['title'], 'section')
        self.assertIn('RESULTS_REQUIRED', report['reasons'])

    def test_xml_entities_are_not_expanded(self):
        report = self.report('model.ald', b'<!DOCTYPE a [<!ENTITY x "secret">]><LIRA_Project Title="&x;"/>')
        self.assertIn('XML_DECLARATIONS_NOT_ALLOWED', report['reasons'])

    def test_nonfinite_coordinates_are_refused(self):
        report = self.report('model.txt', MODEL.replace(b'1 0 0/', b'nan 0 0/'))
        self.assertIn('INVALID_NUMERIC_RECORD', report['reasons'])

    def test_invalid_encoding_is_not_synthetic_source_text(self):
        text, status, _, _, coverage = extract_preview('model.ald', b'\xff\x00')
        self.assertEqual(text, '')
        self.assertEqual(status, 'UNAVAILABLE')
        self.assertIn('UTF8_REQUIRED', coverage['calculation_report']['reasons'])

    def test_preview_truncation_does_not_claim_parser_truncation(self):
        data = MODEL.replace(b'(4/', b'(4/' + b'0 0 0/' * 20000)
        coverage = extract_preview('model.txt', data)[4]
        self.assertIn('CHAR_LIMIT', coverage['stop_reasons'])
        self.assertNotIn('CHAR_LIMIT', coverage['calculation_report']['reasons'])

    def test_truncated_zip_header_keeps_original_uploadable(self):
        report = self.report('broken.zip', b'PK\x05\x06')
        self.assertIn('ARCHIVE_INVENTORY_LIMIT_OR_INVALID', report['reasons'])

    def test_forged_zip_count_does_not_bypass_entry_budget(self):
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, 'w') as z:
            for i in range(65): z.writestr(str(i)+'.txt', MODEL)
        data = bytearray(stream.getvalue()); offset = data.rfind(b'PK\x05\x06')
        struct.pack_into('<HH', data, offset+8, 1, 1)
        report = self.report('forged.zip', bytes(data))
        self.assertIn('ARCHIVE_INVENTORY_LIMIT_OR_INVALID', report['reasons'])
        self.assertEqual(report['members'], [])

    def test_empty_member_does_not_erase_model_observations(self):
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, 'w') as z:
            z.writestr('model.txt', MODEL); z.writestr('empty.txt', b'')
        report = self.report('model.zip', stream.getvalue())
        self.assertEqual(report['members'][0]['report']['observations']['elements'], 1)
        self.assertEqual(report['members'][1]['status'], 'NOT_ANALYZED')

    def test_oversized_document_id_is_reported_without_losing_original(self):
        data = MODEL+b'('+b'9'*4301+b'/)'
        report = self.report('model.txt', data)
        self.assertIn('INVALID_DOCUMENT_FRAMING', report['reasons'])

    def test_corrupt_deflate_is_reported_without_losing_original(self):
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, 'w', zipfile.ZIP_DEFLATED) as z:
            z.writestr('a.txt', b'A'*10000)
        data = bytearray(stream.getvalue()); data[35:38] = b'\xff\xff\xff'
        report = self.report('broken.zip', bytes(data))
        self.assertIn('ARCHIVE_UNREADABLE', report['reasons'])

    def test_document_inventory_is_bounded_before_dossier_storage(self):
        data = MODEL+b''.join(('('+str(i)+'/)').encode() for i in range(100,400))
        report = self.report('model.txt', data)
        self.assertIn('DOCUMENT_INVENTORY_LIMIT', report['reasons'])

    def test_bomless_utf16_cannot_expand_xml_entities(self):
        xml = '<!DOCTYPE LIRA_Project [<!ENTITY x "expanded">]><LIRA_Project Title="&x;"/>'
        for encoding in ('utf-16le','utf-16be','utf-32le','utf-32be'):
            with self.subTest(encoding=encoding):
                preview = extract_preview('model.ald', xml.encode(encoding))
                self.assertEqual(preview[0], '')
                self.assertEqual(preview[1], 'UNAVAILABLE')
                self.assertEqual(preview[4]['calculation_report']['observations'], {})
                self.assertIn('XML_ENCODING_UNSUPPORTED', preview[4]['calculation_report']['reasons'])

    def test_parser_itself_rejects_dtd_even_if_early_filter_changes(self):
        from xml.etree import ElementTree as ET
        from engineering.calculation import upload_analysis
        xml = '<!DOCTYPE LIRA_Project [<!ENTITY x "expanded">]><LIRA_Project Title="&x;"/>'
        self.assertTrue(hasattr(upload_analysis,'RejectDTD'))
        for encoding in ('utf-8','utf-16le','utf-16be'):
            with self.subTest(encoding=encoding), self.assertRaises(ValueError):
                ET.fromstring(xml.encode(encoding), parser=ET.XMLParser(target=upload_analysis.RejectDTD()))

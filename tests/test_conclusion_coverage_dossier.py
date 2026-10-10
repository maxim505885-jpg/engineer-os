import io
import json
import unittest
import unicodedata
import zipfile
from xml.etree import ElementTree as ET

from tests import test_conclusion_drafts as draft_tests
from engineering.local_app import conclusions, coverage
from engineering.local_app.analysis_identity import parser_identity


class CoverageDossierTests(unittest.TestCase):
    setUp = draft_tests.ConclusionTests.setUp
    module = draft_tests.ConclusionTests.module
    build = draft_tests.ConclusionTests.build

    def extraction(self, *, office=False):
        job = self.store.enqueue(self.sid, 'Extraction', [self.source['id']], mode='CORE_RUN')
        run = dict(file_id=self.source['id'], source_sha256=self.source['sha256'],
                   backend='docx' if office else 'native', total_pages=3,
                   processed_pages=3, cycle_complete=True,
                   parser_identity=parser_identity('docx' if office else 'native'))
        if office:
            run.update(total_units=3, physical_pages=None, limitations=['PHYSICAL_PAGES_UNKNOWN'])
        with self.store.connection() as db:
            db.execute("UPDATE jobs SET mode='EXTRACT_NATIVE',state='SUCCEEDED',result=? WHERE id=?", (json.dumps({'extraction':run}),job['id']))
            record = dict(page=1, execution='COMPLETED', status='BLOCK', blocks=[], stored_chars=0,
                          source_sha256=self.source['sha256'], limitations=['IMAGE_CONTENT_UNVERIFIED'],
                          visual_components={'images':1,'vector_paths':2,'tables':'NOT_PARSED'})
            db.execute('INSERT INTO extraction_pages VALUES(?,?,?)',(job['id'],1,json.dumps(record)))
        return job

    def test_observed_journal_overrides_false_complete_summary(self):
        self.extraction()
        self.assertTrue(hasattr(coverage, 'source_dossier'), 'source completeness dossier is missing')
        d = coverage.source_dossier(self.store,self.sid,self.source)
        self.assertEqual(d['processed_units'],1)
        self.assertEqual(d['missing_ranges'],[[2,3]])
        self.assertEqual(d['blocked_units'],1)
        self.assertEqual(d['limitations']['IMAGE_CONTENT_UNVERIFIED'],1)
        self.assertEqual(d['unverified_images'],1)
        self.assertEqual(d['completeness'],'NOT_CHECKED')
        self.assertFalse(d['acceptance_granted'])

    def test_office_units_never_become_physical_pages(self):
        self.extraction(office=True)
        self.assertTrue(hasattr(coverage, 'source_dossier'), 'source completeness dossier is missing')
        d=coverage.source_dossier(self.store,self.sid,self.source)
        self.assertIsNone(d['physical_pages'])
        self.assertEqual(d['unit_kind'],'LOGICAL_UNIT')
        self.assertIn('PHYSICAL_PAGES_UNKNOWN',d['limitations'])

    def test_draft_exports_include_coverage_and_unknown_preview(self):
        d=self.build()
        self.assertIn('source_coverage',d, 'draft lacks source coverage binding')
        self.assertEqual(d['source_coverage'][0]['completeness'],'NOT_CHECKED')
        for fmt in ('docx','pdf'):
            data,_=conclusions.export(self.store,self.sid,revision=1,format=fmt)
            if fmt=='docx':
                with zipfile.ZipFile(io.BytesIO(data)) as z:
                    root=ET.fromstring(z.read('word/document.xml'))
                    text=''.join(x.text or '' for x in root.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t'))
            else:
                import fitz
                with fitz.open(stream=data,filetype='pdf') as pdf:
                    text=''.join(p.get_text() for p in pdf)
            normalized=''.join(unicodedata.normalize('NFKC',text).split())
            self.assertIn('NOT_CHECKED',normalized)
            self.assertIn('TEXT_PREVIEW_ONLY',normalized)

    def test_complete_journal_is_read_beyond_ui_window(self):
        job=self.extraction()
        with self.store.connection() as db:
            db.execute("UPDATE jobs SET result=json_set(result,'$.extraction.total_pages',60) WHERE id=?",(job['id'],))
            for number in range(2,61):
                record=dict(page=number,execution='COMPLETED',status='UNCERTAINTY',blocks=[],source_sha256=self.source['sha256'],limitations=[])
                db.execute('INSERT INTO extraction_pages VALUES(?,?,?)',(job['id'],number,json.dumps(record)))
        self.assertEqual(coverage.source_dossier(self.store,self.sid,self.source)['processed_units'],60)

    def test_journal_text_change_also_invalidates_draft(self):
        job=self.extraction();self.build()
        with self.store.connection() as db:
            db.execute("UPDATE extraction_pages SET record=json_set(record,'$.blocks',json(?)) WHERE job_id=?",(json.dumps([{'text':'Changed coordinates and text'}]),job['id']))
        with self.assertRaises(ValueError):conclusions.export(self.store,self.sid,revision=1,format='pdf')

    def test_journal_mutation_blocks_export_without_changing_case(self):
        job=self.extraction()
        self.assertTrue(hasattr(coverage, 'source_dossier'), 'source completeness dossier is missing')
        self.build()
        with self.store.connection() as db:
            db.execute("UPDATE extraction_pages SET record=json_set(record,'$.limitations[0]','TEXT_LIMIT') WHERE job_id=?",(job['id'],))
        state=conclusions.report(self.store,self.sid)['drafts'][-1]
        self.assertIn('DRAFT_SOURCE_COVERAGE_CHANGED',state['stale_reasons'])
        with self.assertRaises(ValueError):conclusions.export(self.store,self.sid,revision=1,format='docx')

    def test_foreign_session_source_is_rejected(self):
        self.assertTrue(hasattr(coverage, 'source_dossier'), 'source completeness dossier is missing')
        other=self.store.create_session()['id']
        with self.assertRaises(ValueError):coverage.source_dossier(self.store,other,self.source)

    def test_dossier_rejects_extent_outside_supported_pdf_limit(self):
        job=self.extraction()
        with self.store.connection() as db:
            db.execute("UPDATE jobs SET result=json_set(result,'$.extraction.total_pages',5001) WHERE id=?",(job['id'],))
        with self.assertRaises(ValueError):coverage.source_dossier(self.store,self.sid,self.source)

    def test_dossier_rejects_unbounded_limitation_text(self):
        job=self.extraction()
        with self.store.connection() as db:
            db.execute("UPDATE extraction_pages SET record=json_set(record,'$.limitations[0]',?) WHERE job_id=?",('x'*100000,job['id']))
        with self.assertRaises(ValueError):coverage.source_dossier(self.store,self.sid,self.source)

    def test_document_coverage_is_readable_prose(self):
        self.extraction()
        d=self.build()
        text='\n'.join(next(s for s in d['content']['sections'] if s['key']=='sources')['paragraphs'])
        self.assertIn('Обработано 1 из 3',text)
        self.assertNotIn('"acceptance_granted":',text)

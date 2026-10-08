import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET
from engineering.local_app.store import Store, ReviewConflict
from engineering.local_app.files import preserve_file
from engineering.local_app.worker import Worker
from engineering.local_app.real_case import build as build_case

class Model:
    def chat(self,messages):
        return json.dumps(dict(status='UNCERTAINTY',summary='Controlled draft',observations=[],limitations=['Not accepted']))

class ConclusionTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.store=Store(self.tmp.name);self.sid=self.store.create_session('Объект теста')['id']
        self.source=preserve_file(self.store,self.sid,'source.txt','Высота 4 метра'.encode())
        job=self.store.enqueue(self.sid,'Проверить',[self.source['id']],mode='CORE_RUN',requested_checks=['report','calculation'])
        Worker(self.store,Model()).run_once()
        self.case=build_case(self.store,self.sid,job_id=job['id'],expected_revision=0,manifest={'TOR':[self.source['id']],'REPORT':[self.source['id']]})
    def module(self):
        from engineering.local_app import conclusions
        return conclusions
    def build(self,**kwargs):
        return self.module().build(self.store,self.sid,expected_revision=kwargs.pop('expected_revision',0),author='Проверяющий',**kwargs)
    def test_draft_sections_sources_and_no_acceptance(self):
        d=self.build(summary='Нужны данные расчёта')
        self.assertFalse(d['acceptance_granted']);self.assertEqual(d['final_audit'],'NOT_RUN')
        self.assertEqual(d['status'],'BLOCK');self.assertEqual(d['content']['label'],'ЧЕРНОВИК — НЕ ПРИНЯТО')
        sections={s['key'] for s in d['content']['sections']}
        self.assertEqual(sections,{'scope','sources','requirements','facts','normative','calculations','findings','summary','recommendations','limitations'})
        self.assertIn(self.source['sha256'],json.dumps(d['content'],ensure_ascii=False))
        self.assertIn('CALCULATION_DOMAIN_PACKET_MISSING',json.dumps(d['content']))
    def test_edits_history_restart_and_conflict(self):
        a=self.build(summary='Первый');b=self.build(expected_revision=1,summary='Второй')
        r=self.module().report(Store(self.store.root),self.sid)
        self.assertEqual(r['revision'],2);self.assertEqual(r['drafts'][0]['summary'],'Первый')
        self.assertEqual(r['drafts'][1]['summary'],'Второй');self.assertTrue(r['drafts'][1]['fresh'])
        with self.assertRaises(ReviewConflict):self.build(summary='Потерять правку')
    def test_changed_tz_blocks_export(self):
        self.build()
        from engineering.local_app.requirements import create_set
        create_set(self.store,self.sid,text='Новое требование')
        self.assertFalse(self.module().report(self.store,self.sid)['drafts'][-1]['fresh'])
        with self.assertRaises(ValueError):self.module().export(self.store,self.sid,revision=1,format='docx')
    def test_foreign_project_cannot_export_and_history_is_not_current(self):
        self.build();self.build(expected_revision=1)
        other=self.store.create_session()['id']
        with self.assertRaises(ValueError):self.module().export(self.store,other,revision=2,format='pdf')
        with self.assertRaises(ValueError):self.module().export(self.store,self.sid,revision=1,format='pdf')
    def test_tampered_content_blocks_export(self):
        d=self.build()
        with self.store.connection() as db:
            d['summary']='Подмена';db.execute('UPDATE conclusion_drafts SET record=? WHERE id=?',(json.dumps(d),d['id']))
        with self.assertRaises(ValueError):self.module().export(self.store,self.sid,revision=1,format='pdf')
    def test_original_mutation_blocks_export(self):
        self.build();Path(self.store.get_file(self.source['id'])['path']).write_text('Changed')
        with self.assertRaises(ValueError):self.module().export(self.store,self.sid,revision=1,format='docx')
    def test_author_control_chars_and_budget_validation(self):
        for kwargs in ({'summary':'bad\x00'},{'summary':'a'*20001},{'summary':None}):
            with self.assertRaises(ValueError):self.build(**kwargs)
        with self.assertRaises(ValueError):self.module().build(self.store,self.sid,expected_revision=0,author='')
    def test_docx_pdf_share_checked_content_and_escape(self):
        marker='Кириллица <script> & проверка'
        d=self.build(summary=marker,recommendations='Получить модель',limitations='Расчёт не выполнен')
        docx,mime=self.module().export(self.store,self.sid,revision=1,format='docx')
        with zipfile.ZipFile(io.BytesIO(docx)) as z:
            root=ET.fromstring(z.read('word/document.xml'))
            text='\n'.join(x.text or '' for x in root.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t'))
        self.assertIn(marker,text);self.assertIn(d['content_sha256'],text);self.assertIn('ЧЕРНОВИК',text)
        self.assertIn('wordprocessingml',mime)
        pdf,mime=self.module().export(self.store,self.sid,revision=1,format='pdf')
        import fitz
        with fitz.open(stream=pdf,filetype='pdf') as p:text=''.join(page.get_text() for page in p)
        self.assertIn(marker,text);self.assertIn('Получить модель',text);self.assertIn('ЧЕРНОВИК',text)
        self.assertEqual(mime,'application/pdf')
    def test_long_text_exports_without_omission(self):
        marker='Последняя строка сохранена'
        self.build(summary=('Длинный проверяемый черновик. '*300)+marker)
        pdf,_=self.module().export(self.store,self.sid,revision=1,format='pdf')
        import fitz
        with fitz.open(stream=pdf,filetype='pdf') as p:
            self.assertGreater(len(p),2);self.assertIn(marker,''.join(page.get_text() for page in p))

    def test_unbreakable_token_is_not_clipped(self):
        self.build(summary='А'*10000)
        pdf,_=self.module().export(self.store,self.sid,revision=1,format='pdf')
        import fitz
        with fitz.open(stream=pdf,filetype='pdf') as p:
            self.assertGreaterEqual(''.join(page.get_text() for page in p).count('А'),10000)

    def test_invalid_xml_unicode_is_rejected(self):
        for value in ('bad\ufffe','bad\uffff','bad\ud800'):
            with self.assertRaises(ValueError):self.build(summary=value)

    def test_revision_tampering_cannot_export(self):
        d=self.build()
        with self.store.connection() as db:
            d['revision']=987;db.execute('UPDATE conclusion_drafts SET record=? WHERE id=?',(json.dumps(d),d['id']))
        with self.assertRaises(ValueError):self.module().export(self.store,self.sid,revision=987,format='pdf')

    def test_exact_office_locator_and_specialist_limits_are_preserved(self):
        # Regression of independently reproduced real Office-location loss.
        from engineering.local_app.evidence import register
        register(self.store,self.sid,file_id=self.source['id'],quote='Высота 4 метра',statement='Кандидат факта')
        with self.store.connection() as db:
            row=db.execute('SELECT id,record FROM local_evidence WHERE session_id=?',(self.sid,)).fetchone()
            value=json.loads(row['record']);value['locator']={'sheet':'Нагрузки','cell':'A1'}
            value['source_binding']={'logical_unit':1,'locator':value['locator']}
            db.execute('UPDATE local_evidence SET record=? WHERE id=?',(json.dumps(value),row['id']))
        build_case(self.store,self.sid,job_id=self.case['job_id'],expected_revision=1)
        d=self.build();serialized=json.dumps(d['content'],ensure_ascii=False)
        self.assertIn('Нагрузки',serialized);self.assertIn('A1',serialized);self.assertIn('logical_unit',serialized)
        self.assertIn('Controlled draft',serialized);self.assertIn('Not accepted',serialized)

    def test_backup_restore_preserves_draft_history(self):
        self.build(summary='Первый');self.build(expected_revision=1,summary='Второй')
        from engineering.local_app.backup import create_backup,restore_backup
        archive=Path(self.tmp.name).parent/(Path(self.tmp.name).name+'-backup.zip')
        restored=Path(self.tmp.name).parent/(Path(self.tmp.name).name+'-restored')
        self.addCleanup(archive.unlink,missing_ok=True)
        import shutil
        self.addCleanup(shutil.rmtree,restored,True)
        create_backup(self.store.root,archive);restore_backup(archive,restored)
        state=self.module().report(Store(restored),self.sid)
        self.assertEqual(state['revision'],2);self.assertTrue(state['drafts'][-1]['fresh'])
        self.assertEqual(state['drafts'][-1]['summary'],'Второй')

if __name__=='__main__':unittest.main()

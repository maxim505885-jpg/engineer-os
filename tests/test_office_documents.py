import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from engineering.local_app.files import preserve_file
from engineering.local_app.store import Store
from engineering.local_app.worker import Worker

W='http://schemas.openxmlformats.org/wordprocessingml/2006/main'
S='http://schemas.openxmlformats.org/spreadsheetml/2006/main'


def package(parts):
    stream=io.BytesIO()
    with zipfile.ZipFile(stream,'w',zipfile.ZIP_DEFLATED) as z:
        for name,content in parts.items():z.writestr(name,content)
    return stream.getvalue()


def docx(text='Высота 4 м',extra=''):
    return package({'word/document.xml':f'<w:document xmlns:w="{W}"><w:body><w:p><w:r><w:t>{text}</w:t></w:r></w:p><w:tbl><w:tr><w:tc><w:p><w:r><w:t>Толщина</w:t></w:r></w:p></w:tc><w:tc><w:p><w:r><w:t>200 мм</w:t></w:r></w:p></w:tc></w:tr></w:tbl>{extra}<w:p><w:r><w:t>ПОСЛЕДНИЙ_АБЗАЦ</w:t></w:r></w:p></w:body></w:document>'})


def xlsx():
    return package({'xl/workbook.xml':f'<workbook xmlns="{S}" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Нагрузки" sheetId="1" r:id="rId1"/></sheets></workbook>',
        'xl/_rels/workbook.xml.rels':'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Target="worksheets/sheet1.xml" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet"/></Relationships>',
        'xl/worksheets/sheet1.xml':f'<worksheet xmlns="{S}"><sheetData><row r="1"><c r="A1" t="inlineStr"><is><t>Снег</t></is></c><c r="B1"><v>0.50</v></c><c r="C1"><f>B1*2</f><v>1.00</v></c><c r="D1"><f>B1*3</f></c></row></sheetData></worksheet>'})


class Model:
    def __init__(self,fail=None):self.calls=[];self.fail=fail
    def checkpoint_identity(self):return {'provider':'controlled','revision':'office-test-1'}
    def chat(self,messages):
        self.calls.append(messages)
        if len(self.calls)==self.fail:raise RuntimeError('offline')
        if messages[0]['content'].startswith('Назначенная роль:'):
            return json.dumps(dict(status='UNCERTAINTY',summary='Draft',observations=[],limitations=['Unverified']))
        return 'Draft'


class OfficeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.store=Store(Path(self.tmp.name));self.session=self.store.create_session()['id']

    def run_doc(self,name,data,core=False):
        try:f=preserve_file(self.store,self.session,name,data)
        except ValueError as e:self.fail('Office original must be accepted: '+str(e))
        job=self.store.enqueue(self.session,'Read all content',[f['id']],mode='CORE_RUN' if core else 'CHAT',requested_checks=['report'] if core else [])
        model=Model();Worker(self.store,model).run_once();result=self.store.snapshot(self.session)['jobs'][0]
        return f,job,model,result

    def test_docx_order_tables_and_exact_locators(self):
        original=docx()
        f,job,model,result=self.run_doc('report.docx',original)
        self.assertEqual(result['state'],'SUCCEEDED');self.assertIn('ПОСЛЕДНИЙ_АБЗАЦ',str(model.calls))
        records=self.store.analysis_receipts(self.session,job['id'])['records']
        refs=records[0]['refs'];self.assertTrue(all(r['page'] is None for r in refs))
        self.assertTrue(any(r['locator'].get('kind')=='table_cell' and r['locator']['column']==2 for r in refs))
        self.assertTrue(all(r['locator']['part']=='word/document.xml' for r in refs))
        self.assertIn('200 мм',str(model.calls));self.assertFalse(result['result']['acceptance_granted'])
        self.assertEqual(Path(self.store.get_file(f['id'])['path']).read_bytes(),original)

    def test_xlsx_formulas_cached_values_and_missing_cache_are_separate(self):
        _,job,model,result=self.run_doc('table.xlsx',xlsx())
        self.assertEqual(result['state'],'SUCCEEDED');calls=str(model.calls)
        for value in ['Нагрузки','C1','B1*2','1.00','D1','FORMULA_CACHE_MISSING']:self.assertIn(value,calls)
        self.assertNotIn('cached_value: 1.5',calls,'Formula must not be evaluated')
        refs=self.store.analysis_receipts(self.session,job['id'])['records'][0]['refs']
        self.assertTrue(any(r['locator'].get('cell')=='C1' for r in refs))

    def test_docx_core_uses_actual_coverage_not_pdf_preview(self):
        _,_,model,result=self.run_doc('report.docx',docx(),core=True)
        self.assertEqual(result['state'],'SUCCEEDED');self.assertIn('ПОСЛЕДНИЙ_АБЗАЦ',str(model.calls))
        source=result['result']['core_run']['source_context']['sources'][0]
        self.assertEqual(source['extraction_coverage']['method'],'DOCX');self.assertIsNone(source['extraction_coverage']['total_pages'])

    def test_malformed_office_original_retained_without_fabricated_text(self):
        for suffix in ['docx','xlsx']:
            session=self.store.create_session()['id']
            try:f=preserve_file(self.store,session,'bad.'+suffix,b'not a package')
            except ValueError as e:self.fail('Malformed original must be retained: '+str(e))
            self.store.enqueue(session,'Read',[f['id']]);model=Model();Worker(self.store,model).run_once()
            job=self.store.snapshot(session)['jobs'][0];self.assertEqual(job['state'],'FAILED');self.assertEqual(model.calls,[])
            self.assertEqual(Path(self.store.get_file(f['id'])['path']).read_bytes(),b'not a package')

    def test_zip_duplicate_members_and_entities_are_rejected(self):
        bad=package({'word/document.xml':f'<!DOCTYPE root [<!ENTITY x "secret">]><w:document xmlns:w="{W}"><w:body><w:p>&x;</w:p></w:body></w:document>'})
        _,_,model,result=self.run_doc('entities.docx',bad);self.assertEqual(result['state'],'FAILED');self.assertEqual(model.calls,[])

    def test_merged_table_and_unread_parts_are_disclosed(self):
        extra='<w:tbl><w:tr><w:tc><w:tcPr><w:gridSpan w:val="2"/></w:tcPr><w:p><w:r><w:t>merged</w:t></w:r></w:p></w:tc></w:tr></w:tbl><w:p><w:r><w:drawing/></w:r></w:p>'
        _,_,model,result=self.run_doc('merged.docx',docx(extra=extra))
        self.assertEqual(result['state'],'SUCCEEDED');self.assertIn('MERGED_CELL_UNVERIFIED',str(model.calls));self.assertIn('DRAWING_NOT_READ',str(model.calls))

    def test_doc_uses_separate_conversion_and_original_identity(self):
        from unittest.mock import patch
        self.assertTrue(hasattr(__import__('engineering.local_app.office',fromlist=['convert_doc']),'convert_doc'),'Controlled DOC adapter missing')
        original=b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'+b'controlled-doc'
        derived=docx();metadata=dict(original_sha256=__import__('hashlib').sha256(original).hexdigest(),derived_sha256=__import__('hashlib').sha256(derived).hexdigest(),converter='controlled',scope='DERIVED_UNVERIFIED',network_denied=True)
        with patch('engineering.local_app.office.convert_doc',return_value=(derived,metadata)):
            f,job,model,result=self.run_doc('report.doc',original)
        self.assertEqual(result['state'],'SUCCEEDED');self.assertEqual(Path(self.store.get_file(f['id'])['path']).read_bytes(),original)
        source=result['result']['document_analysis']['sources'][0]
        self.assertEqual(source['conversion']['derived_sha256'],metadata['derived_sha256'])
        self.assertTrue(all(r['locator']['scope']=='DERIVED_DOCX_LOCATION' for r in self.store.analysis_receipts(self.session,job['id'])['records'][0]['refs']))

    def test_doc_missing_converter_fails_without_native_fallback(self):
        from unittest.mock import patch
        with patch.dict('os.environ',{'ENGINEER_OS_DOC_CONVERTER':'/nonexistent/converter'}):
            _,_,model,result=self.run_doc('report.doc',b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'+b'controlled-doc')
        self.assertEqual(result['state'],'FAILED');self.assertEqual(model.calls,[])

    def test_office_model_failure_can_resume_same_job(self):
        data=docx(text='source '*2400);f=preserve_file(self.store,self.session,'large.docx',data)
        job=self.store.enqueue(self.session,'Read',[f['id']]);model=Model(fail=2);Worker(self.store,model).run_once()
        self.assertEqual(self.store.snapshot(self.session)['jobs'][0]['state'],'FAILED')
        self.store.resume_analysis(self.session,job['id'],model);model.fail=None;Worker(self.store,model).run_once()
        result=self.store.snapshot(self.session)['jobs'][0];self.assertEqual(result['state'],'SUCCEEDED')
        self.assertEqual(sum(c[-1]['content']==model.calls[0][-1]['content'] for c in model.calls),1)

    def test_doc_resume_reuses_verified_derivative_without_reconversion(self):
        from unittest.mock import patch
        import hashlib
        original=b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'+b'controlled-doc';converted=docx(text='source '*2400)
        metadata=dict(original_sha256=hashlib.sha256(original).hexdigest(),derived_sha256=hashlib.sha256(converted).hexdigest(),converter='controlled',scope='DERIVED_UNVERIFIED',network_denied=True)
        f=preserve_file(self.store,self.session,'large.doc',original);job=self.store.enqueue(self.session,'Read',[f['id']]);model=Model();worker=Worker(self.store,model);save=self.store.save_extraction_page
        def interrupt(child,record):save(child,record);worker.stop_event.set()
        with patch('engineering.local_app.office.convert_doc',return_value=(converted,metadata)) as converter:
            with patch.object(self.store,'save_extraction_page',interrupt):worker.run_once()
            self.store.resume_analysis(self.session,job['id'],model);Worker(self.store,model).run_once()
            self.assertEqual(converter.call_count,1,'Reconversion may change ZIP metadata and break checkpoints')
        self.assertEqual(self.store.snapshot(self.session)['jobs'][0]['state'],'SUCCEEDED')

    def test_office_evidence_does_not_fabricate_pdf_page(self):
        from engineering.local_app.evidence import register
        f=preserve_file(self.store,self.session,'report.docx',docx())
        with self.assertRaisesRegex(ValueError,'Office'):
            register(self.store,self.session,file_id=f['id'],quote='Высота 4 м',statement='Source',page=1)

    def test_word_special_tokens_preserved_and_font_symbols_blocked(self):
        from engineering.local_app.office import read
        extra='<w:p><w:r><w:t>A</w:t><w:noBreakHyphen/><w:t>B</w:t><w:softHyphen/><w:t>C</w:t><w:sym w:font="Symbol" w:char="F0C6"/><w:t>16</w:t></w:r></w:p>'
        units,_=read(docx(extra=extra),'docx')
        item=next(u for u in units if 'A' in u['text'])
        self.assertIn('A\u2011B\u00adC',item['text'])
        self.assertIn('[WORD_SYMBOL font=Symbol char=F0C6]',item['text'])
        self.assertIn('SYMBOL_NOT_DECODED',item['limitations'])

    def test_xlsx_shared_and_inline_phonetic_annotations_are_not_values(self):
        from engineering.local_app.office import read
        with zipfile.ZipFile(io.BytesIO(xlsx())) as z:parts={n:z.read(n).decode() for n in z.namelist()}
        parts['xl/sharedStrings.xml']=f'<sst xmlns="{S}"><si><t>東京</t><rPh sb="0" eb="2"><t>とうきょう</t></rPh></si></sst>'
        parts['xl/worksheets/sheet1.xml']=f'<worksheet xmlns="{S}"><sheetData><row r="1"><c r="A1" t="s"><v>0</v></c><c r="B1" t="inlineStr"><is><r><t>東京</t></r><rPh sb="0" eb="2"><t>とうきょう</t></rPh></is></c></row></sheetData></worksheet>'
        units,_=read(package(parts),'xlsx')
        self.assertEqual([json.loads(u['text'])['stored_value'] for u in units],['東京','東京'])

    def test_coverage_manifest_names_sheets_tables_and_visible_remainders(self):
        for name,data in [('report.docx',docx()),('table.xlsx',xlsx())]:
            _,_,_,result=self.run_doc(name,data)
            source=result['result']['document_analysis']['sources'][0]
            manifest=source['coverage_manifest']
            self.assertEqual(manifest['processed_units'],manifest['declared_units'])
            self.assertEqual(manifest['unprocessed_units'],0)
            self.assertFalse(manifest['acceptance_granted'])
            self.assertTrue(manifest['sheets'] if name.endswith('xlsx') else manifest['tables'])
            self.assertTrue(manifest['limitations'])

import io
import json
import unittest
import zipfile
from xml.etree import ElementTree as ET
from engineering.local_app.office import read
from tests.test_office_documents import docx,xlsx,package
from tests import test_office_documents as fixtures

M='http://schemas.openxmlformats.org/officeDocument/2006/math'


class OfficeStructureTests(unittest.TestCase):
    def test_merge_attribute_namespaces_cannot_overwrite_word_span(self):
        extra='<w:tbl><w:tr><w:tc><w:tcPr><w:gridSpan xmlns:x="urn:extension" w:val="2" x:val="other"/></w:tcPr><w:p/></w:tc></w:tr></w:tbl>'
        units,_=read(docx(extra=extra),'docx');cell=next(u for u in units if u['locator'].get('table')==2)
        attrs=cell['locator']['declared_merge']['gridSpan']
        self.assertEqual(attrs.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val'),'2')
        self.assertEqual(attrs.get('{urn:extension}val'),'other')

    def test_equation_fragment_excludes_sibling_tail_text(self):
        extra=f'<w:p xmlns:m="{M}"><m:oMath><m:r><m:t>42</m:t></m:r></m:oMath>OUTSIDE_FORMULA</w:p>'
        units,_=read(docx(extra=extra),'docx');equation=next(u for u in units if u['locator']['kind']=='equation')
        xml=json.loads(equation['text'])['normalized_omml']
        self.assertNotIn('OUTSIDE_FORMULA',xml);self.assertEqual(ET.fromstring(xml).tag,'{'+M+'}oMath')

    def test_word_equation_keeps_fraction_structure_and_literal_tokens(self):
        extra=f'<w:p xmlns:m="{M}"><m:oMath><m:f><m:num><m:r><m:t>12</m:t></m:r></m:num><m:den><m:r><m:t>3</m:t></m:r></m:den></m:f></m:oMath></w:p>'
        units,_=read(docx(extra=extra),'docx')
        equations=[u for u in units if u['locator']['kind']=='equation']
        self.assertEqual(len(equations),1)
        x=json.loads(equations[0]['text'])
        self.assertEqual(x['literal_tokens'],['12','3'])
        self.assertIn('num',x['normalized_omml']);self.assertIn('den',x['normalized_omml'])
        self.assertFalse(x['evaluated']);self.assertFalse(x['layout_verified'])
        self.assertEqual(equations[0]['locator']['parent_kind'],'paragraph')
        self.assertIn('EQUATION_NOT_READ',equations[0]['limitations'])

    def test_word_merged_cell_preserves_declared_span_and_merge_attributes(self):
        extra='<w:tbl><w:tr><w:tc><w:tcPr><w:gridSpan w:val="2"/><w:vMerge w:val="restart"/></w:tcPr><w:p><w:r><w:t>Top</w:t></w:r></w:p></w:tc></w:tr><w:tr><w:tc><w:tcPr><w:gridSpan w:val="2"/><w:vMerge/></w:tcPr><w:p/></w:tc></w:tr></w:tbl>'
        units,_=read(docx(extra=extra),'docx');cells=[u for u in units if u['locator'].get('table')==2]
        val='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val'
        self.assertEqual(cells[0]['locator'].get('declared_merge'),dict(gridSpan={val:'2'},vMerge={val:'restart'}))
        self.assertEqual(cells[1]['locator'].get('declared_merge'),dict(gridSpan={val:'2'},vMerge={}))
        self.assertIn('XML_CELL_ORDINAL',cells[0]['text'])

    def test_xlsx_merge_declaration_without_materialized_cells_is_preserved(self):
        with zipfile.ZipFile(io.BytesIO(xlsx())) as z:parts={n:z.read(n).decode() for n in z.namelist()}
        part='xl/worksheets/sheet1.xml';parts[part]=parts[part].replace('</worksheet>','<mergeCells count="1"><mergeCell ref="F10:H12"/></mergeCells></worksheet>')
        units,_=read(package(parts),'xlsx');merged=[u for u in units if u['locator']['kind']=='merged_range']
        self.assertEqual(len(merged),1);self.assertEqual(merged[0]['locator']['range'],'F10:H12')
        self.assertFalse(json.loads(merged[0]['text'])['values_propagated'])
        self.assertEqual(merged[0]['locator']['part'],part)


class OfficeStructurePipelineTests(unittest.TestCase):
    # Reuse the existing real Store/Worker/model harness without duplicating tests.
    setUp=fixtures.OfficeTests.setUp
    run_doc=fixtures.OfficeTests.run_doc
    def test_equation_structure_reaches_model_and_receipt_without_acceptance(self):
        extra=f'<w:p xmlns:m="{M}"><m:oMath><m:r><m:t>42</m:t></m:r></m:oMath></w:p>'
        _,job,model,result=self.run_doc('math.docx',docx(extra=extra))
        self.assertIn('literal_tokens',str(model.calls))
        refs=self.store.analysis_receipts(self.session,job['id'])['records'][0]['refs']
        self.assertTrue(any(r['locator'].get('kind')=='equation' and r['page'] is None for r in refs))
        self.assertFalse(result['result']['acceptance_granted'])

    def test_manifest_counts_formula_cells_without_evaluating_them(self):
        _,_,_,result=self.run_doc('formulas.xlsx',xlsx())
        c=result['result']['document_analysis']['sources'][0]['coverage_manifest']['source_components']
        self.assertEqual(c.get('xlsx_formula_cells'),2)
        self.assertFalse(c['formulas_evaluated'])

    def test_shared_formula_followers_are_counted_even_without_formula_text(self):
        with zipfile.ZipFile(io.BytesIO(xlsx())) as z:parts={n:z.read(n).decode() for n in z.namelist()}
        part='xl/worksheets/sheet1.xml'
        parts[part]=parts[part].replace('</row>','<c r="E1"><f t="shared" si="0"/><v>2</v></c></row>')
        _,_,_,result=self.run_doc('shared.xlsx',package(parts))
        c=result['result']['document_analysis']['sources'][0]['coverage_manifest']['source_components']
        self.assertEqual(c['xlsx_formula_cells'],3)

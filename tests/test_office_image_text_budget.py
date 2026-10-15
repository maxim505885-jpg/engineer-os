"""Source locator metadata must not consume the document text checkpoint budget."""
import io
import zipfile
import unittest
from unittest.mock import patch
from engineering.local_app import office
from tests.test_emf_native_text import emf,text_record,vector_doc
from tests import test_office_documents as fixtures
package=fixtures.package


def repeated_vector_doc(count=70):
    data=vector_doc(emf([text_record('Метка источника '+str(n)) for n in range(count)]))
    with zipfile.ZipFile(io.BytesIO(data)) as z:parts={n:z.read(n) for n in z.namelist()}
    parts['word/document.xml']=parts['word/document.xml'].replace(b'</w:body>','<w:p><w:r><w:t>КОНЕЦ_ДОКУМЕНТА</w:t></w:r></w:p></w:body>'.encode())
    return package(parts)


class ImageTextBudgetTests(unittest.TestCase):
    setUp=fixtures.OfficeTests.setUp
    run_doc=fixtures.OfficeTests.run_doc

    def test_all_native_records_remain_with_compact_text_and_exact_full_locators(self):
        units,_=office.read(repeated_vector_doc(),'docx')
        first=units[0]
        self.assertLess(len(first['text']),10000,'Repeated record geometry currently consumes source text budget')
        records=first['locator']['images'][0]['native_emf']['text_records']
        self.assertEqual(len(records),70)
        for record in records:
            self.assertIn(record['text'],first['text'])
            self.assertIn('[EMF 1@'+str(record['record_offset'])+']',first['text'])
            self.assertIn('string_offset',record)
        self.assertIn('EMF_GRAPHICS_NOT_RENDERED',first['limitations'])

    def test_store_reads_last_paragraph_without_spending_text_budget_on_record_geometry(self):
        with patch('engineering.local_app.extraction.MAX_TOTAL_TEXT',10000):
            _,job,model,result=self.run_doc('vector-budget.docx',repeated_vector_doc())
        source=result['result']['document_analysis']['sources'][0]
        self.assertEqual(source['processed_units'],source['total_units'],'Tail currently omitted because source metadata exhausts budget')
        self.assertFalse(source['budget_exhausted'])
        self.assertIn('КОНЕЦ_ДОКУМЕНТА',str(model.calls))
        records=self.store.analysis_receipts(self.session,job['id'])['records']
        ref=next(ref for record in records for ref in record['refs'] if ref.get('logical_unit')==2)
        checkpoint=self.store.extraction_page(self.session,ref['source_job'],2)
        self.assertEqual(checkpoint['blocks'][0]['text'],'КОНЕЦ_ДОКУМЕНТА')
        self.assertFalse(result['result']['acceptance_granted'])

    def test_glyph_indices_are_not_transcribed_as_unicode(self):
        units,_=office.read(vector_doc(emf([text_record('НЕЛЬЗЯ_ВЫДУМАТЬ',16)])),'docx')
        self.assertNotIn('НЕЛЬЗЯ_ВЫДУМАТЬ',units[0]['text'])
        self.assertIsNone(units[0]['locator']['images'][0]['native_emf']['text_records'][0]['text'])

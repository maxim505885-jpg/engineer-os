"""Source binary offsets must establish native text, never rendered table semantics."""
import io
import json
import struct
import unittest
from unittest.mock import patch
from engineering.local_app import office
from tests.test_word_images import image_doc
from tests.test_office_documents import package
from tests import test_office_documents as fixtures


def record(kind,payload):
    payload+=b'\0'*((-len(payload))%4)
    return struct.pack('<II',kind,len(payload)+8)+payload


def text_record(text='Толщина 200 мм',flags=0):
    raw=text.encode('utf-16le');count=len(raw)//2
    # EMR_EXTTEXTOUTW fixed structure, followed by UTF16-LE buffer.
    fixed=struct.pack('<4iI2f2iIII4iI',0,0,-1,-1,1,1,1,12,34,count,76,flags,0,0,-1,-1,0)
    return record(84,fixed+raw)


def emf(records=None):
    records=[text_record()] if records is None else records
    eof=record(14,struct.pack('<III',0,0,20))
    body=b''.join(records)+eof
    header=struct.pack('<II8i4I2H3I4i',1,88,0,0,100,60,0,0,1000,600,0x464d4520,0x10000,88+len(body),len(records)+2,1,0,0,0,0,100,60,25,15)
    return header+body


def vector_doc(data):
    with __import__('zipfile').ZipFile(io.BytesIO(image_doc(image=data))) as z:parts={n:z.read(n) for n in z.namelist()}
    parts['word/_rels/document.xml.rels']=parts['word/_rels/document.xml.rels'].replace(b'source.png',b'source.emf')
    parts['word/media/source.emf']=parts.pop('word/media/source.png')
    return package(parts)


def mixed_doc(vector=None):
    with __import__('zipfile').ZipFile(io.BytesIO(image_doc())) as z:parts={n:z.read(n) for n in z.namelist()}
    drawing=b'<w:drawing><a:blip xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" r:embed="vector"/></w:drawing>'
    parts['word/document.xml']=parts['word/document.xml'].replace(b'</w:p>',drawing+b'</w:p>',1)
    relation=b'<Relationship Id="vector" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/source.emf"/>'
    parts['word/_rels/document.xml.rels']=parts['word/_rels/document.xml.rels'].replace(b'</Relationships>',relation+b'</Relationships>')
    parts['word/media/source.emf']=emf() if vector is None else vector
    return package(parts)


class NativeEMFTests(unittest.TestCase):
    def parse(self,data):
        from engineering.local_app import emf_text
        return emf_text.read(data)

    def test_docx_preserves_native_vector_text_with_image_and_record_identity(self):
        units,_=office.read(vector_doc(emf()),'docx')
        self.assertIn('Толщина 200 мм',units[0]['text'],'EMF text currently omitted')
        self.assertEqual(len(units),1)
        payload=units[0]['locator']['images'][0].get('native_emf',{})
        self.assertEqual(payload.get('status'),'PARSED_SOURCE_RECORDS')
        item=payload['text_records'][0]
        self.assertEqual((item['record_offset'],item['string_offset'],item['reference_logical_units']),(88,164,[12,34]))
        self.assertEqual(item['text'],'Толщина 200 мм')
        self.assertFalse(payload['layout_verified']);self.assertFalse(payload['content_verified'])

    def test_glyph_indices_are_preserved_without_fake_unicode(self):
        result=self.parse(emf([text_record('ABC',16)]))
        item=result['text_records'][0]
        self.assertIsNone(item['text']);self.assertEqual(item['glyph_indices'],[65,66,67])
        self.assertIn('GLYPH_INDICES_NOT_DECODED',result['limitations'])

    def test_unicode_surrogates_are_counted_as_source_code_units(self):
        result=self.parse(emf([text_record('A😀Б')]))
        self.assertEqual(result['text_records'][0]['code_units'],4)
        self.assertEqual(result['text_records'][0]['text'],'A😀Б')

    def test_header_truncation_count_and_record_overflow_are_rejected(self):
        from engineering.local_app import emf_text
        good=emf()
        variants=[good[:-1],good+b'extra',good[:52]+struct.pack('<I',999)+good[56:],good[:92]+struct.pack('<I',0xfffffff0)+good[96:]]
        for data in variants:
            with self.subTest(size=len(data)),self.assertRaises(emf_text.EMFError):self.parse(data)

    def test_text_cannot_point_into_fixed_record_header(self):
        from engineering.local_app import emf_text
        data=bytearray(emf());struct.pack_into('<I',data,88+48,4)
        with self.assertRaises(emf_text.EMFError):self.parse(bytes(data))

    def test_unknown_text_and_comments_remain_explicitly_unread(self):
        result=self.parse(emf([record(83,b'unknown'),record(70,b'comment')]))
        self.assertEqual(result['text_records'],[])
        self.assertIn('OTHER_TEXT_RECORDS_NOT_DECODED',result['limitations'])
        self.assertIn('COMMENT_CONTENT_NOT_READ',result['limitations'])

    def test_invalid_emf_does_not_supply_native_observations(self):
        units,_=office.read(vector_doc(b'broken metafile'),'docx')
        payload=units[0]['locator']['images'][0].get('native_emf',{})
        self.assertEqual(payload.get('status'),'UNAVAILABLE')
        self.assertNotIn('text_records',payload)

    def test_native_emf_limits_stop_before_large_text_allocation(self):
        from engineering.local_app import emf_text
        with patch.object(emf_text,'MAX_RECORDS',2),self.assertRaises(emf_text.EMFError):self.parse(emf())
        with patch.object(emf_text,'MAX_TEXT_CODE_UNITS',1),self.assertRaises(emf_text.EMFError):self.parse(emf())

    def test_invalid_unicode_and_spacing_span_are_rejected(self):
        from engineering.local_app import emf_text
        good=bytearray(emf([text_record('A')]))
        bad_unicode=good.copy();bad_unicode[164:166]=b'\x00\xd8'
        bad_spacing=good.copy();struct.pack_into('<I',bad_spacing,88+72,76)
        for data in [bad_unicode,bad_spacing]:
            with self.assertRaises(emf_text.EMFError):self.parse(data)

    def test_package_reference_budget_and_parser_limit_fail_closed(self):
        from engineering.local_app import emf_text
        for key in ['MAX_REFERENCE_JSON_BYTES','MAX_TEXT_RECORDS']:
            with patch.object(emf_text,key,0),self.assertRaises(office.OfficeError):office.read(vector_doc(emf()),'docx')


class NativePipelineTests(unittest.TestCase):
    setUp=fixtures.OfficeTests.setUp
    run_doc=fixtures.OfficeTests.run_doc
    def test_native_text_cannot_bypass_model_budget_through_source_metadata(self):
        tail='UNSTORED_TAIL_MARKER'
        _,job,model,result=self.run_doc('long-vector.docx',vector_doc(emf([text_record('X'*25000+tail)])))
        self.assertEqual(result['state'],'SUCCEEDED')
        self.assertTrue(result['result']['document_analysis']['text_omitted'])
        self.assertNotIn(tail,str(model.calls),'Unstored EMF tail must not enter inference via locators')
        receipt=self.store.analysis_receipts(self.session,job['id'])['records'][0]
        self.assertIn(tail,receipt['refs'][0]['locator']['images'][0]['native_emf']['text_records'][0]['text'])
    def test_native_image_text_reaches_model_and_bound_receipt_without_acceptance(self):
        original=vector_doc(emf());file,job,model,result=self.run_doc('vector.docx',original)
        self.assertEqual(result['state'],'SUCCEEDED');self.assertIn('Толщина 200 мм',str(model.calls))
        ref=self.store.analysis_receipts(self.session,job['id'])['records'][0]['refs'][0]
        self.assertEqual(ref['locator']['images'][0]['part'],'word/media/source.emf')
        self.assertIsNone(ref['page']);self.assertFalse(result['result']['acceptance_granted'])
        source=result['result']['document_analysis']['sources'][0]['coverage_manifest']['source_components']
        self.assertEqual(source['emf_text_records'],1)
        from pathlib import Path
        self.assertEqual(Path(self.store.get_file(file['id'])['path']).read_bytes(),original)

"""Omitting auxiliary parts must lose these real source/receipt assertions."""
import io
import json
import zipfile
import unittest
from unittest.mock import patch
from engineering.local_app import office
from tests.test_office_documents import docx, package, W
from tests import test_office_documents as fixtures


def source(parts):
    with zipfile.ZipFile(io.BytesIO(docx())) as z:
        base={name:z.read(name) for name in z.namelist()}
    return package(dict(base,**parts))


def word(root,body):
    return f'<w:{root} xmlns:w="{W}">{body}</w:{root}>'


def paragraph(text):
    return f'<w:p><w:r><w:t>{text}</w:t></w:r></w:p>'


class AuxiliaryReaderTests(unittest.TestCase):
    def test_header_footer_and_notes_keep_part_and_note_identity(self):
        parts={'word/header1.xml':word('hdr',paragraph('HEADER_ACTUAL')),
               'word/footer2.xml':word('ftr',paragraph('FOOTER_ACTUAL')),
               'word/footnotes.xml':word('footnotes','<w:footnote w:id="7">'+paragraph('FOOTNOTE_ACTUAL')+'</w:footnote>'),
               'word/endnotes.xml':word('endnotes','<w:endnote w:id="11">'+paragraph('ENDNOTE_ACTUAL')+'</w:endnote>')}
        units,limits=office.read(source(parts),'docx')
        for part,text in zip(parts,['HEADER_ACTUAL','FOOTER_ACTUAL','FOOTNOTE_ACTUAL','ENDNOTE_ACTUAL']):
            item=next((u for u in units if text==u['text']),None)
            self.assertIsNotNone(item,part)
            self.assertEqual(item['locator']['part'],part)
            self.assertEqual(item['locator']['scope'],'PACKAGE_PART_PLACEMENT_UNVERIFIED')
            self.assertIn('AUXILIARY_PLACEMENT_UNVERIFIED',item['limitations'])
            if 'notes.xml' in part:self.assertEqual(item['locator']['note_id'],'7' if 'footnotes' in part else '11')
        self.assertNotIn('HEADERS_FOOTNOTES_NOT_READ',limits)
        self.assertIn('LAYOUT_NOT_VERIFIED',limits)

    def test_auxiliary_tables_and_equations_keep_exact_parent(self):
        table='<w:tbl><w:tblGrid><w:gridCol/></w:tblGrid><w:tr><w:tc>'+paragraph('NOTE_CELL')+'</w:tc></w:tr></w:tbl>'
        equation='<w:p xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math"><m:oMath><m:r><m:t>42</m:t></m:r></m:oMath></w:p>'
        units,_=office.read(source({'word/footnotes.xml':word('footnotes','<w:footnote w:id="7">'+table+equation+'</w:footnote>')}),'docx')
        cell=next((u for u in units if u['text']=='NOTE_CELL'),None)
        self.assertIsNotNone(cell)
        self.assertEqual(cell['locator']['note_id'],'7')
        self.assertEqual(cell['locator']['source_grid']['grid_columns'],[1,1])
        eq=next(u for u in units if u['locator']['kind']=='equation')
        self.assertEqual(eq['locator']['note_id'],'7')
        self.assertFalse(json.loads(eq['text'])['evaluated'])

    def test_relationship_targets_with_nonstandard_paths_are_read(self):
        rels='<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="r1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/footnotes" Target="notes/footnotes.xml"/></Relationships>'
        units,_=office.read(source({'word/_rels/document.xml.rels':rels,'word/notes/footnotes.xml':word('footnotes','<w:footnote w:id="7">'+paragraph('CUSTOM_NOTE')+'</w:footnote>')}),'docx')
        note=next((u for u in units if u['text']=='CUSTOM_NOTE'),None)
        self.assertIsNotNone(note)
        self.assertEqual(note['locator']['part'],'word/notes/footnotes.xml')

    def test_external_and_missing_auxiliary_targets_are_disclosed(self):
        for attrs in ['Target="https://example.invalid/note.xml" TargetMode="External"','Target="notes/missing.xml"']:
            rels='<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="r1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/footnotes" '+attrs+'/></Relationships>'
            with self.subTest(attrs=attrs):
                _,limits=office.read(source({'word/_rels/document.xml.rels':rels}),'docx')
                self.assertIn('HEADERS_FOOTNOTES_NOT_READ',limits)

    def test_empty_auxiliary_part_and_separator_are_visible(self):
        units,_=office.read(source({'word/header1.xml':word('hdr',''),
                                   'word/footnotes.xml':word('footnotes','<w:footnote w:id="-1" w:type="separator"><w:p/></w:footnote>')}),'docx')
        empty=[u for u in units if u['locator'].get('component')=='header']
        self.assertEqual(len(empty),1)
        separator=next(u for u in units if u['locator'].get('note_id')=='-1')
        self.assertEqual(separator['locator']['note_type'],'separator')

    def test_duplicate_note_ids_and_wrong_root_fail_closed(self):
        for body in [word('footnotes','<w:footnote w:id="7"/><w:footnote w:id="7"/>'),word('footnotes','<w:footnote w:id="7"/><w:footnote w:id="007"/>'),word('hdr',paragraph('wrong'))]:
            with self.subTest(body=body), self.assertRaises(office.OfficeError):
                office.read(source({'word/footnotes.xml':body}),'docx')

    def test_auxiliary_xml_entities_and_aggregate_limits_are_enforced(self):
        malicious='<!DOCTYPE hdr [<!ENTITY x "unsafe">]>'+word('hdr',paragraph('&x;'))
        with self.assertRaises(office.OfficeError):office.read(source({'word/header1.xml':malicious}),'docx')
        with patch.object(office,'MAX_AUXILIARY_PARTS',1,create=True),self.assertRaises(office.OfficeError):
            office.read(source({'word/header1.xml':word('hdr',paragraph('h')),'word/footer1.xml':word('ftr',paragraph('f'))}),'docx')


class AuxiliaryPipelineTests(unittest.TestCase):
    setUp=fixtures.OfficeTests.setUp
    run_doc=fixtures.OfficeTests.run_doc
    def test_auxiliary_content_reaches_model_receipts_and_separate_table_inventory(self):
        table='<w:tbl><w:tblGrid><w:gridCol/></w:tblGrid><w:tr><w:tc>'+paragraph('HEADER_CELL')+'</w:tc></w:tr></w:tbl>'
        original=source({'word/header1.xml':word('hdr',table),
                         'word/footnotes.xml':word('footnotes','<w:footnote w:id="7">'+paragraph('NOTE_ACTUAL')+'</w:footnote>')})
        file,job,model,result=self.run_doc('auxiliary.docx',original)
        self.assertEqual(result['state'],'SUCCEEDED')
        self.assertIn('HEADER_CELL',str(model.calls));self.assertIn('NOTE_ACTUAL',str(model.calls))
        refs=self.store.analysis_receipts(self.session,job['id'])['records'][0]['refs']
        self.assertTrue(any(r['locator'].get('note_id')=='7' and r['page'] is None for r in refs))
        manifest=result['result']['document_analysis']['sources'][0]['coverage_manifest']
        self.assertEqual(len(manifest['tables']),2)
        self.assertEqual({t['part'] for t in manifest['tables']},{'word/document.xml','word/header1.xml'})
        self.assertEqual(manifest['source_components']['auxiliary_parts'],['word/footnotes.xml','word/header1.xml'])
        self.assertFalse(manifest['acceptance_granted']);self.assertFalse(result['result']['acceptance_granted'])
        from pathlib import Path
        self.assertEqual(Path(self.store.get_file(file['id'])['path']).read_bytes(),original)

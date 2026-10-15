"""Cached Word field results must stay unverified across XML unit boundaries."""
import unittest
from xml.etree import ElementTree as ET
from engineering.local_app import office

W = office.W


def body(content):
    return ET.fromstring('<w:body xmlns:w="'+W[1:-1]+'">'+content+'</w:body>')


BEGIN = '<w:r><w:fldChar w:fldCharType="begin"/></w:r>'
SEPARATE = '<w:r><w:fldChar w:fldCharType="separate"/></w:r>'
END = '<w:r><w:fldChar w:fldCharType="end"/></w:r>'


class WordFieldContextTests(unittest.TestCase):
    def test_cached_result_between_paragraph_markers_is_never_plain_text(self):
        xml = body('<w:p>'+BEGIN+'<w:r><w:instrText> TOC </w:instrText></w:r>'+SEPARATE+
                   '</w:p><w:p><w:r><w:t>Cached section 12</w:t></w:r></w:p><w:p>'+END+
                   '</w:p><w:p><w:r><w:t>Ordinary paragraph</w:t></w:r></w:p>')
        units = office.word_container_units(xml, 'word/document.xml')
        cached = next(u for u in units if u['text'] == 'Cached section 12')
        self.assertIn('FIELD_NOT_EVALUATED', cached['limitations'])
        ordinary = next(u for u in units if u['text'] == 'Ordinary paragraph')
        self.assertNotIn('FIELD_NOT_EVALUATED', ordinary['limitations'])

    def test_field_marker_only_unit_is_preserved_and_flagged(self):
        units = office.word_container_units(body('<w:p>'+BEGIN+SEPARATE+END+'</w:p>'), 'word/document.xml')
        self.assertEqual(len(units), 1)
        self.assertIn('FIELD_NOT_EVALUATED', units[0]['limitations'])

    def test_nested_field_end_does_not_clear_outer_cached_result(self):
        xml = body('<w:p>'+BEGIN+SEPARATE+'</w:p><w:p>'+BEGIN+SEPARATE+
                   '<w:r><w:t>nested</w:t></w:r>'+END+'</w:p><w:p><w:r><w:t>outer cache</w:t></w:r></w:p>'+
                   '<w:p>'+END+'</w:p>')
        units = office.word_container_units(xml, 'word/document.xml')
        self.assertIn('FIELD_NOT_EVALUATED', next(u for u in units if u['text'] == 'outer cache')['limitations'])

    def test_field_crossing_table_cells_keeps_both_values_unverified(self):
        xml = body('<w:tbl><w:tblGrid><w:gridCol/><w:gridCol/></w:tblGrid><w:tr>'+
                   '<w:tc><w:p>'+BEGIN+SEPARATE+'<w:r><w:t>A</w:t></w:r></w:p></w:tc>'+
                   '<w:tc><w:p><w:r><w:t>B</w:t></w:r>'+END+'</w:p></w:tc></w:tr></w:tbl>')
        units = office.word_container_units(xml, 'word/document.xml')
        self.assertEqual([u['text'] for u in units], ['A', 'B'])
        self.assertTrue(all('FIELD_NOT_EVALUATED' in u['limitations'] for u in units))

    def test_unclosed_or_orphan_field_is_reported_without_inventing_result(self):
        for content in ('<w:p>'+BEGIN+'</w:p><w:p><w:r><w:t>cache</w:t></w:r></w:p>',
                        '<w:p>'+END+'<w:r><w:t>orphan</w:t></w:r></w:p>'):
            with self.subTest(content=content):
                units = office.word_container_units(body(content), 'word/document.xml')
                self.assertTrue(all('FIELD_STRUCTURE_UNVERIFIED' in u['limitations'] for u in units))

    def test_simple_field_does_not_leak_into_following_paragraph(self):
        xml = body('<w:p><w:fldSimple w:instr="PAGE"><w:r><w:t>7</w:t></w:r></w:fldSimple></w:p>'+
                   '<w:p><w:r><w:t>ordinary</w:t></w:r></w:p>')
        units = office.word_container_units(xml, 'word/document.xml')
        self.assertIn('FIELD_NOT_EVALUATED', units[0]['limitations'])
        self.assertNotIn('FIELD_NOT_EVALUATED', units[1]['limitations'])

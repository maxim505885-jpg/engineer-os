import unittest
from engineering.local_app.office import read
from tests.test_office_documents import docx


def table(rows,columns=3):
    return '<w:tbl><w:tblGrid>'+('<w:gridCol/>'*columns)+'</w:tblGrid>'+rows+'</w:tbl>'

def cell(text='',props=''):
    return '<w:tc><w:tcPr>'+props+'</w:tcPr><w:p><w:r><w:t>'+text+'</w:t></w:r></w:p></w:tc>'

class WordGridTests(unittest.TestCase):
    def cells(self,xml):
        return [u for u in read(docx(extra=xml),'docx')[0] if u['locator'].get('table')==2 and u['locator']['kind']=='table_cell']

    def test_nested_table_native_text_not_lost_without_claiming_layout(self):
        inner=table('<w:tr>'+cell('Inner value')+'</w:tr>',1)
        outer='<w:tbl><w:tblGrid><w:gridCol/></w:tblGrid><w:tr><w:tc><w:p><w:r><w:t>Outer</w:t></w:r></w:p>'+inner+'</w:tc></w:tr></w:tbl>'
        units=self.cells(outer)
        self.assertEqual(len(units),1)
        self.assertIn('Outer',units[0]['text'])
        self.assertIn('[NESTED_TABLE_TEXT_UNVERIFIED]',units[0]['text'])
        self.assertIn('Inner value',units[0]['text'])
        self.assertIn('NESTED_TABLE_UNVERIFIED',units[0]['limitations'])

    def test_vertical_continuations_keep_original_text_and_exact_anchor(self):
        span='<w:gridSpan w:val="2"/>'
        rows='<w:tr>'+cell('A',span+'<w:vMerge w:val="restart"/>')+cell('B')+'</w:tr>'
        rows+='<w:tr>'+cell('C',span+'<w:vMerge/>')+cell('D')+'</w:tr>'
        units=self.cells(table(rows));a=units[2]['locator']['source_grid']
        self.assertEqual(a['grid_columns'],[1,2]);self.assertEqual(a['vertical_anchor'],{'row':1,'column':1})
        self.assertEqual(a['status'],'CONSISTENT_SOURCE_STRUCTURE');self.assertFalse(a['values_propagated']);self.assertFalse(a['layout_verified'])
        self.assertTrue(units[2]['text'].startswith('C\n'));self.assertIn('MERGED_CELL_UNVERIFIED',units[2]['limitations'])
        self.assertEqual(units[3]['locator']['source_grid']['grid_columns'],[3,3])

    def test_row_leading_and_trailing_grid_gaps_are_not_cells(self):
        rows='<w:tr><w:trPr><w:gridBefore w:val="1"/><w:gridAfter w:val="1"/></w:trPr>'+cell('A')+'</w:tr>'
        grid=self.cells(table(rows))[0]['locator']['source_grid']
        self.assertEqual(grid['grid_columns'],[2,2]);self.assertEqual(grid['row_grid_columns'],3)
        self.assertEqual(grid['status'],'CONSISTENT_SOURCE_STRUCTURE')

    def test_orphan_or_changed_width_vertical_continue_never_inherits_anchor(self):
        for rows in ['<w:tr>'+cell('A','<w:vMerge/>')+cell('B')+cell('C')+'</w:tr>',
                     '<w:tr>'+cell('A','<w:gridSpan w:val="2"/><w:vMerge w:val="restart"/>')+cell('B')+'</w:tr><w:tr>'+cell('C','<w:vMerge/>')+cell('D')+cell('E')+'</w:tr>']:
            grid=next(u['locator']['source_grid'] for u in self.cells(table(rows)) if 'ORPHAN_VERTICAL_CONTINUE' in u['locator']['source_grid']['issues'])
            self.assertIsNone(grid['vertical_anchor']);self.assertEqual(grid['status'],'UNRESOLVED_SOURCE_STRUCTURE')

    def test_unsupported_or_invalid_declarations_fail_closed(self):
        for props in ['<w:gridSpan w:val="0"/>','<w:gridSpan w:val="99999999999999999999"/>','<w:hMerge w:val="restart"/>','<w:vMerge w:val="bad"/>','<w:gridSpan w:val="1"/><w:gridSpan w:val="2"/>']:
            units=self.cells(table('<w:tr>'+cell('A',props)+'</w:tr>',1));grid=units[0]['locator']['source_grid']
            self.assertEqual(grid['status'],'UNRESOLVED_SOURCE_STRUCTURE');self.assertTrue(grid['issues'])
            self.assertIn('TABLE_GRID_UNRESOLVED',units[0]['limitations'])

    def test_missing_grid_and_row_width_conflicts_are_explicit(self):
        for xml in ['<w:tbl><w:tr>'+cell('A')+'</w:tr></w:tbl>',table('<w:tr>'+cell('A')+'</w:tr>')]:
            grid=self.cells(xml)[0]['locator']['source_grid'];self.assertEqual(grid['status'],'UNRESOLVED_SOURCE_STRUCTURE');self.assertTrue(grid['issues'])

    def test_wrapped_rows_cannot_be_skipped_to_link_vertical_merge(self):
        a='<w:tr>'+cell('A','<w:vMerge w:val="restart"/>')+'</w:tr>'
        hidden='<w:sdt><w:sdtContent><w:tr>'+cell('Hidden')+'</w:tr></w:sdtContent></w:sdt>'
        b='<w:tr>'+cell('B','<w:vMerge/>')+'</w:tr>'
        grid=self.cells(table(a+hidden+b,1))[-1]['locator']['source_grid']
        self.assertEqual(grid['status'],'UNRESOLVED_SOURCE_STRUCTURE');self.assertIsNone(grid['vertical_anchor'])

    def test_revised_row_or_cell_properties_are_not_confirmed_structure(self):
        for props in ['<w:tcPrChange/>','<w:cellMerge/>']:
            grid=self.cells(table('<w:tr>'+cell('A',props)+'</w:tr>',1))[0]['locator']['source_grid']
            self.assertEqual(grid['status'],'UNRESOLVED_SOURCE_STRUCTURE')
        grid=self.cells(table('<w:tr><w:trPr><w:del/></w:trPr>'+cell('A')+'</w:tr>',1))[0]['locator']['source_grid']
        self.assertEqual(grid['status'],'UNRESOLVED_SOURCE_STRUCTURE')

"""Synthetic fixtures for observed continuation/header and stamp contamination failures."""
import copy
import unittest
from engineering.document_intelligence import DoclingDocumentParser, DocumentParseError


def table(values, flags=None):
    cells=[]
    for row, row_values in enumerate(values):
        for col, value in enumerate(row_values):
            cell=dict(text=value,start_row_offset_idx=row,end_row_offset_idx=row+1,
                      start_col_offset_idx=col,end_col_offset_idx=col+1)
            if flags is not None:cell['column_header']=flags[row][col]
            cells.append(cell)
    return {'prov':[{'page_no':397,'bbox':{'l':40,'t':830,'r':580,'b':15,'coord_origin':'BOTTOMLEFT'}}],
            'data':{'num_rows':len(values),'num_cols':len(values[0]),'table_cells':cells}}


class DoclingTableHeaderTests(unittest.TestCase):
    def test_continuation_without_headers_blocks_instead_of_dropping_first_data_row(self):
        raw=table([('Колонна 14/Д','Км1-6'),('Колонна 15/Д','Км1-5')],
                  [(False,False),(False,False)])
        with self.assertRaisesRegex(DocumentParseError,'header'):
            DoclingDocumentParser._table_rows({'tables':[raw]})

    def test_missing_header_metadata_cannot_be_guessed(self):
        raw=table([('Параметр','Значение'),('Нагрузка','0,50 кПа')])
        with self.assertRaisesRegex(DocumentParseError,'header'):
            DoclingDocumentParser._table_rows({'tables':[raw]})

    def test_confirmed_header_keeps_all_data_rows_and_page(self):
        raw=table([('Параметр','Значение'),('Снег','0,50 кПа'),('Ветер','0,30 кПа')],
                  [(True,True),(False,False),(False,False)])
        rows=DoclingDocumentParser._table_rows({'tables':[raw]})
        self.assertEqual([row.text for row in rows],
                         ['Параметр: Снег | Значение: 0,50 кПа',
                          'Параметр: Ветер | Значение: 0,30 кПа'])
        self.assertTrue(all(row.provenance[0].page_no==397 for row in rows))

    def test_ambiguous_header_metadata_blocks(self):
        for flags in [[(True,False),(False,False)],[(True,True),(True,False)],
                      [(1,True),(False,False)],[(True,True),(False,None)]]:
            with self.subTest(flags=flags):
                raw=table([('Параметр','Значение'),('Нагрузка','0,50 кПа')],flags)
                with self.assertRaisesRegex(DocumentParseError,'header'):
                    DoclingDocumentParser._table_rows({'tables':[raw]})

    def test_mixed_bottom_stamp_blocks_even_with_complete_grid_and_header_flags(self):
        raw=table([('Параметр','Значение'),('Колонна','25,133 см²'),
                   ('№ док. Лист Колонна','Подп. Км1-6')],
                  [(True,True),(False,False),(False,False)])
        before=copy.deepcopy(raw)
        with self.assertRaisesRegex(DocumentParseError,'stamp'):
            DoclingDocumentParser._table_rows({'tables':[raw]})
        self.assertEqual(raw,before)

    def test_duplicate_header_names_cannot_hide_column_meaning(self):
        raw=table([('Значение','Значение'),('1','2')],[(True,True),(False,False)])
        with self.assertRaisesRegex(DocumentParseError,'header'):
            DoclingDocumentParser._table_rows({'tables':[raw]})

    def test_diagnostics_preserve_metadata_needed_to_normalize_table(self):
        from scripts.inspect_docling_tables import table_diagnostics
        raw=table([('Параметр','Значение'),('Снег','0,50 кПа')],
                  [(True,True),(False,False)])
        raw['data']['table_cells'][0]['bbox']={'l':10,'t':20,'r':30,'b':40}
        diagnostic=table_diagnostics({'tables':[raw]})[0]
        replay={'tables':[{'prov':diagnostic['provenance'], 'data':{
            'num_rows':diagnostic['num_rows'],'num_cols':diagnostic['num_cols'],
            'table_cells':diagnostic['cells']}}]}
        rows=DoclingDocumentParser._table_rows(replay)
        self.assertEqual([row.text for row in rows],['Параметр: Снег | Значение: 0,50 кПа'])
        self.assertEqual(diagnostic['cells'][0]['bbox'],{'l':10,'t':20,'r':30,'b':40})

    def test_false_model_header_with_rebar_data_blocks_even_without_stamp(self):
        # Observed after clipping the V4 table: no stamp labels, complete grid,
        # but the model puts first-row body text and an area calculation in headers.
        raw=table([('Ко-', 'лонна в осях 14/Д', 'Км1-6 8d20=25.133 см²', '8d20=25.133 см²'),
                   ('Колонна 15/Д', 'Км1-5', '4d20=12.566 см²', '4d20=12.566 см²')],
                  [(True,True,True,True),(False,False,False,False)])
        with self.assertRaisesRegex(DocumentParseError,'header'):
            DoclingDocumentParser._table_rows({'tables':[raw]})

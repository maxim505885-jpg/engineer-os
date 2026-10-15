"""Source-rendered V4 bottom stamps; never generalize engineering grids."""
import copy
import unittest
from engineering.document_intelligence import DoclingDocumentParser


class StampVariantTests(unittest.TestCase):
    def test_observed_shapes_require_exact_stamp_literals_and_source_sheet(self):
        shapes=[(20,2,6,['Изм.','Кол.уч Дата','№ док.','Подп.','ОСК-ССК-22/0526-1 20','Лист','Лист']),
                (22,3,8,['Изм.','Кол.уч','№ док.','Подп.','Дата','ОСК-ССК-22/0526-1','Лист','22','Лист']),
                (175,2,7,['Изм.','Кол.уч Лист','№ док.','Подп.','Дата','ОСК-ССК-22/0526-1','Лист','175']),
                (336,2,7,['Изм.','Кол.уч','№ док. Лист','Подп.','Дата','ОСК-ССК-22/0526-1','Лист','336'])]
        for page,rows,cols,labels in shapes:
            with self.subTest(page=page):
                stamp=dict(prov=[dict(page_no=page,bbox=dict(l=44,t=60,r=580,b=15,coord_origin='BOTTOMLEFT'))],data=dict(num_rows=rows,num_cols=cols,table_cells=[dict(text=t) for t in labels]))
                self.assertTrue(DoclingDocumentParser._is_page_stamp(stamp))
                self.assertEqual(DoclingDocumentParser._table_rows({'tables':[stamp]}),())
                for mutation in ('body','wrong_sheet','wrong_location','invalid_text','missing_document_label','missing_code','narrow_body_box'):
                    bad=copy.deepcopy(stamp)
                    if mutation=='body':bad['data']['table_cells'].append(dict(text='Давление грунта 1,15'))
                    if mutation=='wrong_sheet':bad['prov'][0]['page_no']=999
                    if mutation=='wrong_location':bad['prov'][0]['bbox']['t']=500
                    if mutation=='invalid_text':bad['data']['table_cells'][0]['text']=123
                    if mutation=='missing_document_label':bad['data']['table_cells']=[c for c in bad['data']['table_cells'] if '№ док.' not in c['text']]
                    if mutation=='missing_code':bad['data']['table_cells']=[c for c in bad['data']['table_cells'] if 'ОСК-ССК' not in c['text']]+[dict(text=str(page))]
                    if mutation=='narrow_body_box':bad['prov'][0]['bbox']['r']=455
                    self.assertFalse(DoclingDocumentParser._is_page_stamp(bad),mutation)

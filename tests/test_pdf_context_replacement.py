import base64
import copy
import hashlib
import importlib.util
import tempfile
import unittest
from pathlib import Path

from scripts.recover_docling_export import recover_export, table_digest
from engineering.document_intelligence import DoclingDocumentParser


@unittest.skipUnless(importlib.util.find_spec('fitz'), 'PyMuPDF unavailable')
class ContextReplacementTests(unittest.TestCase):
    def test_split_number_stamp_does_not_become_an_engineering_table(self):
        # Measured p140 stamp splits "№ док." into adjacent fragments and
        # includes the left margin. A numerical body row must still reject it.
        values=['Изм.','Кол.уч','№ Лист','док.','Подп.','Дата','ОСК-ССК-22/0526-1','Лист','140']
        table=dict(prov=[dict(page_no=140,bbox=dict(l=23.488,t=62.552,r=583.605,b=14.34,coord_origin='BOTTOMLEFT'))],
                   data=dict(num_rows=3,num_cols=8,table_cells=[dict(text=v) for v in values]))
        self.assertTrue(DoclingDocumentParser._is_page_stamp(table))
        for mutation in ('engineering_value','wrong_page','body_position'):
            changed=copy.deepcopy(table)
            if mutation=='engineering_value':changed['data']['table_cells'].append(dict(text='500 kPa'))
            if mutation=='wrong_page':changed['prov'][0]['page_no']=139
            if mutation=='body_position':changed['prov'][0]['bbox']['t']=300
            self.assertFalse(DoclingDocumentParser._is_page_stamp(changed))

    def test_two_row_eight_column_stamp_requires_source_sheet_and_code(self):
        # Measured p136/p225 exports add a duplicate "Лист" stamp column.
        values=['Изм.','Кол.уч','№ док.','Подп.','Дата','ОСК-ССК-22/0526-1','Лист','136','Лист']
        table=dict(prov=[dict(page_no=136,bbox=dict(l=43.33,t=60.64,r=582.59,b=14.76,coord_origin='BOTTOMLEFT'))],
                   data=dict(num_rows=2,num_cols=8,table_cells=[dict(text=v) for v in values]))
        self.assertTrue(DoclingDocumentParser._is_page_stamp(table))
        for field,value in [('page_no',135),('t',300)]:
            changed=copy.deepcopy(table)
            if field=='page_no':changed['prov'][0][field]=value
            else:changed['prov'][0]['bbox'][field]=value
            self.assertFalse(DoclingDocumentParser._is_page_stamp(changed))
        for altered in [values+['31.4'],[v for v in values if v!='ОСК-ССК-22/0526-1']]:
            changed=copy.deepcopy(table);changed['data']['table_cells']=[dict(text=v) for v in altered]
            self.assertFalse(DoclingDocumentParser._is_page_stamp(changed))

    # Catch loss of the footer when a neural table contains both grid and margin.
    def test_verified_grid_preserves_oversized_model_region(self):
        import fitz
        with tempfile.TemporaryDirectory() as directory:
            source=Path(directory)/'source.pdf'
            with fitz.open() as pdf:
                p=pdf.new_page(width=100,height=100)
                p.draw_rect(fitz.Rect(10,20,90,60),width=.2)
                p.draw_line((10,40),(90,40),width=.2)
                p.draw_line((50,40),(50,60),width=.2)
                p.insert_text((12,35),'Heading',fontsize=5)
                p.insert_text((12,55),'123.45',fontsize=5)
                p.insert_text((12,80),'Footer',fontsize=5)
                p.insert_text((88,70),'Edge',fontsize=5)
                pdf.save(source)
            sha=hashlib.sha256(source.read_bytes()).hexdigest()
            def f(bbox,text):return dict(source_sha256=sha,source_page=1,coordinate_origin='TOPLEFT',bbox=bbox,text=text)
            target=dict(prov=[dict(page_no=1,bbox=dict(l=10,t=20,r=90,b=90,coord_origin='TOPLEFT'))],data=dict(num_rows=3,num_cols=2,table_cells=[]))
            raw=dict(texts=[],tables=[target])
            grid=dict(table_id='grid',source_page=1,x_boundaries=[10,50,90],y_boundaries=[20,40,60],source_detection_clip=[0,0,100,100],
                      docling_table_index=0,docling_table_sha256=table_digest(target),replacement_mode='SOURCE_VECTOR_CONTEXT',
                      cells=[dict(cell_id='h',row_start=0,row_end=1,col_start=0,col_end=2,source_fragment=f([10,20,90,40],'Heading')),
                             dict(cell_id='v',row_start=1,row_end=2,col_start=0,col_end=1,source_fragment=f([10,40,50,60],'123.45')),
                             dict(cell_id='blank',row_start=1,row_end=2,col_start=1,col_end=2,source_fragment=f([50,40,90,60],''))])
            m=dict(schema_version=2,source_sha256=sha,status='UNCERTAINTY',evidentiary_status='NOT_EVIDENCE',acceptance_granted=False,
                   review=dict(reviewer='test',reviewed_at='2026-10-05T00:00:00Z',scope='physical grid'),
                   context_fragments=[f([10,20,90,60],'Heading 123.45')],tables=[grid])
            result=recover_export(source,raw,m,project_id='p',document_id='d')
            self.assertEqual(result['status'],'UNCERTAINTY',result.get('reason'))
            self.assertEqual([b['text'] for b in result['blocks'] if b['kind']=='table_cell'],['Heading','123.45',''])
            context=[b for b in result['blocks'] if b['kind']=='source_context'][0]
            self.assertEqual(context['text'],'Edge Footer')
            self.assertEqual(context['provenance'][0]['bbox'],dict(left=10.0,top=20.0,right=90.0,bottom=90.0))
            png=base64.b64decode(context['source_visual']['png_base64'],validate=True)
            self.assertEqual(hashlib.sha256(png).hexdigest(),context['source_visual']['sha256'])
            self.assertEqual(context['original_target_sha256'],table_digest(target))
            self.assertEqual(context['interpretation_status'],'UNCERTAINTY')
            self.assertEqual(result['document_status'],'BLOCK')
            self.assertFalse(result['complete_page'])
            self.assertFalse(result['acceptance_granted'])
            self.assertEqual(raw['tables'][0]['data']['table_cells'],[])
            # Original strict mode must continue rejecting oversized regions.
            strict=copy.deepcopy(m);strict['tables'][0]['replacement_mode']='SOURCE_VECTOR_GRID'
            self.assertEqual(recover_export(source,raw,strict,project_id='p',document_id='d')['status'],'BLOCK')
            # No relocation to an unrelated page region, forged text or digest.
            for mutation in ('foreign_box','thin_overlap','bad_digest','invented_cell','invalid_box'):
                mm=copy.deepcopy(m);rr=copy.deepcopy(raw)
                if mutation=='foreign_box':rr['tables'][0]['prov'][0]['bbox']=dict(l=1,t=1,r=5,b=5,coord_origin='TOPLEFT');mm['tables'][0]['docling_table_sha256']=table_digest(rr['tables'][0])
                if mutation=='thin_overlap':rr['tables'][0]['prov'][0]['bbox']=dict(l=89,t=20,r=99,b=90,coord_origin='TOPLEFT');mm['tables'][0]['docling_table_sha256']=table_digest(rr['tables'][0])
                if mutation=='bad_digest':mm['tables'][0]['docling_table_sha256']='0'*64
                if mutation=='invented_cell':mm['tables'][0]['cells'][1]['source_fragment']['text']='999'
                if mutation=='invalid_box':rr['tables'][0]['prov'][0]['bbox']['r']=101;mm['tables'][0]['docling_table_sha256']=table_digest(rr['tables'][0])
                with self.subTest(mutation=mutation):
                    failed=recover_export(source,rr,mm,project_id='p',document_id='d')
                    self.assertEqual(failed['status'],'BLOCK')
                    self.assertEqual(failed['blocks'],[])

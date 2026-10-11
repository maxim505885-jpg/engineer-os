import hashlib
import json
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path
from engineering.document_intelligence.pdf_table_asset_ingestion import pdf_table_candidates
from engineering.document_intelligence.asset_provenance import verify_payload

class PDFTableAssetTests(unittest.TestCase):
    def test_table_candidate_has_validated_bytes_not_verified_meaning(self):
        import fitz
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'table.pdf'
            doc=fitz.open()
            page=doc.new_page(width=420,height=420)
            shape=page.new_shape()
            for x in (30,140,250):
                shape.draw_line((x,50),(x,160))
            for y in (50,105,160):
                shape.draw_line((30,y),(250,y))
            shape.finish(color=(0,0,0))
            shape.commit()
            page.insert_text((45,80),'A1')
            page.insert_text((155,80),'B1')
            page.insert_text((45,135),'A2')
            page.insert_text((155,135),'B2')
            doc.save(path)
            doc.close()
            pairs=pdf_table_candidates(path,[1])
            self.assertGreaterEqual(len(pairs),1)
            for candidate,payload in pairs:
                self.assertEqual(candidate.asset_kind,'table_cells')
                self.assertIn('bbox=',candidate.location)
                self.assertEqual(candidate.page_number,1)
                self.assertEqual(candidate.source_sha256,hashlib.sha256(path.read_bytes()).hexdigest())
                self.assertFalse(candidate.verified)
                self.assertTrue(verify_payload(candidate,payload,candidate.source_sha256))
                data=json.loads(payload)
                self.assertIsInstance(data,dict,'Reader discards per-cell source geometry')
                self.assertEqual(data['schema'],'ENGINEER_OS_PDF_TABLE_CELLS_V2')
                self.assertEqual(data['values'],[['A1','B1'],['A2','B2']])
                self.assertEqual(data['cells'][0],{'row':1,'column':1,'bbox':[30.0,50.0,140.0,105.0],
                    'text':'A1','geometry_status':'DETECTED_UNVERIFIED'})
                self.assertEqual(data['cells'][-1]['bbox'],[140.0,105.0,250.0,160.0])
                self.assertEqual(data['coordinate_system'],'PYMUPDF_UNROTATED_PAGE_TOPLEFT_POINTS')
                self.assertFalse(data['content_verified'])
                self.assertFalse(data['header']['external'])
                self.assertEqual(data['header']['names'],['A1','B1'])
                self.assertEqual(data['header']['cells'],[c['bbox'] for c in data['cells'][:2]])

    def test_merged_cell_retains_real_rectangle_and_unknown_slot(self):
        import fitz
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'merged.pdf'
            doc=fitz.open(); page=doc.new_page(width=420,height=420)
            shape=page.new_shape()
            for x in (30,250): shape.draw_line((x,50),(x,160))
            shape.draw_line((140,105),(140,160))
            for y in (50,105,160): shape.draw_line((30,y),(250,y))
            shape.finish(color=(0,0,0));shape.commit()
            for xy,word in [((45,80),'MERGED'),((45,135),'LEFT'),((155,135),'RIGHT')]:
                page.insert_text(xy,word)
            doc.save(path);doc.close()
            candidate,payload=pdf_table_candidates(path,[1])[0]
            data=json.loads(payload)
            self.assertIsInstance(data,dict,'Reader discards merged cell geometry')
            self.assertEqual(data['values'],[['MERGED',None],['LEFT','RIGHT']])
            self.assertEqual(data['cells'][0]['bbox'],[30.0,50.0,250.0,105.0])
            self.assertEqual(data['cells'][1]['bbox'],None)
            self.assertEqual(data['cells'][1]['geometry_status'],'UNRESOLVED_SLOT')
            self.assertIn('MERGED_OR_MISSING_CELL_RELATION_UNVERIFIED',data['limitations'])
            self.assertFalse(candidate.verified)
            self.assertEqual(data['header']['cells'][1],None)

    def test_external_header_preserves_labels_and_separate_rectangles(self):
        import fitz
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'external-header.pdf'
            doc=fitz.open();page=doc.new_page()
            shape=page.new_shape()
            for x in (30,140,250):shape.draw_line((x,50),(x,160))
            for y in (50,105,160):shape.draw_line((30,y),(250,y))
            shape.finish(color=(0,0,0));shape.commit()
            for xy,word in [((45,43),'FIRST'),((155,43),'SECOND'),((45,80),'A1'),
                            ((155,80),'B1'),((45,135),'A2'),((155,135),'B2')]:
                page.insert_text(xy,word)
            doc.save(path);doc.close()
            data=json.loads(pdf_table_candidates(path,[1])[0][1])
            self.assertTrue(data['header']['external'])
            self.assertEqual(data['header']['names'],['FIRST','SECOND'])
            self.assertLess(data['header']['bbox'][1],data['bbox'][1])
            self.assertEqual(data['header']['bbox'][3],data['bbox'][1])
            with fitz.open(path) as original:
                for name,rect in zip(data['header']['names'],data['header']['cells']):
                    self.assertEqual(original[0].get_text(clip=rect).strip(),name)

    def test_invalid_page_rejected(self):
        import fitz
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'t.pdf'
            doc=fitz.open()
            doc.new_page()
            doc.save(path)
            doc.close()
            with self.assertRaisesRegex(ValueError,'INVALID_PAGE_NUMBER'):
                pdf_table_candidates(path,[2])

    def test_rotated_page_keeps_unrotated_cell_geometry(self):
        import fitz
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'rotated.pdf'
            doc=fitz.open();page=doc.new_page(width=420,height=300)
            shape=page.new_shape()
            for x in (30,140,250):shape.draw_line((x,50),(x,160))
            for y in (50,105,160):shape.draw_line((30,y),(250,y))
            shape.finish(color=(0,0,0));shape.commit()
            page.insert_text((45,80),'A1');page.set_rotation(90)
            doc.save(path);doc.close()
            candidate,payload=pdf_table_candidates(path,[1])[0]
            data=json.loads(payload)
            self.assertEqual(data['page_rotation'],90)
            self.assertEqual(data['page_rect'],[0.0,0.0,300.0,420.0])
            self.assertEqual(data['cells'][0]['bbox'],[30.0,50.0,140.0,105.0])
            with fitz.open(path) as original:
                self.assertEqual(original[0].get_text(clip=data['cells'][0]['bbox']).strip(),'A1')

    def test_source_change_during_detection_is_rejected(self):
        import fitz
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'changed.pdf'
            doc=fitz.open();doc.new_page();doc.save(path);doc.close()
            original_open=fitz.open
            def changed_open(*args,**kwargs):
                opened=original_open(*args,**kwargs)
                with path.open('ab') as output:output.write(b'\n% source changed')
                return opened
            with patch.object(fitz,'open',side_effect=changed_open):
                with self.assertRaisesRegex(ValueError,'SOURCE_IDENTITY_CHANGED_DURING_EXTRACTION'):
                    pdf_table_candidates(path,[1])

if __name__=='__main__':
    unittest.main()

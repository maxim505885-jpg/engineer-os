import copy
import hashlib
import importlib
import importlib.util
import tempfile
import unittest
from pathlib import Path


@unittest.skipUnless(importlib.util.find_spec('fitz'), 'PyMuPDF unavailable')
class PdfRegionTests(unittest.TestCase):
    def test_serialized_decimal_crop_geometry_can_be_remapped(self):
        import fitz
        from scripts.pdf_region import prepare_region, remap_export
        with tempfile.TemporaryDirectory() as directory:
            source, crop = Path(directory)/'s.pdf', Path(directory)/'r.pdf'
            with fitz.open() as pdf:
                p = pdf.new_page(width=300, height=400)
                p.insert_text((60,80), 'Decimal crop')
                pdf.save(source)
            mapping = prepare_region(source, crop, page_no=1,
                bbox=[40.1,50.2,260.3,250.4], expected_sha256=hashlib.sha256(source.read_bytes()).hexdigest())
            with fitz.open(crop) as pdf:
                size = dict(width=pdf[0].rect.width, height=pdf[0].rect.height)
            raw = dict(pages={'1': dict(page_no=1, size=size)}, texts=[dict(prov=[dict(
                page_no=1, bbox=dict(l=1,r=10,t=1,b=10,coord_origin='TOPLEFT'))])])
            result = remap_export(source,crop,mapping,raw)
            self.assertEqual(result['texts'][0]['prov'][0]['bbox']['l'], 41.1)
            rounded = copy.deepcopy(raw)
            rounded['pages']['1']['size'] = {k:round(v, 5) for k,v in size.items()}
            rounded['texts'][0]['prov'][0]['bbox'] = dict(l=0,r=round(size['width'],5),
                t=round(size['height'],5),b=0,coord_origin='BOTTOMLEFT')
            try:
                mapped = remap_export(source,crop,mapping,rounded)
            except ValueError as exc:
                self.fail(f'valid rounded Docling geometry rejected: {exc}')
            self.assertAlmostEqual(mapped['texts'][0]['prov'][0]['bbox']['t'],50.2)
            wrong = copy.deepcopy(mapping)
            wrong['derived_size']['width'] += .01
            with self.assertRaises(ValueError):
                remap_export(source,crop,wrong,raw)

    def test_crop_and_remap_keep_original_page_and_coordinates(self):
        # Without the production transform, local page 1 and bottom-left
        # coordinates could be attached to a different place in the source.
        spec = importlib.util.find_spec('scripts.pdf_region')
        self.assertIsNotNone(spec, 'bounded PDF regions need an original-source transform')
        module = importlib.import_module('scripts.pdf_region')
        import fitz
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, crop = root/'source.pdf', root/'region.pdf'
            with fitz.open() as pdf:
                pdf.new_page(width=300, height=400)
                page = pdf.new_page(width=300, height=400)
                page.insert_text((60, 80), 'Inside')
                page.insert_text((60, 300), 'Outside')
                pdf.save(source)
            sha = hashlib.sha256(source.read_bytes()).hexdigest()
            mapping = module.prepare_region(source, crop, page_no=2,
                                            bbox=[40, 50, 260, 250], expected_sha256=sha)
            with fitz.open(crop) as pdf:
                self.assertEqual(len(pdf), 1)
                self.assertIn('Inside', pdf[0].get_text())
                self.assertNotIn('Outside', pdf[0].get_text())
                self.assertEqual((pdf[0].rect.width, pdf[0].rect.height), (220, 200))
            raw = dict(pages={'1': dict(page_no=1, size=dict(width=220, height=200))},
                       texts=[dict(text='Inside', prov=[dict(page_no=1, bbox=dict(
                           l=20, r=70, t=180, b=160, coord_origin='BOTTOMLEFT'))])],
                       tables=[dict(prov=[dict(page_no=1, bbox=dict(
                           l=0, r=220, t=0, b=200, coord_origin='TOPLEFT'))])])
            original = copy.deepcopy(raw)
            result = module.remap_export(source, crop, mapping, raw)
            self.assertEqual(raw, original)
            self.assertEqual(result['texts'][0]['prov'][0], dict(page_no=2,
                bbox=dict(l=60, r=110, t=70, b=90, coord_origin='TOPLEFT')))
            self.assertEqual(result['tables'][0]['prov'][0]['bbox'], dict(
                l=40, r=260, t=50, b=250, coord_origin='TOPLEFT'))
            self.assertEqual(result['pages']['2']['size'], dict(width=300, height=400))
            self.assertFalse(result['region_provenance']['complete_page'])
            self.assertFalse(result['region_provenance']['acceptance_granted'])
            self.assertEqual(result['region_provenance']['source_sha256'], sha)
            for changed in ('page', 'bbox', 'size'):
                invalid = copy.deepcopy(raw)
                if changed == 'page': invalid['texts'][0]['prov'][0]['page_no'] = 2
                if changed == 'bbox': invalid['texts'][0]['prov'][0]['bbox']['r'] = 221
                if changed == 'size': invalid['pages']['1']['size']['height'] = 201
                with self.subTest(changed=changed), self.assertRaises(ValueError):
                    module.remap_export(source, crop, mapping, invalid)
            with self.assertRaises(ValueError):
                module.prepare_region(source, crop, page_no=2, bbox=[40,50,260,250], expected_sha256='0'*64)
            for bbox in ([0, 0, 301, 100], [0, 0, float('nan'), 100], [5, 5, 4, 10]):
                with self.subTest(bbox=bbox), self.assertRaises(ValueError):
                    module.prepare_region(source, crop, page_no=2, bbox=bbox, expected_sha256=sha)
            with self.assertRaises(ValueError):
                module.prepare_region(source, source, page_no=2, bbox=[40,50,260,250], expected_sha256=sha)
            crop.write_bytes(b'changed')
            with self.assertRaises(ValueError):
                module.remap_export(source, crop, mapping, raw)

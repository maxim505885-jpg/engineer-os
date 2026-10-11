"""Independent regressions for asset class limits and HD Photo references."""
import hashlib
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from engineering.local_app import office, source_assets
from tests.test_office_documents import package
from tests.test_word_embedded_layers import doc


class AssetBudgetReviewTests(unittest.TestCase):
    def test_inventory_class_overflow_rejected_before_member_decompression(self):
        for directory, budget in (
            ('word/media', 'MAX_IMAGE_TOTAL_BYTES'),
            ('word/embeddings', 'MAX_OBJECT_TOTAL_BYTES'),
        ):
            with self.subTest(directory=directory), tempfile.TemporaryDirectory() as folder:
                first, overflow = directory+'/a.bin', directory+'/b.bin'
                data = package({'word/document.xml': '<document/>', first: b'a'*6, overflow: b'b'*6})
                path = Path(folder)/'budget.docx'
                path.write_bytes(data)
                record = dict(name=path.name, path=str(path), session_id='session',
                              sha256=hashlib.sha256(data).hexdigest())

                class Store:
                    def get_file(self, file_id):
                        return record

                reads = []
                original_read = zipfile.ZipFile.read

                def observed_read(archive, name, *args, **kwargs):
                    reads.append(name)
                    return original_read(archive, name, *args, **kwargs)

                with patch.object(source_assets, budget, 10), patch.object(zipfile.ZipFile, 'read', observed_read):
                    with self.assertRaisesRegex(ValueError, 'Asset size limit'):
                        source_assets.read_assets(Store(), 'session', 'file')
                self.assertIn(first, reads)
                self.assertNotIn(overflow, reads)

    def test_hdphoto_relation_binds_only_declared_image_layer(self):
        relationship_type = 'http://schemas.microsoft.com/office/2007/relationships/hdphoto'
        payload = b'exact-hdphoto-layer-source'
        data = doc(
            '<w:p><w:drawing><a:blip r:embed="layer"><a14:imgLayer r:embed="layer"/></a:blip></w:drawing></w:p>',
            f'<Relationship Id="layer" Type="{relationship_type}" Target="media/layer.wdp"/>',
            {'word/media/layer.wdp': payload},
        )
        units, _ = office.read(data, 'docx')
        standard, layer = units[0]['locator']['images']
        self.assertEqual(standard['status'], 'UNAVAILABLE')
        self.assertEqual(standard['reason'], 'IMAGE_RELATIONSHIP_MISSING_OR_WRONG_TYPE')
        self.assertNotIn('sha256', standard)
        self.assertEqual(layer['status'], 'BOUND_PACKAGE_IMAGE')
        self.assertEqual(layer['reference_kind'], 'HD_PHOTO_LAYER')
        self.assertEqual(layer['sha256'], hashlib.sha256(payload).hexdigest())
        self.assertFalse(layer['layer_composition_verified'])
        self.assertFalse(layer['content_verified'])
        self.assertIn('IMAGE_LAYER_COMPOSITION_UNVERIFIED', units[0]['limitations'])


if __name__ == '__main__':
    unittest.main()

import hashlib
import tempfile
import unittest
from pathlib import Path
import ezdxf


class CadRoundtripComparisonTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.source=Path(self.tmp.name)/'source.dxf';self.output=self.source.with_name('output.dxf')
        doc=ezdxf.new('R2010',units=4)
        doc.modelspace().add_line((0,0),(100,0))
        doc.modelspace().add_text('section 200 mm')
        doc.saveas(self.source)
        self.sha=hashlib.sha256(self.source.read_bytes()).hexdigest()

    def compare(self):
        from engineering.cad.roundtrip import compare_dxf
        return compare_dxf(self.source,self.output,source_sha256=self.sha)

    def test_roundtrip_reports_serialized_dxf_preservation_only(self):
        ezdxf.readfile(self.source).saveas(self.output)
        result=self.compare()
        self.assertEqual(result['status'],'PASS')
        self.assertEqual(result['scope'],'DXF_SERIALIZED_DATA_ONLY')
        self.assertFalse(result['dwg_equivalence_verified'])
        self.assertFalse(result['acceptance_granted'])
        self.assertEqual(hashlib.sha256(self.source.read_bytes()).hexdigest(),self.sha)

    def test_lost_and_changed_entities_are_classified_by_source_type(self):
        doc=ezdxf.readfile(self.source)
        doc.modelspace().delete_entity(doc.modelspace().query('TEXT')[0])
        doc.modelspace().query('LINE')[0].dxf.end=(101,0,0)
        doc.saveas(self.output)
        result=self.compare()
        self.assertEqual(result['status'],'BLOCK')
        self.assertEqual(result['missing_by_type'],{'TEXT':1})
        self.assertEqual(result['changed_by_type'],{'LINE':1})

    def test_unit_change_corruption_and_wrong_identity_block(self):
        doc=ezdxf.readfile(self.source);doc.units=6;doc.saveas(self.output)
        self.assertIn('UNITS_CHANGED',self.compare()['reasons'])
        self.output.write_bytes(b'corrupt')
        self.assertEqual(self.compare()['status'],'BLOCK')
        self.sha='0'*64
        self.assertEqual(self.compare()['status'],'BLOCK')

    def test_no_declared_units_cannot_pass(self):
        doc=ezdxf.readfile(self.source);doc.units=0;doc.saveas(self.source)
        self.sha=hashlib.sha256(self.source.read_bytes()).hexdigest()
        ezdxf.readfile(self.source).saveas(self.output)
        self.assertIn('DECLARED_UNITS_REQUIRED',self.compare()['reasons'])

    def test_identical_nonfinite_geometry_does_not_pass(self):
        doc=ezdxf.readfile(self.source)
        doc.modelspace().query('LINE')[0].dxf.end=(float('nan'),0,0)
        doc.saveas(self.source)
        self.sha=hashlib.sha256(self.source.read_bytes()).hexdigest()
        self.output.write_bytes(self.source.read_bytes())
        self.assertIn('NONFINITE_SOURCE_GEOMETRY',self.compare()['reasons'])

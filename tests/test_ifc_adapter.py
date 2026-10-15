"""Synthetic declared IFC data, never an accepted structural analysis model."""
import hashlib
import tempfile
import unittest
from pathlib import Path
try:
    import ifcopenshell
except ImportError:
    ifcopenshell=None


@unittest.skipUnless(ifcopenshell,'optional requirements-bim.txt not installed')
class IfcAdapterTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.source=Path(self.tmp.name)/'sample.ifc'
        self.source.write_bytes((Path(__file__).parent/'fixtures/bim/reference.ifc').read_bytes())
        self.sha=hashlib.sha256(self.source.read_bytes()).hexdigest()

    def inspect(self):
        from engineering.bim.ifc_adapter import inspect_ifc
        return inspect_ifc(self.source,expected_sha256=self.sha)

    def test_inventory_units_materials_quantities_and_guid_provenance(self):
        result=self.inspect()
        self.assertEqual(result['status'],'UNCERTAINTY')
        self.assertEqual(result['length_to_m'],0.001)
        self.assertEqual(len(result['storeys']),1)
        self.assertEqual({x['type'] for x in result['elements']},{'IfcBeam','IfcColumn','IfcWall','IfcSlab'})
        beam=next(x for x in result['elements'] if x['type']=='IfcBeam')
        self.assertEqual(beam['materials'],['Synthetic steel'])
        self.assertEqual(beam['properties']['BaseQuantities']['Length'],6000.)
        self.assertEqual(beam['locator'],'ifc:guid:'+beam['guid'])
        self.assertEqual(beam['data_class'],'PROJECT')
        self.assertFalse(result['calculation_model_verified'])
        self.assertFalse(result['acceptance_granted'])
        self.assertEqual(hashlib.sha256(self.source.read_bytes()).hexdigest(),self.sha)

    def test_corruption_identity_missing_units_and_duplicate_guid_fail_closed(self):
        self.sha='0'*64
        self.assertIn('IFC_SOURCE_IDENTITY_MISMATCH',self.inspect()['reasons'])
        self.source.write_text('broken IFC')
        self.sha=hashlib.sha256(self.source.read_bytes()).hexdigest()
        self.assertEqual(self.inspect()['status'],'BLOCK')
        self.setUp()
        model=ifcopenshell.open(str(self.source));model.by_type('IfcProject')[0].UnitsInContext=None
        model.write(str(self.source));self.sha=hashlib.sha256(self.source.read_bytes()).hexdigest()
        self.assertIn('IFC_LENGTH_UNIT_REQUIRED',self.inspect()['reasons'])

    def test_duplicate_guid_and_missing_container_are_reported(self):
        model=ifcopenshell.open(str(self.source))
        beam=model.by_type('IfcBeam')[0];model.by_type('IfcColumn')[0].GlobalId=beam.GlobalId
        model.by_type('IfcRelContainedInSpatialStructure')[0].RelatedElements=(beam,)
        model.write(str(self.source));self.sha=hashlib.sha256(self.source.read_bytes()).hexdigest()
        result=self.inspect()
        self.assertIn('IFC_DUPLICATE_GUID',result['reasons'])
        self.assertIn('IFC_STOREY_RELATION_UNVERIFIED',result['reasons'])

    def test_diff_uses_guid_and_detects_changed_declared_properties(self):
        from engineering.bim.ifc_adapter import compare_ifc
        output=self.source.with_name('revision.ifc')
        model=ifcopenshell.open(str(self.source))
        beam=model.by_type('IfcBeam')[0];beam.Name='changed beam'
        model.write(str(output))
        result=compare_ifc(self.source,output,source_sha256=self.sha)
        self.assertEqual(result['changed_guids'],[beam.GlobalId])
        self.assertEqual(result['added_guids'],[])
        self.assertEqual(result['status'],'UNCERTAINTY')
        self.assertFalse(result['acceptance_granted'])

    def test_entity_limit_blocks_without_truncated_success(self):
        from engineering.bim.ifc_adapter import inspect_ifc
        result=inspect_ifc(self.source,expected_sha256=self.sha,max_entities=2)
        self.assertEqual(result['status'],'BLOCK')
        self.assertIn('IFC_ENTITY_LIMIT',result['reasons'])

    def test_lengthunit_label_cannot_disguise_a_time_unit(self):
        model=ifcopenshell.open(str(self.source))
        model.by_type('IfcSIUnit')[0].Name='SECOND'
        model.write(str(self.source));self.sha=hashlib.sha256(self.source.read_bytes()).hexdigest()
        result=self.inspect()
        self.assertEqual(result['status'],'BLOCK')
        self.assertIn('IFC_LENGTH_UNIT_INVALID',result['reasons'])

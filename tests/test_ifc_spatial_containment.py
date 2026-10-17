"""Direct and inherited spatial membership are distinct source declarations."""
import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest


@unittest.skipUnless(importlib.util.find_spec('ifcopenshell'),'Optional IFC profile absent')
class SpatialContainmentTests(unittest.TestCase):
    def setUp(self):
        import ifcopenshell
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)/'model.ifc'
        self.model=ifcopenshell.open(str(Path(__file__).parent/'fixtures/bim/reference.ifc'))
        self.beam=self.model.by_type('IfcBeam')[0]
        self.relation=self.model.by_type('IfcRelContainedInSpatialStructure')[0]

    def parent(self):
        import ifcopenshell
        assembly=self.model.create_entity('IfcElementAssembly',GlobalId=ifcopenshell.guid.new(),Name='Controlled assembly')
        self.relation.RelatedElements=tuple(e for e in self.relation.RelatedElements if e!=self.beam)+(assembly,)
        self.model.create_entity('IfcRelAggregates',GlobalId=ifcopenshell.guid.new(),RelatingObject=assembly,RelatedObjects=[self.beam])
        return assembly

    def inspect(self):
        from engineering.bim.ifc_adapter import inspect_ifc
        self.model.write(str(self.path))
        return inspect_ifc(self.path,expected_sha256=hashlib.sha256(self.path.read_bytes()).hexdigest())

    def test_unique_assembly_membership_reaches_storey_without_fabricated_direct_relation(self):
        self.parent();result=self.inspect()
        self.assertEqual(result['status'],'UNCERTAINTY',result)
        beam=next(e for e in result['elements'] if e['guid']==self.beam.GlobalId)
        self.assertEqual(beam['storey_guid'],self.relation.RelatingStructure.GlobalId)
        self.assertEqual(beam['storey_relation'],'INHERITED')

    def test_multiple_parent_relations_never_choose_an_arbitrary_storey(self):
        self.parent();self.parent();result=self.inspect()
        self.assertEqual(result['status'],'BLOCK',result)
        self.assertIn('IFC_STOREY_RELATION_UNVERIFIED',result['reasons'])

    def test_cyclic_spatial_ancestry_is_bounded(self):
        import ifcopenshell
        assembly=self.parent()
        self.relation.RelatedElements=tuple(e for e in self.relation.RelatedElements if e!=assembly)
        self.model.create_entity('IfcRelAggregates',GlobalId=ifcopenshell.guid.new(),RelatingObject=self.beam,RelatedObjects=[assembly])
        self.assertEqual(self.inspect()['status'],'BLOCK')

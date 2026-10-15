import hashlib
import tempfile
import unittest
from pathlib import Path
import ifcopenshell

class IfcGeometryTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/'model.ifc'
        self.path.write_bytes((Path(__file__).parent/'fixtures/bim/reference.ifc').read_bytes())
    def inspect(self,**kw):
        from engineering.bim.ifc_geometry import inspect_geometry
        return inspect_geometry(self.path,expected_sha256=hashlib.sha256(self.path.read_bytes()).hexdigest(),**kw)
    def test_missing_representation_is_not_visible(self):
        r=self.inspect();self.assertEqual(r['elements'][0]['visibility'],'NOT_VISIBLE')
        self.assertFalse(r['acceptance_granted']);self.assertFalse(r['calculation_model_verified'])
    def test_solid_geometry_and_metre_provenance(self):
        import ifcopenshell.api
        m=ifcopenshell.open(str(self.path))
        context=ifcopenshell.api.run('context.add_context',m,context_type='Model')
        body=ifcopenshell.api.run('context.add_context',m,context_type='Model',context_identifier='Body',target_view='MODEL_VIEW',parent=context)
        rep=ifcopenshell.api.run('geometry.add_wall_representation',m,context=body,length=6.,height=3.,thickness=.2)
        ifcopenshell.api.run('geometry.assign_representation',m,product=m.by_type('IfcWall')[0],representation=rep)
        m.write(str(self.path));r=self.inspect()
        wall=next(x for x in r['elements'] if x['type']=='IfcWall')
        self.assertEqual(wall['visibility'],'VISIBLE');self.assertEqual(wall['coordinate_unit'],'m')
        self.assertAlmostEqual(wall['bounds_m'][1][0],6.)
        self.assertIn(wall['guid'],wall['locator']);self.assertEqual(wall['source_sha256'],r['source_sha256'])
    def test_invalid_limits_and_source_fail_closed(self):
        self.assertEqual(self.inspect(max_vertices=0)['status'],'BLOCK')
        from engineering.bim.ifc_geometry import inspect_geometry
        self.assertEqual(inspect_geometry(self.path,expected_sha256='0'*64)['status'],'BLOCK')

class IfcRequirementsTests(unittest.TestCase):
    def test_explicit_declaration_checks_and_missing(self):
        from engineering.bim.ifc_requirements import check_requirements
        path=Path(__file__).parent/'fixtures/bim/reference.ifc';sha=hashlib.sha256(path.read_bytes()).hexdigest()
        req={'id':'TZ-1','source':'User technical assignment section 1','ifc_type':'IfcBeam','pset':'BaseQuantities','property':'Length','equals':6000.,'unit':'project_length'}
        r=check_requirements(path,expected_sha256=sha,requirements=[req])
        self.assertEqual(r['checks'][0]['status'],'PASS');self.assertFalse(r['acceptance_granted'])
        req['property']='Unknown';r=check_requirements(path,expected_sha256=sha,requirements=[req])
        self.assertEqual(r['checks'][0]['status'],'UNCERTAINTY')
    def test_undeclared_source_and_nan_block(self):
        from engineering.bim.ifc_requirements import check_requirements
        r=check_requirements('missing',expected_sha256='0'*64,requirements=[{'equals':float('nan')}])
        self.assertEqual(r['status'],'BLOCK')

class IfcGeometryNegativeTests(IfcGeometryTests):
    def test_timeout_is_blocked(self):
        from unittest.mock import patch
        import subprocess
        with patch('engineering.bim.ifc_geometry.subprocess.run',side_effect=subprocess.TimeoutExpired('worker',1)):
            self.assertEqual(self.inspect()['reasons'],['IFC_GEOMETRY_TIMEOUT'])
    def test_output_provenance_rejected(self):
        from unittest.mock import patch
        import subprocess
        with patch('engineering.bim.ifc_geometry.subprocess.run',return_value=subprocess.CompletedProcess([],0,'[]','')):
            self.assertEqual(self.inspect()['reasons'],['IFC_GEOMETRY_PROVENANCE_INVALID'])

class IfcRequirementNegativeTests(unittest.TestCase):
    def test_declared_length_unit_cannot_disguise_property(self):
        from engineering.bim.ifc_requirements import check_requirements
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'fake.ifc';m=ifcopenshell.open(str(Path(__file__).parent/'fixtures/bim/reference.ifc'))
            q=m.by_type('IfcElementQuantity')[0]
            q.Quantities=(m.create_entity('IfcQuantityArea',Name='Length',AreaValue=6000.),)
            m.write(str(path))
            req={'id':'TZ-1','source':'test','ifc_type':'IfcBeam','pset':'BaseQuantities','property':'Length','equals':6000.,'unit':'project_length'}
            r=check_requirements(path,expected_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),requirements=[req])
            self.assertEqual(r['checks'][0]['status'],'UNCERTAINTY')

class IfcRequirementMismatchTests(unittest.TestCase):
    def test_explicit_mismatch_is_traceable_without_acceptance(self):
        from engineering.bim.ifc_requirements import check_requirements
        path=Path(__file__).parent/'fixtures/bim/reference.ifc';sha=hashlib.sha256(path.read_bytes()).hexdigest()
        req={'id':'TZ-X','source':'synthetic test requirement','ifc_type':'IfcBeam','pset':'BaseQuantities','property':'Length','equals':5000.,'unit':'project_length'}
        r=check_requirements(path,expected_sha256=sha,requirements=[req])
        self.assertEqual(r['checks'][0]['status'],'ERROR')
        self.assertEqual(r['checks'][0]['source_sha256'],sha)
        self.assertFalse(r['acceptance_granted'])

class IfcInverseUnitDisguiseTests(unittest.TestCase):
    def test_length_cannot_be_declared_unitless(self):
        from engineering.bim.ifc_requirements import check_requirements
        path=Path(__file__).parent/'fixtures/bim/reference.ifc'
        req={'id':'TZ-inverse','source':'test','ifc_type':'IfcBeam','pset':'BaseQuantities','property':'Length','equals':6000.,'unit':'unitless'}
        r=check_requirements(path,expected_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),requirements=[req])
        self.assertEqual(r['checks'][0]['status'],'UNCERTAINTY')

class IfcWorkerOutputContractTests(IfcGeometryTests):
    def test_invalid_worker_geometry_fields_block(self):
        import json
        import subprocess
        from unittest.mock import patch
        from engineering.bim.ifc_adapter import inspect_ifc
        inventory=inspect_ifc(self.path,expected_sha256=hashlib.sha256(self.path.read_bytes()).hexdigest())
        rows=[dict(guid=e['guid'],type=e['type'],visibility='NOT_VISIBLE',geometry_status='NOT_VERIFIED',coordinate_unit='m',bounds_m=None) for e in inventory['elements']]
        for change in ({'coordinate_unit':'mm'},{'bounds_m':[[float('nan')]*3,[1.]*3],'visibility':'VISIBLE','geometry_status':'MESH_BOUNDS_EVALUATED','vertex_count':3},{'bounds_m':[[2.,0.,0.],[1.,1.,1.]],'visibility':'VISIBLE','geometry_status':'MESH_BOUNDS_EVALUATED','vertex_count':3},{'type':'IfcDoor'},{'vertex_count':True}):
            candidate=[dict(r) for r in rows];candidate[0].update(change)
            with patch('engineering.bim.ifc_geometry.subprocess.run',return_value=subprocess.CompletedProcess([],0,json.dumps(candidate),'')):
                self.assertEqual(self.inspect()['status'],'BLOCK',change)

class IfcDimensionlessPropertyTests(unittest.TestCase):
    def test_real_property_is_unitless_only_without_explicit_unit(self):
        from engineering.bim.ifc_requirements import check_requirements
        import ifcopenshell.api
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'real.ifc';m=ifcopenshell.open(str(Path(__file__).parent/'fixtures/bim/reference.ifc'))
            beam=m.by_type('IfcBeam')[0]
            pset=ifcopenshell.api.run('pset.add_pset',m,product=beam,name='Synthetic')
            ifcopenshell.api.run('pset.edit_pset',m,pset=pset,properties={'Ratio':.5})
            prop=pset.HasProperties[0]
            req={'id':'ratio','source':'test','ifc_type':'IfcBeam','pset':'Synthetic','property':'Ratio','equals':.5,'unit':'unitless'}
            for explicit,expected in ((None,'PASS'),(m.by_type('IfcSIUnit')[0],'UNCERTAINTY')):
                prop.Unit=explicit;m.write(str(path))
                r=check_requirements(path,expected_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),requirements=[req])
                self.assertEqual(r['checks'][0]['status'],expected)

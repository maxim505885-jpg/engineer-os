import hashlib
import importlib.util
from pathlib import Path
import tempfile
import threading
import unittest


@unittest.skipUnless(importlib.util.find_spec('ifcopenshell'),'Optional IFC profile absent')
class IfcJobsTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)/'model.ifc'
        self.path.write_bytes((Path(__file__).parent/'fixtures/bim/reference.ifc').read_bytes())

    def run_tool(self,tool,options=None,second=None):
        from engineering.local_app.ifc_process import run_ifc
        sources=[(self.path,hashlib.sha256(self.path.read_bytes()).hexdigest())]
        if second:sources.append((second,hashlib.sha256(second.read_bytes()).hexdigest()))
        return run_ifc(tool=tool,sources=sources,stop=threading.Event(),options=options or {})

    def test_geometry_runs_inside_existing_boundary_without_extra_child(self):
        result=self.run_tool('IFC_GEOMETRY')
        self.assertEqual(result['status'],'UNCERTAINTY',result)
        self.assertEqual(result['elements'][0]['visibility'],'NOT_VISIBLE')
        self.assertTrue(result['resource_boundary']['child_isolated'])
        self.assertEqual(result['resource_boundary']['timeout_seconds'],30)
        self.assertFalse(result['calculation_model_verified'])

    def test_actual_solid_bounds_are_in_metres_and_source_bound(self):
        import ifcopenshell,ifcopenshell.api
        model=ifcopenshell.open(str(self.path))
        context=ifcopenshell.api.run('context.add_context',model,context_type='Model')
        body=ifcopenshell.api.run('context.add_context',model,context_type='Model',context_identifier='Body',target_view='MODEL_VIEW',parent=context)
        rep=ifcopenshell.api.run('geometry.add_wall_representation',model,context=body,length=6.,height=3.,thickness=.2)
        ifcopenshell.api.run('geometry.assign_representation',model,product=model.by_type('IfcWall')[0],representation=rep)
        model.write(str(self.path));result=self.run_tool('IFC_GEOMETRY')
        wall=next(e for e in result['elements'] if e['type']=='IfcWall')
        self.assertAlmostEqual(wall['bounds_m'][1][0],6.)
        self.assertEqual(wall['source_sha256'],hashlib.sha256(self.path.read_bytes()).hexdigest())

    def test_declared_requirements_keep_units_and_do_not_accept_actual_structure(self):
        req=dict(id='TZ-1',source='Controlled declared requirement',ifc_type='IfcBeam',pset='BaseQuantities',property='Length',equals=6000.,unit='project_length')
        result=self.run_tool('IFC_REQUIREMENTS',{'requirements':[req]})
        self.assertEqual(result['checks'][0]['status'],'PASS',result)
        req['unit']='unitless';result=self.run_tool('IFC_REQUIREMENTS',{'requirements':[req]})
        self.assertEqual(result['checks'][0]['status'],'UNCERTAINTY')
        self.assertFalse(result['acceptance_granted'])

    def test_diff_binds_both_staged_sources(self):
        second=Path(self.temp.name)/'revision.ifc';second.write_bytes(self.path.read_bytes())
        result=self.run_tool('IFC_DIFF',second=second)
        self.assertEqual(result['added_guids'],[]);self.assertEqual(result['removed_guids'],[])
        self.assertEqual(result['output_sha256'],hashlib.sha256(second.read_bytes()).hexdigest())

    def test_valid_unicode_requirements_fit_utf8_request_budget(self):
        req=dict(source='Я'*4000,ifc_type='IfcBeam',pset='BaseQuantities',property='Length',equals=6000.,unit='project_length')
        result=self.run_tool('IFC_REQUIREMENTS',{'requirements':[dict(req,id=str(i)) for i in range(3)]})
        self.assertEqual(len(result['checks']),3,result)

    def test_options_cannot_replace_server_source_or_add_nonfinite_data(self):
        for options in ({'sources':[]},{'requirements':[float('nan')]}):
            with self.subTest(options=options),self.assertRaises(ValueError):self.run_tool('IFC_REQUIREMENTS',options)

    def test_kernel_memory_exhaustion_cannot_be_reported_as_completed_geometry(self):
        import ifcopenshell
        from unittest.mock import patch
        from engineering.bim.ifc_geometry import inspect_geometry_in_worker
        model=ifcopenshell.open(str(self.path))
        model.by_type('IfcBeam')[0].Representation=model.create_entity('IfcProductDefinitionShape',Representations=[])
        model.write(str(self.path))
        with patch('ifcopenshell.geom.create_shape',side_effect=MemoryError):
            result=inspect_geometry_in_worker(self.path,expected_sha256=hashlib.sha256(self.path.read_bytes()).hexdigest())
        self.assertEqual(result['status'],'BLOCK',result)

    def test_missing_model_units_do_not_become_metres_or_verified_length(self):
        import ifcopenshell
        model=ifcopenshell.open(str(self.path));model.by_type('IfcProject')[0].UnitsInContext=None;model.write(str(self.path))
        self.assertEqual(self.run_tool('IFC_GEOMETRY')['status'],'BLOCK')
        req=dict(id='TZ-1',source='Controlled requirement',ifc_type='IfcBeam',pset='BaseQuantities',property='Length',equals=6000.,unit='project_length')
        result=self.run_tool('IFC_REQUIREMENTS',{'requirements':[req]})
        self.assertEqual(result['status'],'BLOCK',result)
        self.assertIn('IFC_LENGTH_UNIT_REQUIRED',result['reasons'])

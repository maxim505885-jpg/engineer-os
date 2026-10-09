import hashlib
import tempfile
import unittest
from pathlib import Path
try:import ezdxf
except ImportError:ezdxf=None
from engineering.cad.dxf_workflow import inventory_dxf, derive_annotation, verify_export
from engineering.cad.intake import inspect_cad

@unittest.skipUnless(ezdxf,'optional ezdxf not installed')
class CadWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.source=Path(self.temp.name)/'source.dxf';self.output=self.source.with_name('derived.dxf')
        doc=ezdxf.new('R2010',units=4);doc.modelspace().add_line((0,0),(100,0));doc.modelspace().add_circle((50,20),5);doc.modelspace().add_text('SOURCE')
        doc.saveas(self.source);self.sha=hashlib.sha256(self.source.read_bytes()).hexdigest()
        self.request=dict(source_sha256=self.sha,text='Review item',insert=[10,20],height=2,reason='Evidence annotation',evidence_ids=['ev1'],units_acknowledged=4)
    def test_roundtrip_preserves_geometry_and_records_annotation(self):
        report=inventory_dxf(self.source,self.sha)
        self.assertEqual(report['units'],4);self.assertEqual(report['entity_counts'],{'LINE':1,'CIRCLE':1,'TEXT':1})
        manifest=derive_annotation(self.source,self.output,self.request)
        self.assertEqual(manifest['verification']['status'],'PASS');self.assertEqual(manifest['human_review'],'REQUIRED')
        self.assertEqual(hashlib.sha256(self.source.read_bytes()).hexdigest(),self.sha)
        self.assertEqual(len(ezdxf.readfile(self.output).modelspace()),4)
    def test_export_tamper_is_detected(self):
        manifest=derive_annotation(self.source,self.output,self.request)
        doc=ezdxf.readfile(self.output);doc.modelspace().query('LINE')[0].dxf.end=(999,0,0);doc.saveas(self.output)
        manifest['output_sha256']=hashlib.sha256(self.output.read_bytes()).hexdigest()
        result=verify_export(self.source,self.output,manifest)
        self.assertEqual(result['status'],'BLOCK');self.assertIn('Original entity',result['reasons'][0])
    def test_unknown_units_and_unsupported_entity_block_edit(self):
        for kind in ('units','entity'):
            doc=ezdxf.readfile(self.source)
            if kind=='units':doc.units=0
            else:doc.modelspace().add_point((0,0))
            doc.saveas(self.source);self.request['source_sha256']=hashlib.sha256(self.source.read_bytes()).hexdigest()
            with self.assertRaises(ValueError):derive_annotation(self.source,self.output,self.request)
    def test_source_identity_and_overwrite_controls(self):
        self.request['source_sha256']='0'*64
        with self.assertRaises(ValueError):derive_annotation(self.source,self.output,self.request)
        self.request['source_sha256']=self.sha
        with self.assertRaises(ValueError):derive_annotation(self.source,self.source,self.request)
        derive_annotation(self.source,self.output,self.request)
        with self.assertRaises(ValueError):derive_annotation(self.source,self.output,self.request)
    def test_dwg_and_corrupt_dxf_are_blocked(self):
        path=self.source.with_suffix('.dwg');path.write_bytes(b'AC1032'+b'\0'*20)
        self.assertEqual(inspect_cad(path)['reasons'],['DWG_CONVERTER_UNAVAILABLE'])
        self.source.write_bytes(b'not a drawing')
        self.assertEqual(inventory_dxf(self.source)['status'],'BLOCK')
    def test_nonfinite_annotation_is_rejected(self):
        self.request['insert']=[float('nan'),0]
        with self.assertRaises(ValueError):derive_annotation(self.source,self.output,self.request)

    def test_nonfinite_source_geometry_blocks_edit(self):
        doc=ezdxf.readfile(self.source);doc.modelspace().query('LINE')[0].dxf.end=(float('nan'),0,0);doc.saveas(self.source)
        self.request['source_sha256']=hashlib.sha256(self.source.read_bytes()).hexdigest()
        with self.assertRaises(ValueError):derive_annotation(self.source,self.output,self.request)
    def test_xref_and_paperspace_block_edit(self):
        for kind in ('xref','paper'):
            doc=ezdxf.readfile(self.source)
            if kind=='xref':doc.blocks.new('external',dxfattribs={'flags':4,'xref_path':'external.dwg'})
            else:doc.layout().add_line((0,0),(1,1))
            doc.saveas(self.source);self.request['source_sha256']=hashlib.sha256(self.source.read_bytes()).hexdigest()
            with self.assertRaises(ValueError):derive_annotation(self.source,self.output,self.request)
    def test_out_of_plane_source_is_inventory_only(self):
        doc=ezdxf.readfile(self.source);doc.modelspace().query('LINE')[0].dxf.end=(1,0,10);doc.saveas(self.source)
        self.request['source_sha256']=hashlib.sha256(self.source.read_bytes()).hexdigest()
        with self.assertRaises(ValueError):derive_annotation(self.source,self.output,self.request)
    def test_inventory_tables_are_bounded_with_explicit_coverage(self):
        doc=ezdxf.readfile(self.source)
        for i in range(110):doc.layers.new('layer'+str(i))
        doc.saveas(self.source)
        report=inventory_dxf(self.source)
        self.assertLessEqual(len(report['layers']),100);self.assertFalse(report['inventory_complete'])
        self.assertIn('INVENTORY_TABLE_LIMIT',report['reasons'])
    def test_rendering_resources_are_preserved(self):
        manifest=derive_annotation(self.source,self.output,self.request)
        doc=ezdxf.readfile(self.output);style=doc.styles.get('Standard');style.dxf.width=10;style.dxf.font='different.shx';doc.saveas(self.output)
        manifest['output_sha256']=hashlib.sha256(self.output.read_bytes()).hexdigest()
        result=verify_export(self.source,self.output,manifest)
        self.assertEqual(result['status'],'BLOCK');self.assertIn('resource',result['reasons'][0])
    def test_header_geometry_settings_are_preserved(self):
        manifest=derive_annotation(self.source,self.output,self.request)
        doc=ezdxf.readfile(self.output);doc.header['$LTSCALE']=10;doc.saveas(self.output)
        manifest['output_sha256']=hashlib.sha256(self.output.read_bytes()).hexdigest()
        result=verify_export(self.source,self.output,manifest)
        self.assertEqual(result['status'],'BLOCK');self.assertIn('header',result['reasons'][0])
    def test_block_definition_and_layout_resources_are_preserved(self):
        for kind in ('block','layout','linetype'):
            output=self.source.with_name(kind+'.dxf');manifest=derive_annotation(self.source,output,self.request)
            doc=ezdxf.readfile(output)
            if kind=='block':doc.blocks.get('*Model_Space').block.dxf.base_point=(1,0,0)
            elif kind=='layout':doc.layouts.get('Layout1').dxf_layout.dxf.plot_rotation=1
            else:doc.linetypes.get('Continuous').dxf.description='Changed source resource'
            doc.saveas(output);manifest['output_sha256']=hashlib.sha256(output.read_bytes()).hexdigest()
            result=verify_export(self.source,output,manifest)
            self.assertEqual(result['status'],'BLOCK',kind)
    def test_added_annotation_must_exactly_match_request(self):
        changes={'z':('insert',(10,20,10)),'rotation':('rotation',45),'extrusion':('extrusion',(0,1,0)),'style':('style','Different'),'thickness':('thickness',3)}
        for name,(attribute,value) in changes.items():
            output=self.source.with_name('annotation-'+name+'.dxf');manifest=derive_annotation(self.source,output,self.request)
            doc=ezdxf.readfile(output);entity=doc.entitydb[manifest['added_handle']];setattr(entity.dxf,attribute,value);doc.saveas(output)
            manifest['output_sha256']=hashlib.sha256(output.read_bytes()).hexdigest()
            result=verify_export(self.source,output,manifest)
            self.assertEqual(result['status'],'BLOCK',name)
            self.assertIn('Annotation',result['reasons'][0],name)

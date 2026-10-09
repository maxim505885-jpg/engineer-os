import hashlib
import tempfile
import time
import unittest
import uuid
from pathlib import Path
try:import ezdxf
except ImportError:ezdxf=None
from engineering.local_app.store import Store

@unittest.skipUnless(ezdxf,'optional ezdxf not installed')
class LocalCadTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.store=Store(self.temp.name);self.sid=self.store.create_session()['id'];self.other=self.store.create_session()['id']
        self.fid=str(uuid.uuid4());folder=self.store.root/'files';folder.mkdir();self.path=folder/(self.fid+'.dxf')
        doc=ezdxf.new('R2010',units=4);doc.modelspace().add_line((0,0),(1,0));doc.saveas(self.path)
        self.sha=hashlib.sha256(self.path.read_bytes()).hexdigest()
        self.store.add_file(dict(id=self.fid,session_id=self.sid,name='source.dxf',path=str(self.path),sha256=self.sha,size=self.path.stat().st_size,text='',extraction_status='UNAVAILABLE',extraction_note='CAD',text_truncated=0,created=time.time()))
        self.eid=str(uuid.uuid4());self.store.add_evidence(dict(id=self.eid,session_id=self.sid,file_id=self.fid,quote='Annotation reviewed',created=time.time()))
        self.request=dict(source_sha256=self.sha,text='Review',insert=[0,1],height=0.2,reason='Review evidence',evidence_ids=[self.eid],units_acknowledged=4)
    def module(self):
        from engineering.local_app import cad
        return cad
    def test_session_derived_export_and_original_preservation(self):
        cad=self.module();self.assertEqual(cad.inventory(self.store,self.sid,self.fid)['units'],4)
        result=cad.derive(self.store,self.sid,self.fid,request=self.request)
        data,mime=cad.export(self.store,self.sid,result['id'])
        self.assertEqual(mime,'application/dxf');self.assertEqual(hashlib.sha256(data).hexdigest(),result['output_sha256'])
        self.assertEqual(hashlib.sha256(self.path.read_bytes()).hexdigest(),self.sha)
        with self.assertRaises(ValueError):cad.export(self.store,self.other,result['id'])
        with self.assertRaises(ValueError):cad.inventory(self.store,self.other,self.fid)
    def test_changed_source_prevents_export(self):
        cad=self.module();result=cad.derive(self.store,self.sid,self.fid,request=self.request)
        self.path.write_bytes(b'changed')
        with self.assertRaises(ValueError):cad.export(self.store,self.sid,result['id'])
    def test_missing_or_foreign_evidence_rejected(self):
        self.request['evidence_ids']=[str(uuid.uuid4())]
        with self.assertRaises(ValueError):self.module().derive(self.store,self.sid,self.fid,request=self.request)
    def test_backup_restore_preserves_cad_derivative_and_rebinds_source(self):
        from engineering.local_app.backup import create_backup,restore_backup
        cad=self.module();result=cad.derive(self.store,self.sid,self.fid,request=self.request)
        with tempfile.TemporaryDirectory() as delivery:
            archive=Path(delivery)/'backup.zip';target=Path(delivery)/'restored'
            create_backup(self.store.root,archive);restore_backup(archive,target)
            restored=Store(target)
            data,mime=cad.export(restored,self.sid,result['id'])
            self.assertEqual(hashlib.sha256(data).hexdigest(),result['output_sha256'])
            self.assertTrue(Path(restored.get_file(self.fid)['path']).is_relative_to(target))
            self.assertEqual(mime,'application/dxf')
    def test_actual_entity_locator_creates_unverified_source_candidate(self):
        cad=self.module();report=cad.inventory(self.store,self.sid,self.fid)
        handle=report['entities'][0]['handle']
        candidate=cad.register_locator(self.store,self.sid,self.fid,handle=handle,statement='Review annotation required')
        self.assertEqual(candidate['locator']['handle'],handle)
        self.assertEqual(candidate['status'],'UNVERIFIED');self.assertFalse(candidate['acceptance_granted'])
        self.request['evidence_ids']=[candidate['id']]
        self.assertEqual(cad.derive(self.store,self.sid,self.fid,request=self.request)['verification']['status'],'PASS')
        with self.assertRaises(ValueError):cad.register_locator(self.store,self.sid,self.fid,handle='BAD',statement='Missing entity')

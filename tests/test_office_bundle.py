"""Pinned software bundle identity; not engineering or image-content acceptance."""
import hashlib,json,tempfile,threading,unittest
from pathlib import Path
from runtime.office_bundle import verify_bundle,BundleError
class OfficeBundleTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);(self.root/'qemu').mkdir()
        self.files={'qemu/qemu-system-x86_64.exe':b'owned exe','worker.qcow2':b'owned image','worker-seed.iso':b'owned seed'}
        for name,data in self.files.items():(self.root/name).write_bytes(data)
    def manifest(self,**changes):
        worker=Path(__file__).resolve().parents[1]/'runtime/office_guest.py'
        value=dict(schema=1,files={n:hashlib.sha256(b).hexdigest() for n,b in self.files.items()},guest_worker_sha256=hashlib.sha256(worker.read_bytes()).hexdigest());value.update(changes)
        raw=json.dumps(value).encode();(self.root/'manifest.json').write_bytes(raw);return hashlib.sha256(raw).hexdigest()
    def test_exact_bundle_is_verified_without_acceptance(self):
        result=verify_bundle(self.root,self.manifest(),stop=threading.Event())
        self.assertEqual(result['image'],self.root/'worker.qcow2');self.assertFalse(result['acceptance_granted'])
    def test_wrong_pin_or_changed_file_or_extra_file_rejected(self):
        pin=self.manifest()
        with self.assertRaises(BundleError):verify_bundle(self.root,'a'*64,stop=threading.Event())
        (self.root/'qemu/extra.dll').write_bytes(b'extra')
        with self.assertRaises(BundleError):verify_bundle(self.root,pin,stop=threading.Event())
        (self.root/'qemu/extra.dll').unlink();(self.root/'worker.qcow2').write_bytes(b'changed')
        with self.assertRaises(BundleError):verify_bundle(self.root,pin,stop=threading.Event())
    def test_guest_change_and_path_escape_rejected(self):
        for changes in [dict(guest_worker_sha256='a'*64),dict(files={'../escape':'a'*64})]:
            with self.assertRaises(BundleError):verify_bundle(self.root,self.manifest(**changes),stop=threading.Event())
    def test_cancelled_verification_stops(self):
        stop=threading.Event();stop.set()
        with self.assertRaises(BundleError):verify_bundle(self.root,self.manifest(),stop=stop)
if __name__=='__main__':unittest.main()

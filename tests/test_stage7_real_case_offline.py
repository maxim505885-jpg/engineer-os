import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from scripts.stage7_real_case_offline import run,sha256

class Stage7OfflineTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
    def make(self,name,data=b"x"):
        p=self.root/name;p.write_bytes(data);return p
    def pdf(self,name):
        return self.make(name,b"%PDF-1.7\nfixture")
    def office(self,name,member):
        p=self.root/name
        with zipfile.ZipFile(p,"w") as z:
            z.writestr("[Content_Types].xml","x");z.writestr(member,"x")
        return p
    def lir(self,name):
        p=self.root/name
        with zipfile.ZipFile(p,"w") as z:z.writestr("0","x")
        return p
    def manifest(self):
        files=[
            ("TOR",self.pdf("tor.pdf")),("REPORT",self.pdf("report.pdf")),
            ("CALCULATION_REPORT",self.office("calc.docx","word/document.xml")),
            ("MODEL",self.lir("model.lir")),("GEODESY",self.pdf("geo.pdf")),("GRAPHICS",self.pdf("graphics.pdf"))]
        return dict(case_name="fixture",external_gates=dict(v4_document_completeness="BLOCK",point6_normative_decision="DEFERRED",point6_solver_decision="DEFERRED",actual_structure_correlation="DEFERRED"),
                    files=[dict(role=r,name=p.name,path=str(p),expected_size=p.stat().st_size,expected_sha256=sha256(p)) for r,p in files])
    def test_real_case_workflow_completes_with_open_engineering_blocks(self):
        a=run(self.manifest());b=run(self.manifest())
        self.assertEqual(a,b);self.assertEqual(a["source_identity_status"],"PASS")
        self.assertEqual(a["stage7_completion"],"COMPLETE_WITH_OPEN_ENGINEERING_BLOCKS")
        self.assertFalse(a["acceptance_granted"]);self.assertEqual(a["final_audit"],"NOT_RUN")
    def test_changed_hash_fails_closed_and_changes_case_identity(self):
        m=self.manifest();baseline=run(m);m["files"][3]["expected_sha256"]="0"*64
        changed=run(m);self.assertEqual(changed["source_identity_status"],"BLOCK")
        self.assertEqual(changed["stage7_completion"],"BLOCKED_BY_SOURCE_INTEGRITY")
        self.assertNotEqual(changed["case_sha256"],baseline["case_sha256"])
        self.assertIn("SOURCE_IDENTITY_OR_FORMAT_BLOCK",changed["block_reasons"])
    def test_missing_required_role_blocks(self):
        m=self.manifest();m["files"]=[x for x in m["files"] if x["role"]!="MODEL"]
        r=run(m);self.assertIn("MODEL",r["missing_roles"]);self.assertEqual(r["source_identity_status"],"BLOCK")

if __name__=="__main__":unittest.main()

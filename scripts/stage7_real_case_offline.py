from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path

REQUIRED_ROLES={"TOR","REPORT","CALCULATION_REPORT","MODEL","GEODESY","GRAPHICS"}
ALLOWED_ROLES=REQUIRED_ROLES|{"PHOTO","OTHER"}

def sha256(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):h.update(chunk)
    return h.hexdigest()

def file_probe(path:Path)->dict:
    ext=path.suffix.lower();head=path.read_bytes()[:16]
    if ext==".pdf":
        ok=head.startswith(b"%PDF");return {"format_status":"PASS" if ok else "BLOCK","details":["PDF_MAGIC_OK" if ok else "PDF_MAGIC_INVALID"]}
    if ext==".doc":
        ok=head.startswith(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1")
        return {"format_status":"PASS" if ok else "BLOCK","details":["OLE_MAGIC_OK" if ok else "OLE_MAGIC_INVALID"]}
    if ext in {".docx",".xlsx"}:
        if not zipfile.is_zipfile(path):return {"format_status":"BLOCK","details":["OFFICE_ZIP_INVALID"]}
        with zipfile.ZipFile(path) as z:names=set(z.namelist())
        required={"[Content_Types].xml","word/document.xml"} if ext==".docx" else {"[Content_Types].xml","xl/workbook.xml"}
        missing=sorted(required-names)
        return {"format_status":"PASS" if not missing else "BLOCK","details":["OFFICE_STRUCTURE_OK"] if not missing else ["OFFICE_STRUCTURE_MISSING:"+",".join(missing)]}
    if ext==".lir":
        if not zipfile.is_zipfile(path):return {"format_status":"BLOCK","details":["LIR_CONTAINER_NOT_READABLE"]}
        with zipfile.ZipFile(path) as z:members=z.namelist()
        return {"format_status":"PASS","details":["LIR_CONTAINER_READABLE",f"LIR_MEMBERS={len(members)}"]}
    ok=path.stat().st_size>0
    return {"format_status":"PASS" if ok else "BLOCK","details":["NONEMPTY_FILE" if ok else "EMPTY_FILE"]}

def stable_digest(value)->str:
    return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode()).hexdigest()

def run(manifest:dict)->dict:
    if not isinstance(manifest,dict) or set(manifest)!={"case_name","external_gates","files"}:raise ValueError("Invalid stage7 manifest")
    if not isinstance(manifest["files"],list) or not manifest["files"]:raise ValueError("Stage7 files required")
    entries=[];roles=set();reasons=[]
    for item in manifest["files"]:
        if not isinstance(item,dict) or set(item)!={"role","name","path","expected_size","expected_sha256"}:raise ValueError("Invalid stage7 file entry")
        role=item["role"]
        if role not in ALLOWED_ROLES:raise ValueError(f"Unsupported role: {role}")
        roles.add(role);path=Path(item["path"]).resolve()
        if not path.is_file():
            entries.append({k:item[k] for k in ("role","name","expected_size","expected_sha256")} | {"status":"BLOCK","reasons":["FILE_MISSING"]})
            reasons.append("SOURCE_FILE_MISSING");continue
        size=path.stat().st_size;digest=sha256(path);probe=file_probe(path)
        row=dict(role=role,name=item["name"],size=size,sha256=digest,size_match=size==item["expected_size"],
                 sha256_match=digest==item["expected_sha256"],format_status=probe["format_status"],format_details=probe["details"])
        row["status"]="PASS" if row["size_match"] and row["sha256_match"] and probe["format_status"]=="PASS" else "BLOCK"
        row["reasons"]=[]
        if not row["size_match"]:row["reasons"].append("SIZE_MISMATCH")
        if not row["sha256_match"]:row["reasons"].append("SHA256_MISMATCH")
        if probe["format_status"]!="PASS":row["reasons"].append("FORMAT_PROBE_BLOCK")
        if row["status"]=="BLOCK":reasons.append("SOURCE_IDENTITY_OR_FORMAT_BLOCK")
        entries.append(row)
    missing_roles=sorted(REQUIRED_ROLES-roles)
    if missing_roles:reasons.append("CASE_REQUIRED_ROLES_MISSING")
    all_sources_ok=all(x["status"]=="PASS" for x in entries) and not missing_roles
    external=manifest["external_gates"]
    for key,reason in (
        ("v4_document_completeness","V4_DOCUMENT_COMPLETENESS_BLOCK"),
        ("point6_normative_decision","POINT6_NORMATIVE_DECISION_PENDING"),
        ("point6_solver_decision","POINT6_SOLVER_DECISION_PENDING"),
        ("actual_structure_correlation","ACTUAL_STRUCTURE_CORRELATION_PENDING"),
    ):
        if external.get(key)!="PASS":reasons.append(reason)
    stable=dict(schema="ENGINEER_OS_STAGE7_REAL_CASE_V1",case_name=manifest["case_name"],files=entries,
                required_roles=sorted(REQUIRED_ROLES),missing_roles=missing_roles,
                source_identity_status="PASS" if all_sources_ok else "BLOCK",external_gates=external,
                block_reasons=sorted(set(reasons)),workflow_complete=True,
                engineering_status="BLOCK" if reasons else "READY_FOR_ENGINEERING_DECISION",
                acceptance_granted=False,final_audit="NOT_RUN",
                stage7_completion="COMPLETE_WITH_OPEN_ENGINEERING_BLOCKS" if all_sources_ok else "BLOCKED_BY_SOURCE_INTEGRITY")
    stable["case_sha256"]=stable_digest(stable)
    return stable

def main():
    ap=argparse.ArgumentParser();ap.add_argument("manifest");ap.add_argument("--out");args=ap.parse_args()
    result=run(json.loads(Path(args.manifest).read_text(encoding="utf-8")))
    text=json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True)
    if args.out:Path(args.out).write_text(text+"\n",encoding="utf-8")
    print(text)

if __name__=="__main__":main()

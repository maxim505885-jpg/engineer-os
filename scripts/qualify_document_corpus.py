"""Compare declared per-object reference payloads against immutable local sources.

This command does not render documents or qualify the independent reference.
A PASS comparison is never document completeness or engineering acceptance.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from engineering.document_intelligence.qualification import qualify_document
from engineering.local_app.analysis_identity import digest,parser_identity

MAX_JSON_BYTES=16*1024*1024
MAX_SOURCE_BYTES=256*1024*1024


def _bounded(path,limit):
    with path.open('rb') as stream:
        raw=stream.read(limit+1)
    if len(raw)>limit:raise ValueError('QUALIFICATION_JSON_SIZE_LIMIT')
    return raw


def _pairs(items):
    out={}
    for key,value in items:
        if key in out:raise ValueError('DUPLICATE_QUALIFICATION_JSON_KEY')
        out[key]=value
    return out


def _constant(value):raise ValueError('NONFINITE_QUALIFICATION_JSON')


def _json(path):
    try:
        raw=_bounded(path,MAX_JSON_BYTES)
        return json.loads(raw.decode('utf-8'),object_pairs_hook=_pairs,parse_constant=_constant),hashlib.sha256(raw).hexdigest()
    except (UnicodeError,RecursionError) as exc:raise ValueError('INVALID_QUALIFICATION_JSON') from exc


def _sha(path):
    total=0;checksum=hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''):
            total+=len(chunk)
            if total>MAX_SOURCE_BYTES:raise ValueError('QUALIFICATION_SOURCE_SIZE_LIMIT')
            checksum.update(chunk)
    return checksum.hexdigest()


def _path(value):
    path=Path(value)
    if any(p.is_symlink() or (hasattr(p,'is_junction') and p.is_junction()) for p in [path,*path.parents]):
        raise ValueError('QUALIFICATION_LINK_UNSUPPORTED')
    return path.resolve()


def compare_files(source,reference,manifest_path,observations_path,output,*,backend):
    inputs=[_path(p) for p in (source,reference,manifest_path,observations_path)]
    target=_path(output)
    if len(set(inputs))!=4 or target in inputs or target.exists():
        raise ValueError('QUALIFICATION_OUTPUT_OR_INPUT_ALIAS')
    if backend not in ('docx','pdf','ocr','docling'):
        raise ValueError('QUALIFICATION_BACKEND_UNSUPPORTED')
    source,reference,manifest_path,observations_path=inputs
    manifest,manifest_sha=_json(manifest_path);observations,observations_sha=_json(observations_path)
    before={source:_sha(source),reference:_sha(reference),manifest_path:manifest_sha,observations_path:observations_sha}
    identity=dict(source_sha256=before[source],reference_sha256=before[reference],parser_sha256=digest(parser_identity(backend)))
    if not isinstance(manifest,dict) or any(manifest.get(k)!=v for k,v in identity.items()):
        raise ValueError('QUALIFICATION_FILE_OR_PARSER_IDENTITY_MISMATCH')
    result=qualify_document(manifest,observations)
    if any(_sha(p)!=sha for p,sha in before.items()) or digest(parser_identity(backend))!=identity['parser_sha256']:
        raise ValueError('QUALIFICATION_INPUT_CHANGED_DURING_COMPARISON')
    result.update(source_files_identity_verified=True,backend=backend,
                  comparison_inputs_sha256=dict(manifest=before[manifest_path],observations=before[observations_path]))
    body=json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n'
    target.parent.mkdir(parents=True,exist_ok=True)
    with target.open('x',encoding='utf-8') as stream:stream.write(body)
    if json.loads(target.read_text(encoding='utf-8'))!=result:
        raise ValueError('QUALIFICATION_RECEIPT_READBACK_MISMATCH')
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('source','reference','manifest','observations','output'):
        parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--backend',choices=('docx','pdf','ocr','docling'),required=True)
    args=parser.parse_args()
    try:
        result=compare_files(args.source,args.reference,args.manifest,args.observations,args.output,backend=args.backend)
    except (OSError,ValueError) as exc:
        print('BLOCK: '+str(exc),file=sys.stderr);return 2
    print(json.dumps({k:result[k] for k in ('status','comparison_status','expected_objects','matched_objects','document_completeness','acceptance_granted')}))
    return 0 if result['comparison_status']=='PASS' else 2


if __name__=='__main__':raise SystemExit(main())

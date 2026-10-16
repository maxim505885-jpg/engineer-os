"""Verify a locally pinned converter bundle; no deployment or engineering gate."""
import hashlib
import json
from pathlib import Path,PurePosixPath
import re

MAX_FILES=1024
MAX_FILE_BYTES=2*1024**3
MAX_TOTAL_BYTES=4*1024**3
MAX_MANIFEST=256*1024
class BundleError(ValueError):pass

def _cancel(stop):
    if stop.is_set():raise BundleError('OFFICE_CANCELLED')

def _no_links(path):
    for item in (path,*path.parents):
        if item.is_symlink() or item.is_junction():raise BundleError('OFFICE_BUNDLE_LINK')

def _hash(path,stop,maximum=MAX_FILE_BYTES):
    _cancel(stop);_no_links(path)
    before=path.stat()
    if not path.is_file() or not 0<before.st_size<=maximum:raise BundleError('OFFICE_BUNDLE_FILE_LIMIT')
    digest=hashlib.sha256();total=0
    with path.open('rb') as stream:
        while chunk:=stream.read(1024**2):
            _cancel(stop);total+=len(chunk)
            if total>maximum:raise BundleError('OFFICE_BUNDLE_FILE_LIMIT')
            digest.update(chunk)
    after=path.stat()
    if total!=before.st_size or (before.st_size,before.st_mtime_ns,before.st_ino)!=(after.st_size,after.st_mtime_ns,after.st_ino):raise BundleError('OFFICE_BUNDLE_CHANGED')
    return digest.hexdigest()

def _unique(pairs):
    value={}
    for key,item in pairs:
        if key in value:raise BundleError('OFFICE_BUNDLE_DUPLICATE')
        value[key]=item
    return value

def _sha(value):return isinstance(value,str) and re.fullmatch('[0-9a-f]{64}',value) is not None

def verify_bundle(root,expected_manifest_sha256,*,stop):
    _cancel(stop)
    if not _sha(expected_manifest_sha256):raise BundleError('OFFICE_BUNDLE_PIN_REQUIRED')
    root=Path(root).absolute();_no_links(root);root=root.resolve()
    manifest=root/'manifest.json'
    if _hash(manifest,stop,MAX_MANIFEST)!=expected_manifest_sha256:raise BundleError('OFFICE_BUNDLE_PIN_MISMATCH')
    with manifest.open('rb') as stream:raw=stream.read(MAX_MANIFEST+1)
    if len(raw)>MAX_MANIFEST or hashlib.sha256(raw).hexdigest()!=expected_manifest_sha256:raise BundleError('OFFICE_BUNDLE_CHANGED')
    try:value=json.loads(raw,object_pairs_hook=_unique)
    except (ValueError,UnicodeError,RecursionError) as exc:raise BundleError('OFFICE_BUNDLE_JSON') from exc
    if not isinstance(value,dict) or set(value)!={'schema','files','guest_worker_sha256'} or type(value['schema']) is not int or value['schema']!=1:raise BundleError('OFFICE_BUNDLE_SCHEMA')
    if not _sha(value['guest_worker_sha256']) or value['guest_worker_sha256']!=_hash(Path(__file__).with_name('office_guest.py'),stop):raise BundleError('OFFICE_GUEST_IDENTITY_CHANGED')
    files=value['files']
    if not isinstance(files,dict) or not 3<=len(files)<=MAX_FILES:raise BundleError('OFFICE_BUNDLE_FILE_COUNT')
    required={'qemu/qemu-system-x86_64.exe','worker.qcow2','worker-seed.iso'}
    if not required.issubset(files):raise BundleError('OFFICE_BUNDLE_ROLES')
    seen=set()
    for name,digest in files.items():
        if not isinstance(name,str) or len(name)>256 or '\\' in name or ':' in name or '\0' in name or PurePosixPath(name).is_absolute() or any(p in ('','.','..') for p in name.split('/')):raise BundleError('OFFICE_BUNDLE_PATH')
        if name.casefold() in seen or not _sha(digest) or (name not in required and not name.startswith('qemu/')):raise BundleError('OFFICE_BUNDLE_PATH_OR_HASH')
        seen.add(name.casefold())
    actual=set();count=0
    for path in root.rglob('*'):
        _cancel(stop);_no_links(path);count+=1
        if count>MAX_FILES*2:raise BundleError('OFFICE_BUNDLE_TREE_LIMIT')
        if path.is_file():actual.add(path.relative_to(root).as_posix())
    if actual!=set(files)|{'manifest.json'}:raise BundleError('OFFICE_BUNDLE_FILE_SET_CHANGED')
    total=0
    for name,digest in files.items():
        path=root/name;total+=path.stat().st_size
        if total>MAX_TOTAL_BYTES:raise BundleError('OFFICE_BUNDLE_TOTAL_LIMIT')
        if _hash(path,stop)!=digest:raise BundleError('OFFICE_BUNDLE_CHANGED')
    return dict(root=root,engine=root/'qemu',image=root/'worker.qcow2',seed=root/'worker-seed.iso',
                manifest_sha256=expected_manifest_sha256,guest_worker_sha256=value['guest_worker_sha256'],
                files=dict(files),acceptance_granted=False)

"""Startup build identity and bounded artifact-integrity checks; never acceptance."""
import copy
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import threading

SCHEMA='ENGINEER_OS_BUILD_MANIFEST_V1'
ROOT=Path(__file__).resolve().parents[2]
DIRECTORIES=('engineering','scripts','agents','skills','config','schemas')
MAX_FILES=4096
MAX_FILE_BYTES=32*1024*1024
MAX_TOTAL_BYTES=128*1024*1024


def _digest(data):return hashlib.sha256(data).hexdigest()


def _source_digest(files):
    return _digest(json.dumps(files,sort_keys=True,separators=(',',':')).encode('utf-8'))


def _safe(path,root):
    for item in (path,*path.parents):
        if item==root:break
        if item.is_symlink() or item.is_junction():raise ValueError('BUILD_LINK_UNSUPPORTED')


def inventory(root):
    root=Path(root).resolve();paths=[]
    for name in DIRECTORIES:
        folder=root/name
        if not folder.exists():continue
        _safe(folder,root)
        for p in folder.rglob('*'):
            if '__pycache__' in p.parts or p.suffix in {'.pyc','.pyo'}:continue
            _safe(p,root)
            if p.is_file():
                paths.append(p)
                if len(paths)>MAX_FILES:raise ValueError('BUILD_FILE_COUNT_LIMIT')
    for p in root.iterdir():
        if p.is_file() and (p.suffix in {'.cmd','.py','.js','.html','.css'} or
                           p.name.startswith('requirements') or p.name in {'AGENTS.md','pyproject.toml'}):
            paths.append(p)
            if len(paths)>MAX_FILES:raise ValueError('BUILD_FILE_COUNT_LIMIT')
    if not 1<=len(paths)<=MAX_FILES:raise ValueError('BUILD_FILE_COUNT_LIMIT')
    result={};total=0
    for p in sorted(paths):
        _safe(p,root);stat=p.stat();total+=stat.st_size
        if stat.st_size>MAX_FILE_BYTES or total>MAX_TOTAL_BYTES:raise ValueError('BUILD_BYTES_LIMIT')
        with p.open('rb') as stream:data=stream.read(MAX_FILE_BYTES+1)
        after=p.stat()
        if len(data)!=stat.st_size or (stat.st_size,stat.st_mtime_ns,stat.st_ino)!=(after.st_size,after.st_mtime_ns,after.st_ino):
            raise ValueError('BUILD_SOURCE_CHANGED')
        result[p.relative_to(root).as_posix()]=_digest(data)
    return result


def create_manifest(root,*,version,profile,tree_sha,dirty):
    value=dict(schema=SCHEMA,version=version,profile=profile,tree_sha=tree_sha,
               dirty=dirty,schema_version=1,files=inventory(root))
    _validate(value)
    return value


def _validate(value):
    if not isinstance(value,dict) or set(value)!={'schema','version','profile','tree_sha','dirty','schema_version','files'}:
        raise ValueError('BUILD_MANIFEST_INVALID')
    if value['schema']!=SCHEMA or not isinstance(value['version'],str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9.+_-]{0,79}',value['version']):
        raise ValueError('BUILD_MANIFEST_INVALID')
    if value['profile'] not in {'native','engineering'} or type(value['dirty']) is not bool or type(value['schema_version']) is not int or value['schema_version']!=1:
        raise ValueError('BUILD_MANIFEST_INVALID')
    if not isinstance(value['tree_sha'],str) or not re.fullmatch(r'(?:[0-9a-f]{40}|[0-9a-f]{64})',value['tree_sha']):
        raise ValueError('BUILD_MANIFEST_INVALID')
    files=value['files']
    if not isinstance(files,dict) or not 1<=len(files)<=MAX_FILES:raise ValueError('BUILD_MANIFEST_INVALID')
    seen=set()
    for name,digest in files.items():
        if not isinstance(name,str) or len(name)>500 or '\\' in name or ':' in name or '\x00' in name:
            raise ValueError('BUILD_MANIFEST_INVALID')
        path=PurePosixPath(name)
        if path.is_absolute() or any(x in {'.','..',''} for x in name.split('/')) or name.casefold() in seen:
            raise ValueError('BUILD_MANIFEST_INVALID')
        seen.add(name.casefold())
        if not isinstance(digest,str) or not re.fullmatch('[0-9a-f]{64}',digest):raise ValueError('BUILD_MANIFEST_INVALID')


def _json_object(pairs):
    out={}
    for key,value in pairs:
        if key in out:raise ValueError('BUILD_MANIFEST_INVALID')
        out[key]=value
    return out


def git_identity(root):
    try:
        opts=dict(cwd=root,capture_output=True,text=True,timeout=5,check=True)
        tree=subprocess.run(['git','rev-parse','HEAD^{tree}'],**opts).stdout.strip()
        dirty=bool(subprocess.run(['git','status','--porcelain','--untracked-files=normal'],**opts).stdout.strip())
        if not re.fullmatch(r'(?:[0-9a-f]{40}|[0-9a-f]{64})',tree):raise ValueError('Git tree invalid')
        return tree,dirty
    except (OSError,subprocess.SubprocessError,ValueError):return None,None


class BuildIdentity:
    def __init__(self,root=ROOT,*,manifest_path=None,profile='native',discover_git=False):
        self.root=Path(root).resolve();self.path=Path(manifest_path) if manifest_path is not None else self.root/'build-manifest.json'
        self.lock=threading.Lock();self.files=None;self.dev_files=None;self.manifest_digest=None;self.invalidations=set()
        self.base=dict(version='development',tree_sha=None,dirty=None,profile=profile,schema_version=1,
                       manifest_sha256=None,source_sha256=None,artifact_verified=False,acceptance_granted=False,
                       scope='LOCAL_BUILD_ARTIFACT_INTEGRITY_ONLY',status='UNCERTAINTY',reasons=['BUILD_MANIFEST_MISSING'])
        if discover_git:
            self.base['tree_sha'],self.base['dirty']=git_identity(self.root)
            try:
                self.dev_files=inventory(self.root);self.base['source_sha256']=_source_digest(self.dev_files)
            except (OSError,ValueError):self.base.update(status='BLOCK',reasons=['BUILD_SOURCE_UNAVAILABLE'])
        if not self.path.exists():return
        try:
            if self.path.stat().st_size>1024*1024:raise ValueError('BUILD_MANIFEST_INVALID')
            data=self.path.read_bytes();value=json.loads(data.decode('utf-8'),object_pairs_hook=_json_object)
            _validate(value);self.files=copy.deepcopy(value['files']);self.manifest_digest=_digest(data)
            self.base.update({k:value[k] for k in ('version','tree_sha','dirty','schema_version')})
            self.base.update(manifest_sha256=self.manifest_digest,source_sha256=_source_digest(self.files),status='PASS',reasons=[])
            if profile!=value['profile']:self.base['reasons'].append('BUILD_PROFILE_MISMATCH')
            if value['dirty']:self.base['reasons'].append('BUILD_DIRTY')
        except (OSError,ValueError,UnicodeError,RecursionError):
            self.base.update(status='BLOCK',reasons=['BUILD_MANIFEST_INVALID']);self.files=None

    def report(self):
        with self.lock:
            result=copy.deepcopy(self.base)
            if self.files is not None:
                try:
                    if self.path.stat().st_size>1024*1024 or _digest(self.path.read_bytes())!=self.manifest_digest:
                        result['reasons'].append('BUILD_MANIFEST_CHANGED')
                    if inventory(self.root)!=self.files:result['reasons'].append('BUILD_SOURCE_CHANGED')
                except (OSError,ValueError):result['reasons'].append('BUILD_SOURCE_UNAVAILABLE')
                result['artifact_verified']=not result['reasons']
                result['status']='PASS' if result['artifact_verified'] else 'BLOCK'
            elif self.dev_files is not None:
                try:
                    if inventory(self.root)!=self.dev_files:
                        result['reasons'].append('BUILD_SOURCE_CHANGED');result['status']='BLOCK'
                except (OSError,ValueError):
                    result['reasons'].append('BUILD_SOURCE_UNAVAILABLE');result['status']='BLOCK'
            self.invalidations.update(r for r in result['reasons'] if r in {'BUILD_SOURCE_CHANGED','BUILD_SOURCE_UNAVAILABLE','BUILD_MANIFEST_CHANGED'})
            result['reasons']=list(dict.fromkeys(result['reasons']+sorted(self.invalidations)))
            if self.invalidations:result.update(status='BLOCK',artifact_verified=False)
            return result


def runtime_build(store):
    if not hasattr(store,'runtime_build'):
        store.runtime_build=BuildIdentity(manifest_path=os.environ.get('ENGINEER_OS_BUILD_MANIFEST'),
                                         profile=os.environ.get('ENGINEER_OS_PROFILE','native'))
    return store.runtime_build


def data_identity(root):
    return _digest(os.path.normcase(str(Path(root).resolve())).encode('utf-8'))


def runtime_report(store):
    from .store import SCHEMA_VERSION
    return dict(runtime_build(store).report(),data_root_sha256=data_identity(store.root),database_schema_version=SCHEMA_VERSION)

"""Offline, bounded, verified backups. Restore publishes only a new directory."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import sqlite3
import tempfile
import zipfile
import ctypes
from .lock import DataLock,managed_file,managed_database
from .settings import load as load_settings,validate as validate_settings

MAX_BYTES=10*1024**3
MAX_MEMBERS=100000
MAX_MANIFEST=16*1024**2
BackupError = ValueError


def _counts(db):
    names=[r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")]
    return {name:db.execute('SELECT count(*) FROM "'+name.replace('"','""')+'"').fetchone()[0] for name in names}


def _legacy_manifest(manifest):
    """Read candidate archives through the same bounded validation engine."""
    database=manifest.get('database');files=manifest.get('files')
    if not isinstance(database,dict) or database.get('archive_path')!='history.sqlite3' or not isinstance(files,list):
        raise ValueError('Invalid legacy backup manifest')
    entries={'history.sqlite3':{key:database.get(key) for key in ('size','sha256')}}
    bindings={}
    for item in files:
        if not isinstance(item,dict) or not isinstance(item.get('id'),str) or not isinstance(item.get('archive_path'),str):
            raise ValueError('Invalid legacy original entry')
        ident=item['id'];name=item['archive_path']
        if ident in bindings or name in entries:raise ValueError('Duplicate legacy original entry')
        bindings[ident]=name;entries[name]={key:item.get(key) for key in ('size','sha256')}
    counts=database.get('table_counts')
    required={'sessions','messages','files','jobs','local_evidence','analysis_receipts','analysis_contexts','extraction_pages','source_reviews','requirement_sets','domain_packets','requirement_assessments','real_case_snapshots','final_audits'}
    if not isinstance(counts,dict) or not required<=set(counts) or any(type(v) is not int or v<0 for v in counts.values()):
        raise ValueError('Invalid legacy table inventory')
    return dict(schema='ENGINEER_OS_BACKUP_V1',entries=entries,bindings=bindings,
                settings=manifest.get('non_secret_config',{}),legacy_table_counts=counts)


def _hash(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def _allowed(name):
    path=PurePosixPath(name)
    reserved={'CON','PRN','AUX','NUL',*[f'COM{i}' for i in range(1,10)],*[f'LPT{i}' for i in range(1,10)]}
    return (isinstance(name,str) and '\\' not in name and ':' not in name
            and all(p.rstrip(' .')==p and p.split('.')[0].upper() not in reserved for p in path.parts)
            and not path.is_absolute() and '..' not in path.parts
            and (name in {'history.sqlite3','engineering-verification.key'}
                 or len(path.parts)==2 and path.parts[0] in {'files','derived'}
                 and all(part not in {'','.','..'} for part in path.parts)))


def _database(path):
    managed_database(path)
    db=sqlite3.connect(path)
    try:
        if db.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise ValueError('Database integrity failed')
        if db.execute('PRAGMA user_version').fetchone()[0] not in {0,1}:raise ValueError('Unsupported database version')
        if db.execute('PRAGMA foreign_key_check').fetchone() is not None:raise ValueError('Database references are invalid')
        return db
    except BaseException:db.close();raise


def _publish_directory(source,target):
    if os.name=='nt':os.rename(source,target);return
    library=ctypes.CDLL(None,use_errno=True)
    rename=getattr(library,'renameat2',None)
    if rename is None:raise OSError('Atomic no-replace restore is unavailable on this platform')
    rename.argtypes=[ctypes.c_int,ctypes.c_char_p,ctypes.c_int,ctypes.c_char_p,ctypes.c_uint]
    rename.restype=ctypes.c_int
    if rename(-100,os.fsencode(source),-100,os.fsencode(target),1)!=0:
        code=ctypes.get_errno();raise OSError(code,os.strerror(code))


def create_backup(root,output):
    root=Path(root).resolve();output=Path(output).absolute()
    output=output.parent.resolve()/output.name
    managed_database(root/'history.sqlite3')
    if not (root/'history.sqlite3').is_file():raise ValueError('Existing application data required')
    if output.exists() or output.is_symlink() or output.is_relative_to(root):raise ValueError('Choose a new backup outside application data')
    output.parent.mkdir(parents=True,exist_ok=True)
    with DataLock(root),tempfile.TemporaryDirectory(prefix='engineer-backup-',dir=output.parent) as temporary:
        folder=Path(temporary);snapshot=folder/'history.sqlite3'
        source=sqlite3.connect((root/'history.sqlite3').as_uri()+'?mode=ro',uri=True)
        try:
            destination=sqlite3.connect(snapshot)
            try:source.backup(destination)
            finally:destination.close()
        finally:source.close()
        db=_database(snapshot)
        try:
            db.execute('PRAGMA journal_mode=DELETE')
            bindings={}
            for ident,path,sha,size in db.execute('SELECT id,path,sha256,size FROM files'):
                original=Path(path)
                managed_file(original)
                if original.is_symlink() or not original.resolve().is_relative_to(root/'files'):
                    raise ValueError('Original outside managed storage')
                relative=original.relative_to(root).as_posix()
                if not _allowed(relative) or original.stat().st_size!=size or _hash(original)!=sha:
                    raise ValueError('Original identity changed')
                bindings[ident]=relative
        finally:db.close()
        members={'history.sqlite3':snapshot}
        for directory in ('files','derived'):
            parent=root/directory
            if parent.is_symlink():raise ValueError('Linked data directory is unsupported')
            if parent.exists():
                for path in parent.iterdir():
                    managed_file(path)
                    name=path.relative_to(root).as_posix()
                    if path.is_symlink() or not path.is_file() or not _allowed(name):raise ValueError('Unexpected managed data entry')
                    members[name]=path
        key=root/'engineering-verification.key'
        managed_file(key)
        if key.exists() or key.is_symlink():
            if key.is_symlink() or key.stat().st_size!=32:raise ValueError('Invalid verification key')
            members[key.name]=key
        if len(members)>MAX_MEMBERS or sum(p.stat().st_size for p in members.values())>MAX_BYTES:
            raise ValueError('Backup exceeds supported capacity')
        manifest=dict(schema='ENGINEER_OS_BACKUP_V1',bindings=bindings,settings=load_settings(root),
                      entries={n:dict(size=p.stat().st_size,sha256=_hash(p)) for n,p in members.items()})
        encoded=json.dumps(manifest,sort_keys=True,separators=(',',':')).encode()
        if len(encoded)>MAX_MANIFEST:raise ValueError('Backup manifest too large')
        archive=folder/'backup.zip'
        with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr('manifest.json',encoded)
            for name,path in members.items():z.write(path,name)
        verify_backup(archive)
        os.chmod(archive,0o600)
        # Hard-link publication is exclusive: never replace an existing copy.
        os.link(archive,output)
        return dict(verify_backup(output),path=str(output),archive=str(output),bytes=output.stat().st_size)


def _extract(archive,folder):
    with zipfile.ZipFile(archive) as z:
        infos=z.infolist();names=[i.filename for i in infos]
        if len(names)>MAX_MEMBERS+1 or len(set(names))!=len(names) or 'manifest.json' not in names:
            raise ValueError('Invalid archive inventory')
        if z.getinfo('manifest.json').file_size>MAX_MANIFEST:raise ValueError('Manifest too large')
        manifest=json.loads(z.read('manifest.json'))
        if isinstance(manifest,dict) and manifest.get('schema')=='ENGINEER_OS_DATA_BACKUP_V1':
            manifest=_legacy_manifest(manifest)
        if not isinstance(manifest,dict) or manifest.get('schema')!='ENGINEER_OS_BACKUP_V1':raise ValueError('Unsupported backup format')
        validate_settings(manifest.get('settings',{}))
        entries=manifest.get('entries');bindings=manifest.get('bindings')
        if not isinstance(entries,dict) or not isinstance(bindings,dict) or set(names)!={'manifest.json',*entries}:
            raise ValueError('Manifest inventory mismatch')
        if 'history.sqlite3' not in entries or any(not _allowed(n) for n in entries):raise ValueError('Unsafe archive path')
        if sum(i.file_size for i in infos)>MAX_BYTES+MAX_MANIFEST:raise ValueError('Archive exceeds supported capacity')
        for name,expected in entries.items():
            info=z.getinfo(name)
            if ((info.external_attr>>16)&0o170000)==0o120000:raise ValueError('Archive links are unsupported')
            if not isinstance(expected,dict) or expected.get('size')!=info.file_size:raise ValueError('Entry size mismatch')
            target=folder/name;target.parent.mkdir(parents=True,exist_ok=True)
            with z.open(info) as source,target.open('xb') as dest:shutil.copyfileobj(source,dest,1024*1024)
            os.chmod(target,0o600)
            if _hash(target)!=expected.get('sha256'):raise ValueError('Backup checksum failed')
        db=_database(folder/'history.sqlite3')
        try:
            if 'legacy_table_counts' in manifest:
                actual=_counts(db)
                if any(actual.get(name)!=count for name,count in manifest['legacy_table_counts'].items()):
                    raise ValueError('Legacy database table counts changed')
            rows=list(db.execute('SELECT id,sha256,size FROM files'))
            if set(bindings)!={r[0] for r in rows}:raise ValueError('Original bindings mismatch')
            for ident,sha,size in rows:
                name=bindings[ident]
                if not isinstance(name,str) or not name.startswith('files/') or name not in entries:
                    raise ValueError('Original binding missing')
                if entries[name].get('sha256')!=sha or entries[name].get('size')!=size:raise ValueError('Original database identity mismatch')
            key=folder/'engineering-verification.key'
            if key.exists() and key.stat().st_size!=32:raise ValueError('Invalid verification key')
        finally:db.close()
        return manifest


def verify_backup(archive):
    try:
        with tempfile.TemporaryDirectory(prefix='engineer-verify-') as temporary:
            manifest=_extract(archive,Path(temporary))
            db=_database(Path(temporary)/'history.sqlite3')
            try:counts=_counts(db)
            finally:db.close()
            return dict(status='PASS',files=len(manifest['entries']),originals=len(manifest['bindings']),
                        table_counts=counts,database_sha256=manifest['entries']['history.sqlite3']['sha256'],
                        authority_key_preserved='engineering-verification.key' in manifest['entries'])
    except (zipfile.BadZipFile,json.JSONDecodeError,KeyError,TypeError,sqlite3.Error,OSError) as exc:
        raise ValueError('Invalid or unreadable backup') from exc


def restore_backup(archive,target):
    target=Path(target).absolute()
    target=target.parent.resolve()/target.name
    if target.exists() or target.is_symlink():raise ValueError('Restore requires a new, absent directory')
    target.parent.mkdir(parents=True,exist_ok=True)
    # Parent lock coordinates competing restores without creating the target.
    with DataLock(target.parent),tempfile.TemporaryDirectory(prefix='engineer-restore-',dir=target.parent) as temporary:
        folder=Path(temporary)/'data';folder.mkdir(mode=0o700)
        try:manifest=_extract(archive,folder)
        except (zipfile.BadZipFile,json.JSONDecodeError,KeyError,TypeError,sqlite3.Error,OSError) as exc:
            raise ValueError('Invalid or unreadable backup') from exc
        db=sqlite3.connect(folder/'history.sqlite3')
        try:
            for ident,name in manifest['bindings'].items():
                db.execute('UPDATE files SET path=? WHERE id=?',(str(target/name),ident))
            db.commit()
        finally:db.close()
        from .store import Store
        Store(folder)  # Transactional schema migration before publication.
        settings=folder/'settings.json'
        settings.write_text(json.dumps(manifest.get('settings',{}),ensure_ascii=False),encoding='utf-8')
        os.chmod(settings,0o600)
        if target.exists():raise ValueError('Restore destination appeared during validation')
        _publish_directory(folder,target)
    db=_database(target/'history.sqlite3')
    try:counts=_counts(db)
    finally:db.close()
    return dict(status='PASS',path=str(target),target=str(target),files=len(manifest['entries']),
                originals=len(manifest['bindings']),table_counts=counts,
                authority_key_preserved='engineering-verification.key' in manifest['entries'])


validate_backup = verify_backup

"""Allowlisted non-secret model settings for recovery; environment overrides."""
import json
import os
from pathlib import Path
from urllib.parse import urlsplit
from .lock import managed_file,managed_database

KEYS={'ENGINEER_OS_LOCAL_MODEL_URL','ENGINEER_OS_LOCAL_MODEL','ENGINEER_OS_LOCAL_PROVIDER','ENGINEER_OS_LOCAL_THINK','ENGINEER_OS_LOCAL_MODEL_TIMEOUT'}


def validate(value):
    if not isinstance(value,dict) or not set(value)<=KEYS:raise ValueError('Unsupported saved settings')
    if any(not isinstance(v,str) or not v.strip() or len(v)>2000 for v in value.values()):raise ValueError('Invalid saved settings')
    if 'ENGINEER_OS_LOCAL_MODEL_URL' in value:
        url=urlsplit(value['ENGINEER_OS_LOCAL_MODEL_URL'])
        if url.scheme not in {'http','https'} or not url.hostname or url.username or url.password or url.query or url.fragment:
            raise ValueError('Saved model URL must not contain credentials or query secrets')
    return value


def load(root):
    path=Path(root)/'settings.json'
    managed_file(path)
    value={}
    if path.exists():
        if path.stat().st_size>16000:raise ValueError('Saved settings too large')
        value=validate(json.loads(path.read_text(encoding='utf-8')))
    value.update({k:os.environ[k] for k in KEYS if os.environ.get(k)})
    return validate(value)


def configure(store,model,values):
    """Persist non-secret settings and replace the live configuration while idle."""
    import tempfile
    from .model import LocalModel,thinking_setting
    validate(values)
    for key,value in values.items():
        if os.environ.get(key) and os.environ[key]!=value:raise ValueError('Setting is fixed by the launch environment: '+key)
    current=load(store.root);current.update(values)
    candidate=LocalModel(current.get('ENGINEER_OS_LOCAL_MODEL_URL',model.origin),current.get('ENGINEER_OS_LOCAL_MODEL',model.model),model.key,
        provider=current.get('ENGINEER_OS_LOCAL_PROVIDER',model.provider),thinking=thinking_setting(current.get('ENGINEER_OS_LOCAL_THINK','default')),
        timeout=int(current.get('ENGINEER_OS_LOCAL_MODEL_TIMEOUT',getattr(model,'timeout',180))))
    with store.connection() as db:
        db.execute('BEGIN IMMEDIATE')
        if db.execute("SELECT 1 FROM jobs WHERE state IN ('QUEUED','RUNNING','ATTACHMENT') LIMIT 1").fetchone():raise ValueError('Wait for active tasks before changing model settings')
        path=store.root/'settings.json'
        managed_file(path)
        fd,name=tempfile.mkstemp(prefix='model-settings-',dir=store.root)
        try:
            with os.fdopen(fd,'w',encoding='utf-8') as stream:
                json.dump(current,stream,ensure_ascii=False);stream.flush();os.fsync(stream.fileno())
            os.replace(name,path)
            model.__dict__.update(candidate.__dict__)
        finally:
            if Path(name).exists():Path(name).unlink()
    return dict(origin=model.origin,model=model.model,provider=model.provider,thinking=model.thinking,timeout=model.timeout)


def active_directory(selection,fallback):
    selection=Path(selection)
    managed_file(selection)
    if not selection.exists():return Path(fallback).resolve()
    if selection.is_symlink() or selection.stat().st_size>16000:raise ValueError('Invalid active directory selection')
    value=selection.read_text(encoding='utf-8').strip()
    if not value or '\n' in value or '\r' in value or '\x00' in value or not Path(value).is_absolute():raise ValueError('Active directory must be an absolute path')
    root=Path(value).resolve()
    managed_database(root/'history.sqlite3')
    if not (root/'history.sqlite3').is_file():raise ValueError('Selected project data are unavailable; reopen recovery and select an existing project')
    return root


def activate(root,selection):
    """Select an idle, existing project without replacing either data directory."""
    import tempfile
    from .lock import DataLock
    from .store import Store
    root=Path(root)
    if not root.is_absolute() or not (root/'history.sqlite3').is_file():raise ValueError('Choose an existing absolute project data directory')
    root=root.resolve();selection=Path(selection)
    managed_database(root/'history.sqlite3');managed_file(selection)
    selection=selection.parent.resolve()/selection.name
    if selection.is_symlink() or selection.is_relative_to(root):raise ValueError('Selection must be outside project data')
    with DataLock(root):
        Store(root);load(root)
        selection.parent.mkdir(parents=True,exist_ok=True)
        fd,name=tempfile.mkstemp(prefix='active-directory-',dir=selection.parent)
        try:
            with os.fdopen(fd,'w',encoding='utf-8') as stream:stream.write(str(root)+'\n');stream.flush();os.fsync(stream.fileno())
            os.replace(name,selection)
        finally:
            if Path(name).exists():Path(name).unlink()
    return root

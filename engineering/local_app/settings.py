"""Allowlisted non-secret model settings for recovery; environment overrides."""
import json
import os
from pathlib import Path
from urllib.parse import urlsplit

KEYS={'ENGINEER_OS_LOCAL_MODEL_URL','ENGINEER_OS_LOCAL_MODEL','ENGINEER_OS_LOCAL_PROVIDER','ENGINEER_OS_LOCAL_THINK'}


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
    if path.is_symlink():raise ValueError('Linked settings are unsupported')
    value={}
    if path.exists():
        if path.stat().st_size>16000:raise ValueError('Saved settings too large')
        value=validate(json.loads(path.read_text(encoding='utf-8')))
    value.update({k:os.environ[k] for k in KEYS if os.environ.get(k)})
    return validate(value)


def active_directory(selection,fallback):
    selection=Path(selection)
    if not selection.exists():return Path(fallback).resolve()
    if selection.is_symlink() or selection.stat().st_size>16000:raise ValueError('Invalid active directory selection')
    value=selection.read_text(encoding='utf-8').strip()
    if not value or '\n' in value or '\r' in value or '\x00' in value or not Path(value).is_absolute():raise ValueError('Active directory must be an absolute path')
    root=Path(value).resolve()
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

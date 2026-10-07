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

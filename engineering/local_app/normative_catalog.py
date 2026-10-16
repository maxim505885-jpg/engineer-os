"""Inspect uploaded, source-bound rules without granting normative authority."""
from collections import defaultdict
from dataclasses import asdict
import hashlib
import json
import re
from pathlib import Path
import tempfile
from engineering.normative.catalog import load_rule_catalog, MAX_CATALOG_BYTES, MAX_SOURCE_BYTES, MAX_TOTAL_SOURCE_BYTES, _pairs, _constant
from engineering.normative.rule_registry import rule_digest


def _snapshot(store, session_id, file_id, suffixes, limit):
    file=store.get_file(file_id)
    if file['session_id']!=session_id or Path(file['name']).suffix.lower() not in suffixes:
        raise ValueError('Select a same-project catalog or complete TXT/MD source')
    with Path(file['path']).open('rb') as stream:raw=stream.read(limit+1)
    if len(raw)>limit or hashlib.sha256(raw).hexdigest()!=file['sha256']:
        raise ValueError('Catalog/source changed or exceeds size limit')
    return file,raw


def inspect_catalog(store, session_id, *, catalog_file_id, source_file_ids):
    """Flat source_path names are matched exactly, never interpreted as server paths."""
    if not isinstance(source_file_ids,list) or len(source_file_ids)>1000 or any(not isinstance(x,str) for x in source_file_ids) or len(set(source_file_ids))!=len(source_file_ids):
        raise ValueError('Unique source file IDs required')
    catalog,raw=_snapshot(store,session_id,catalog_file_id,{'.json'},MAX_CATALOG_BYTES)
    try:data=json.loads(raw.decode('utf-8'),object_pairs_hook=_pairs,parse_constant=_constant)
    except (UnicodeError,RecursionError) as exc:raise ValueError('Invalid catalog JSON') from exc
    if not isinstance(data,dict) or set(data)!={'format_version','registry_version','rules'} or not isinstance(data['rules'],list) or not 1<=len(data['rules'])<=1000:
        raise ValueError('Complete catalog required')
    available=defaultdict(list)
    for file_id in source_file_ids:
        file=store.get_file(file_id)
        if file['session_id']!=session_id or Path(file['name']).suffix.lower() not in {'.txt','.md'}:raise ValueError('Same-project TXT/MD sources required')
        available[file['name']].append(file)
    checked={};entries=[];source_rows=[];total=0
    with tempfile.TemporaryDirectory(prefix='engineer-catalog-') as directory:
        root=Path(directory)
        for entry in data['rules']:
            if not isinstance(entry,dict):raise ValueError('Complete rule required')
            name=entry.get('source_path')
            if not isinstance(name,str) or not name or len(name)>200 or any(c in name for c in '/\\:') or name in {'.','..'} or Path(name).suffix.lower() not in {'.txt','.md'}:
                raise ValueError('Application catalog source_path must be a flat TXT/MD filename')
            matches=available.get(name,[])
            if len(matches)!=1:raise ValueError('Select exactly one source named '+name)
            file=matches[0]
            if file['id'] not in checked:
                file,payload=_snapshot(store,session_id,file['id'],{'.txt','.md'},MAX_SOURCE_BYTES)
                total+=len(payload)
                if total>MAX_TOTAL_SOURCE_BYTES:raise ValueError('Catalog total source limit')
                target='source-'+str(len(checked))+Path(name).suffix.lower();(root/target).write_bytes(payload)
                checked[file['id']]=(file,target)
            entries.append(dict(entry,source_path=checked[file['id']][1]))
            source_rows.append(dict(file_id=file['id'],name=file['name'],sha256=file['sha256']))
        snapshot=dict(data,rules=entries);path=root/'catalog.json';path.write_text(json.dumps(snapshot,allow_nan=False),encoding='utf-8')
        registry=load_rule_catalog(path)
    # Reject a mutation during the inspection, not just a stale upload hash.
    _snapshot(store,session_id,catalog_file_id,{'.json'},MAX_CATALOG_BYTES)
    for file,_ in checked.values():_snapshot(store,session_id,file['id'],{'.txt','.md'},MAX_SOURCE_BYTES)
    return dict(registry_version=registry.registry_version,catalog_file_id=catalog['id'],catalog_sha256=catalog['sha256'],
        rules=[dict(rule=asdict(rule),rule_sha256=rule_digest(rule),limit_fragment=re.search(r'(?<![\w.,+\-])'+re.escape(rule.limit)+r'\s+'+re.escape(rule.limit_unit)+r'(?![\w^/])',rule.requirement).group(0),source=source) for rule,source in zip(registry.rules,source_rows)],
        scope='DECLARED_SOURCE_BOUND_RULE_ONLY',current_edition_verified=False,acceptance_granted=False)

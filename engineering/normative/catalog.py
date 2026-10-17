"""Bounded, exact-text local catalog loading; declared rules never grant acceptance.

Only complete UTF-8 TXT/MD sources are supported here. PDF/OCR text equivalence,
legal authenticity, applicability and current editions require separate review.
"""
from dataclasses import fields
from datetime import date
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
from .rule_registry import Rule, RuleRegistry
from .numeric_comparison import compare_quantity

MAX_CATALOG_BYTES=2*1024*1024
MAX_SOURCE_BYTES=50*1024*1024
MAX_TOTAL_SOURCE_BYTES=100*1024*1024
CLASSES={'PROJECT','ACTUAL','MEASURED','TESTED','CALCULATED'}

def _read(path,limit):
    with path.open('rb') as stream:
        raw=stream.read(limit+1)
    if len(raw)>limit:raise ValueError('CATALOG_SOURCE_SIZE_LIMIT')
    return raw

def _pairs(items):
    result={}
    for key,value in items:
        if key in result:raise ValueError('DUPLICATE_CATALOG_KEY')
        result[key]=value
    return result

def _constant(value):raise ValueError('NONFINITE_CATALOG_VALUE')

def _source(root,value):
    if (not isinstance(value,str) or not value or len(value)>500 or '\\' in value or ':' in value):raise ValueError('INVALID_CATALOG_SOURCE_PATH')
    relative=PurePosixPath(value)
    if relative.is_absolute() or any(p in ('','.','..') for p in value.split('/')) or relative.suffix.lower() not in ('.txt','.md'):raise ValueError('UNSUPPORTED_CATALOG_SOURCE_PATH')
    path=(root/Path(*relative.parts)).resolve(strict=True)
    if not path.is_relative_to(root) or not path.is_file():raise ValueError('CATALOG_SOURCE_OUTSIDE_ROOT')
    return path

def load_rule_catalog(path: Path) -> RuleRegistry:
    """Read a frozen snapshot; source paths cannot escape the catalog directory."""
    path=Path(path).resolve(strict=True);root=path.parent
    try:
        catalog=json.loads(_read(path,MAX_CATALOG_BYTES).decode('utf-8'),object_pairs_hook=_pairs,parse_constant=_constant)
        if not isinstance(catalog,dict) or set(catalog)!={'format_version','registry_version','rules'} or type(catalog['format_version'])!=int or catalog['format_version']!=1:raise ValueError('INVALID_CATALOG_FORMAT')
        version=catalog['registry_version'];entries=catalog['rules']
        if not isinstance(version,str) or not version.strip() or len(version)>200 or not isinstance(entries,list) or not 1<=len(entries)<=1000:raise ValueError('INVALID_CATALOG_REGISTRY')
        required={f.name for f in fields(Rule)}|{'source_path'};rules=[];seen=set();sources={};total=0
        for entry in entries:
            if not isinstance(entry,dict) or set(entry)!=required:raise ValueError('COMPLETE_CATALOG_RULE_REQUIRED')
            data={key:value for key,value in entry.items() if key!='source_path'}
            classes=data['accepted_data_classes']
            if not isinstance(classes,list) or not 1<=len(classes)<=5 or any(type(c)!=str or c not in CLASSES for c in classes) or len(set(classes))!=len(classes):raise ValueError('INVALID_CATALOG_DATA_CLASSES')
            data['accepted_data_classes']=tuple(classes)
            if any(not isinstance(v,str) or not v.strip() or len(v)>4000 for k,v in data.items() if k!='accepted_data_classes'):raise ValueError('INVALID_CATALOG_RULE_TEXT')
            rule=Rule(**data);key=(rule.rule_id,rule.rule_version)
            if key in seen:raise ValueError('DUPLICATE_RULE_VERSION')
            seen.add(key)
            if not re.fullmatch('[0-9a-f]{64}',rule.normative_source_sha256):raise ValueError('INVALID_NORMATIVE_SOURCE_HASH')
            start=date.fromisoformat(rule.effective_from);end=date.fromisoformat(rule.effective_until)
            if start.isoformat()!=rule.effective_from or end.isoformat()!=rule.effective_until or start>end:raise ValueError('INVALID_EFFECTIVE_INTERVAL')
            if compare_quantity(actual=rule.limit,actual_unit=rule.limit_unit,limit=rule.limit,limit_unit=rule.limit_unit,operator=rule.operator)['status']=='BLOCK':raise ValueError('INVALID_CATALOG_QUANTITY')
            fragment=r'(?<![\w.,+\-])'+re.escape(rule.limit)+r'\s+'+re.escape(rule.limit_unit)+r'(?![\w^/])'
            if len(re.findall(fragment,rule.requirement))!=1:raise ValueError('EXACT_RULE_QUANTITY_FRAGMENT_REQUIRED')
            source=_source(root,entry['source_path'])
            if source not in sources:
                raw=_read(source,MAX_SOURCE_BYTES);total+=len(raw)
                if total>MAX_TOTAL_SOURCE_BYTES:raise ValueError('CATALOG_TOTAL_SOURCE_LIMIT')
                sources[source]=(hashlib.sha256(raw).hexdigest(),raw.decode('utf-8'))
            sha,text=sources[source]
            if sha!=rule.normative_source_sha256:raise ValueError('CATALOG_SOURCE_HASH_CHANGED')
            if ('\x00' in text or any(part not in text for part in (rule.document,rule.edition,rule.clause,rule.source_locator)) or text.count(rule.clause_text)!=1 or rule.requirement not in rule.clause_text or rule.clause not in rule.clause_text):raise ValueError('EXACT_CATALOG_CLAUSE_TEXT_REQUIRED')
            rules.append(rule)
        return RuleRegistry(tuple(rules),version)
    except (OSError,UnicodeError,TypeError,KeyError,RecursionError) as exc:
        raise ValueError('CATALOG_INPUT_UNAVAILABLE_OR_INVALID') from exc

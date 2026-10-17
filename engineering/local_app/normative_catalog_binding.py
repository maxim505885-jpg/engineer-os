"""Bind a declared catalog snapshot to current, same-session plaintext sources."""
from dataclasses import asdict
from datetime import date
import hashlib
import json
from pathlib import Path
import tempfile
from engineering.normative.catalog import load_rule_catalog, MAX_SOURCE_BYTES
from engineering.normative.rule_registry import rule_digest
from engineering.normative.numeric_comparison import compare_quantity

CLASS_NAMES={'P':'PROJECT','F':'ACTUAL','M':'MEASURED','T':'TESTED','C':'CALCULATED'}

def validate(store,session_id,packet,candidates):
    binding=packet['catalog_rule']
    if not isinstance(binding,dict) or set(binding)!={'registry_version','rule','rule_sha256','assessment_date'} or not isinstance(binding['rule'],dict):raise ValueError('Complete catalog binding required')
    declared=binding['rule'];sha=declared.get('normative_source_sha256')
    files={}
    for eid in packet['norm_ids']:
        candidate=candidates[eid];file=store.get_file(candidate['file_id'])
        if file['session_id']!=session_id:raise ValueError('Foreign catalog source')
        if file['sha256']==sha:files[file['id']]=file
    if len(files)!=1:raise ValueError('Exact catalog source required')
    file=next(iter(files.values()))
    if Path(file['name']).suffix.lower() not in ('.txt','.md'):raise ValueError('Full plaintext catalog source required')
    with Path(file['path']).open('rb') as stream:raw=stream.read(MAX_SOURCE_BYTES+1)
    if len(raw)>MAX_SOURCE_BYTES or hashlib.sha256(raw).hexdigest()!=sha:raise ValueError('Catalog source changed or too large')
    with tempfile.TemporaryDirectory(prefix='engineer-norm-rule-') as directory:
        root=Path(directory);(root/'source.txt').write_bytes(raw)
        entry=dict(declared,source_path='source.txt')
        (root/'catalog.json').write_text(json.dumps(dict(format_version=1,registry_version=binding['registry_version'],rules=[entry]),allow_nan=False),encoding='utf-8')
        registry=load_rule_catalog(root/'catalog.json')
    rule=registry.rules[0]
    if rule_digest(rule)!=binding['rule_sha256']:raise ValueError('Catalog rule digest changed')
    day=date.fromisoformat(binding['assessment_date'])
    if day.isoformat()!=binding['assessment_date'] or not rule.effective_from<=binding['assessment_date']<=rule.effective_until:raise ValueError('Assessment outside declared rule interval')
    if any(packet['chain'][key]!=getattr(rule,key) for key in ('document','edition','scope','clause','requirement')):raise ValueError('Catalog rule and normative chain differ')
    if not any(candidates[e]['source_sha256']==sha and rule.clause_text in candidates[e]['quote'] for e in packet['norm_ids']):raise ValueError('Exact catalog clause candidate required')
    if any(CLASS_NAMES.get(candidates[e]['data_class']) not in rule.accepted_data_classes for e in packet['actual_ids']):raise ValueError('Actual class not allowed by rule')
    quantities=packet['quantities']
    if not quantities:raise ValueError('Catalog numeric comparison required')
    from .domain_packets import ALIASES
    q=quantities['limit'];unit=ALIASES.get(q['unit'],q['unit'])
    same=compare_quantity(actual=q['value'].replace(',','.'),actual_unit=unit,limit=rule.limit,limit_unit=rule.limit_unit,operator='==')
    if quantities['operator']!=rule.operator or same['status']=='BLOCK' or not same['satisfied']:raise ValueError('Catalog quantity or operator differs')
    return dict(registry_version=registry.registry_version,rule=asdict(rule),rule_sha256=binding['rule_sha256'],assessment_date=binding['assessment_date'],scope='DECLARED_SOURCE_BOUND_RULE_ONLY',current_edition_verified=False,acceptance_granted=False)

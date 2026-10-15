"""Replay recorded source judgements; no live model, solver or field acceptance.

Run from the repository: python -m scripts.replay_normative_review --manifest
private.json --source-dir ORIGINALS --output NEW_DIRECTORY
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
from engineering.local_app.store import Store
from engineering.local_app.files import preserve_file
from engineering.local_app.evidence import register
from engineering.local_app.review import record_review
from engineering.local_app.domain_packets import save,report


def replay(data,source_dir,output):
    source_dir=Path(source_dir).resolve();output=Path(output)
    originals={}
    for source in data['sources']:
        name=source['name']
        if not isinstance(name,str) or Path(name).name!=name or source['key'] in originals:
            raise ValueError('Unique source basename required')
        path=(source_dir/name).resolve()
        if path.parent!=source_dir:raise ValueError('Source outside original directory')
        content=path.read_bytes()
        if hashlib.sha256(content).hexdigest()!=source['sha256']:raise ValueError('Source identity mismatch: '+name)
        originals[source['key']]=(name,content)
    output.mkdir(parents=True,exist_ok=False)
    store=Store(output/'data');sid=store.create_session()['id']
    files={key:preserve_file(store,sid,name,content) for key,(name,content) in originals.items()}
    candidates={}
    actor='Recorded Codex source review; qualification and field truth unverified'
    for item in data['candidates']:
        if item['key'] in candidates:raise ValueError('Duplicate candidate key')
        c=register(store,sid,file_id=files[item['source']]['id'],quote=item['quote'],statement=item['statement'],page=item.get('page'),data_class=item.get('data_class','U'))
        record_review(store,sid,c['id'],expected_revision=0,decision=item['decision'],note=item['note'],actor=actor)
        candidates[item['key']]=c
    for revision,template in enumerate(data['packets']):
        packet=copy.deepcopy(template)
        packet['norm_ids']=[candidates[k]['id'] for k in packet['norm_ids']]
        packet['actual_ids']=[candidates[k]['id'] for k in packet['actual_ids']]
        if packet.get('quantities'):
            for field in ('actual','limit'):packet['quantities'][field]['candidate_id']=candidates[packet['quantities'][field]['candidate_id']]['id']
        if 'authority_source' in packet:packet['authority_source']['candidate_id']=candidates[packet['authority_source']['candidate_id']]['id']
        for item in packet.get('data_class_reviews',[]):item['candidate_id']=candidates[item['candidate_id']]['id']
        save(store,sid,packet=packet,expected_revision=revision)
    result=report(store,sid)
    reopened=report(Store(store.root),sid)
    if reopened!=result:raise RuntimeError('Persisted normative review mismatch')
    artifact=dict(scope='RECORDED_SOURCE_REVIEW_NOT_LIVE_EXPERTISE',manifest_sha256=hashlib.sha256(json.dumps(data,ensure_ascii=False,sort_keys=True).encode()).hexdigest(),session_id=sid,
                  report=result,saved_reload_equal=True,engineering_verified=False,acceptance_granted=False,final_audit='NOT_RUN',live_model='NOT_RUN',solver='NOT_RUN')
    (output/'result.json').write_text(json.dumps(artifact,ensure_ascii=False,indent=2)+'\n')
    return artifact


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest',required=True,type=Path);p.add_argument('--source-dir',required=True,type=Path);p.add_argument('--output',required=True,type=Path)
    args=p.parse_args();result=replay(json.loads(args.manifest.read_text()),args.source_dir,args.output)
    print(json.dumps(dict(packets=len(result['report']['packets']),saved_reload_equal=result['saved_reload_equal'],status=result['report']['status'],acceptance_granted=False,final_audit='NOT_RUN')))

if __name__=='__main__':main()

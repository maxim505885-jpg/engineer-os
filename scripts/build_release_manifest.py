"""Write a new code-integrity manifest; this does not qualify a release."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from engineering.local_app.build_identity import create_manifest,git_identity


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--version',required=True)
    p.add_argument('--profile',choices=('native','engineering'),default='native')
    p.add_argument('--allow-dirty',action='store_true')
    a=p.parse_args();tree,dirty=git_identity(a.root)
    if tree is None or (dirty and not a.allow_dirty):p.error('a known clean Git tree is required; --allow-dirty is development only')
    manifest=create_manifest(a.root,version=a.version,profile=a.profile,tree_sha=tree,dirty=dirty)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open('x',encoding='utf-8',newline='\n') as out:json.dump(manifest,out,sort_keys=True,indent=2)
    print(json.dumps(dict(status='MANIFEST_WRITTEN',dirty=dirty,tree_sha=tree,release_qualification='NOT_RUN')))


if __name__=='__main__':main()

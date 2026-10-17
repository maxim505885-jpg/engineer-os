"""Refuse accidental reuse of a different local build; does not attest a process."""
import argparse
import json
import os
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit
from urllib.request import Request,build_opener,HTTPRedirectHandler,ProxyHandler
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from engineering.local_app.build_identity import BuildIdentity,data_identity


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):return None


def check_running_build(origin,expected):
    result=dict(match=False,scope='LOCAL_BUILD_REUSE_CHECK_NOT_PROCESS_ATTESTATION',reasons=[])
    try:
        url=urlsplit(origin)
        if url.scheme!='http' or url.hostname!='127.0.0.1' or url.path not in {'','/'} or url.query or url.fragment or url.username or url.password or url.port is None:
            raise ValueError('Loopback origin required')
        opener=build_opener(ProxyHandler({}),NoRedirect())
        def read(path,headers=None):
            with opener.open(Request(origin.rstrip('/')+path,headers=headers or {}),timeout=5) as response:
                data=response.read(1024*1024+1)
                if len(data)>1024*1024:raise ValueError('Build response limit')
                return data
        html=read('/').decode('utf-8')
        match=re.search(r'<meta name="app-token" content="([A-Za-z0-9_-]{20,100})"',html)
        if not match:raise ValueError('Build API token unavailable')
        observed=json.loads(read('/api/build',{'X-Engineer-Token':match.group(1)}))
        fields=('source_sha256','profile','version','tree_sha','manifest_sha256')
        if 'data_root_sha256' in expected:fields+=('data_root_sha256',)
        if not isinstance(observed,dict) or not isinstance(expected.get('source_sha256'),str) or expected.get('status')=='BLOCK' or observed.get('status')=='BLOCK':
            raise ValueError('Build integrity unavailable')
        if any(observed.get(k)!=expected.get(k) for k in fields):raise ValueError('Build differs')
        if expected.get('artifact_verified') is True and observed.get('artifact_verified') is not True:
            raise ValueError('Build artifact verification missing')
        result.update(match=True,reasons=[],source_sha256=observed['source_sha256'])
    except Exception:result['reasons']=['RUNNING_BUILD_MISMATCH_OR_UNAVAILABLE']
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--app-url',required=True);a=p.parse_args()
    expected=BuildIdentity(Path(__file__).resolve().parents[1],manifest_path=os.environ.get('ENGINEER_OS_BUILD_MANIFEST'),profile=os.environ.get('ENGINEER_OS_PROFILE','native'),discover_git=True).report()
    from engineering.local_app.settings import active_directory
    root=Path(__file__).resolve().parents[1]
    expected['data_root_sha256']=data_identity(active_directory(root/'.engineer-os/active-data-dir.txt',root/'.engineer-os/local-app'))
    result=check_running_build(a.app_url,expected);print(json.dumps(result));return 0 if result['match'] else 2


if __name__=='__main__':raise SystemExit(main())

"""Download release assets with optional GitHub login; credentials remain in memory."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
import httpx
from restore_data import restore,sha256

ROOT=Path(__file__).resolve().parents[1]

def token():
    value=os.environ.get('GH_TOKEN') or os.environ.get('GITHUB_TOKEN')
    if value:return value
    if shutil.which('gh'):
        result=subprocess.run(['gh','auth','token'],capture_output=True,text=True)
        if result.returncode==0 and result.stdout.strip():return result.stdout.strip()
    if shutil.which('git'):
        result=subprocess.run(['git','-c','credential.interactive=never','credential','fill'],
            input='protocol=https\nhost=github.com\nusername=Chengsong-Fu\n\n',capture_output=True,text=True,
            env={**os.environ,'GIT_TERMINAL_PROMPT':'0','GCM_INTERACTIVE':'never'})
        values=dict(s.split('=',1) for s in result.stdout.splitlines() if '=' in s)
        if result.returncode==0 and values.get('password'):return values['password']
    return None

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scenario',choices=['sc1','sc2','sc3','sc4'])
    parser.add_argument('--download-dir',type=Path,default=ROOT/'downloads')
    parser.add_argument('--output',type=Path,default=ROOT)
    parser.add_argument('--download-only',action='store_true')
    args=parser.parse_args()
    args.download_dir.mkdir(parents=True,exist_ok=True)
    manifest=json.loads((ROOT/'metadata/archives.json').read_text(encoding='utf-8'))
    parts=[p for a in manifest['archives'] if not args.scenario or a['scenario']==args.scenario for p in a['parts']]
    base='https://api.github.com/repos/'+manifest['repository']
    headers={'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28'}
    credential=token()
    if credential:headers['Authorization']='Bearer '+credential
    with httpx.Client(headers=headers,follow_redirects=True,timeout=120) as api:
        response=api.get(base+'/releases/tags/'+manifest['tag'])
        response.raise_for_status()
        assets={p['name']:p for p in response.json()['assets']}
        for part in parts:
            target=args.download_dir/part['name']
            if target.exists():
                assert target.stat().st_size==part['size_bytes'] and sha256(target)==part['sha256'],target.name
                print('Already verified:',target.name,flush=True)
                continue
            temporary=target.with_name(target.name+'.part')
            for attempt in range(3):
                try:
                    offset=temporary.stat().st_size if temporary.exists() else 0
                    assert offset<=part['size_bytes']
                    if offset<part['size_bytes']:
                        request_headers={'Accept':'application/octet-stream'}
                        if offset:request_headers['Range']=f'bytes={offset}-'
                        with api.stream('GET',assets[part['name']]['url'],headers=request_headers) as result:
                            result.raise_for_status()
                            if result.status_code==206:
                                assert result.headers.get('content-range','').startswith(f'bytes {offset}-')
                            else:offset=0
                            with temporary.open('ab' if offset else 'wb') as stream:
                                for chunk in result.iter_bytes(1024*1024):stream.write(chunk)
                    assert temporary.stat().st_size==part['size_bytes'] and sha256(temporary)==part['sha256'],target.name
                    os.replace(temporary,target)
                    print('Downloaded and verified:',target.name,flush=True)
                    break
                except httpx.HTTPError:
                    if attempt==2:raise
                    time.sleep(2*(attempt+1))
    if not args.download_only:restore(args.download_dir,args.output,args.scenario)

if __name__=='__main__':main()

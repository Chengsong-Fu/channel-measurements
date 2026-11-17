"""Verify split ZIPs, safely restore scientific files and verify their original SHA-256."""
import argparse
import csv
import hashlib
import json
import os
from pathlib import Path,PurePosixPath
import tempfile
import zipfile

ROOT=Path(__file__).resolve().parents[1]

def sha256(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        while chunk:=stream.read(4*1024*1024):h.update(chunk)
    return h.hexdigest()

def restore(archive_dir,output,scene=None,verify_only=False):
    output=output.resolve()
    with (ROOT/'metadata/files.csv').open(encoding='utf-8-sig',newline='') as stream:
        files={r['path']:r for r in csv.DictReader(stream)}
    manifest=json.loads((ROOT/'metadata/archives.json').read_text(encoding='utf-8'))
    for archive in manifest['archives']:
        if scene and archive['scenario']!=scene:continue
        expected={name:r for name,r in files.items() if r['campaign']==archive['campaign']}
        if verify_only:
            for name,record in expected.items():
                path=output/name
                assert path.stat().st_size==int(record['size_bytes']) and sha256(path)==record['sha256'],name
            print('Verified original files:',archive['campaign'],len(expected),flush=True)
            continue
        for part in archive['parts']:
            path=archive_dir/part['name']
            assert path.stat().st_size==part['size_bytes'] and sha256(path)==part['sha256'],part['name']
        # Temporary joined ZIP is removed on success and failure; original files are never deleted.
        with tempfile.NamedTemporaryFile(prefix=archive['campaign']+'-',suffix='.zip',dir=archive_dir,delete=False) as joined:
            joined_path=Path(joined.name)
            digest=hashlib.sha256()
            for part in archive['parts']:
                with (archive_dir/part['name']).open('rb') as stream:
                    while chunk:=stream.read(4*1024*1024):
                        joined.write(chunk)
                        digest.update(chunk)
        try:
            assert joined_path.stat().st_size==archive['size_bytes'] and digest.hexdigest()==archive['sha256']
            with zipfile.ZipFile(joined_path) as source:
                infos=source.infolist()
                assert len(infos)==len(expected) and {i.filename for i in infos}==set(expected),'Archive manifest mismatch'
                for info in infos:
                    parts=PurePosixPath(info.filename)
                    assert not parts.is_absolute() and '..' not in parts.parts and '\\' not in info.filename
                    target=(output/info.filename).resolve()
                    assert target.is_relative_to(output)
                    record=expected[info.filename]
                    assert info.file_size==int(record['size_bytes'])
                    if target.exists():
                        assert target.stat().st_size==info.file_size and sha256(target)==record['sha256'],'Refusing to overwrite different file: '+info.filename
                        continue
                    target.parent.mkdir(parents=True,exist_ok=True)
                    temp=target.with_name(target.name+'.restore-part')
                    digest=hashlib.sha256()
                    with source.open(info) as src,temp.open('wb') as dst:
                        while chunk:=src.read(4*1024*1024):
                            digest.update(chunk)
                            dst.write(chunk)
                    assert digest.hexdigest()==record['sha256'],info.filename
                    os.replace(temp,target)
            print('Restored and verified:',archive['campaign'],len(expected),'files',flush=True)
        finally:
            joined_path.unlink(missing_ok=True)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive-dir',type=Path,default=ROOT/'downloads')
    parser.add_argument('--output',type=Path,default=ROOT)
    parser.add_argument('--scenario',choices=['sc1','sc2','sc3','sc4'])
    parser.add_argument('--verify-only',action='store_true')
    args=parser.parse_args()
    restore(args.archive_dir,args.output,args.scenario,args.verify_only)

if __name__=='__main__':main()

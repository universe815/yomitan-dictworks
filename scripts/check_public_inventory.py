"""Validate the unified inventory; fail closed for a requested body release."""
import argparse
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urlparse

ROOT=Path(__file__).resolve().parents[1]

def validate_release_rights(entry):
    p=entry['publication']
    if p.get('status')!='release-eligible' or p.get('redistributionApproved') is not True:
        raise ValueError(entry['id']+': redistribution is not approved; publish metadata/tools only')
    if not isinstance(p.get('license'),str) or not p['license'].strip():
        raise ValueError(entry['id']+': a concrete content license is required')
    if not isinstance(p.get('evidence'),str) or urlparse(p['evidence']).scheme!='https' or not urlparse(p['evidence']).netloc:
        raise ValueError(entry['id']+': HTTPS rights evidence is required')

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--dictionary-id')
    parser.add_argument('--archive',type=Path)
    args=parser.parse_args()
    if bool(args.dictionary_id)!=bool(args.archive):parser.error('dictionary-id and archive must be supplied together')
    data=json.loads((ROOT/'catalog/build-inventory.json').read_text(encoding='utf-8'))
    entries=data['dictionaries'];ids=set()
    assert data['editionCount']==len(entries)
    assert data['workCount']==len({e['work'] for e in entries})
    for e in entries:
        assert e['id'] not in ids;ids.add(e['id'])
        assert re.fullmatch('[a-z0-9-]+',e['id'])
        assert re.fullmatch('[a-f0-9]{64}',e['sha256'])
        assert isinstance(e['searchRecords'],int) and e['searchRecords']>0
        assert isinstance(e['bytes'],int) and e['bytes']>0
        assert Path(e['assetName']).name==e['assetName'] and '/' not in e['assetName'] and '\\' not in e['assetName']
        p=e['publication']
        assert p['status'] in {'metadata-and-tools-only','release-eligible','released'}
        if p['status']=='release-eligible':validate_release_rights(e)
        else:assert p['redistributionApproved'] is False
        if p['status']=='released':
            assert p['channel']=='github-release'
            assert isinstance(p['releaseTag'],str) and p['releaseTag']
            assert isinstance(p['releaseAssetName'],str) and p['releaseAssetName'].endswith('.zip')
    if args.dictionary_id:
        e=next((e for e in entries if e['id']==args.dictionary_id),None)
        if e is None:raise ValueError('Unknown dictionary ID')
        validate_release_rights(e)
        assert args.archive.stat().st_size==e['bytes'],'Archive size mismatch'
        assert hashlib.sha256(args.archive.read_bytes()).hexdigest()==e['sha256'],'Archive hash mismatch'
    print(f'Unified inventory valid: {data["workCount"]} works / {len(entries)} editions.')

if __name__=='__main__':main()

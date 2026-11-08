#!/usr/bin/env python3
"""Download only explicitly selected rule files; never mirror deletions."""
import hashlib
import json
import os
from pathlib import Path
import re
import sys
from datetime import datetime, timezone
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
MAX_BYTES = 2_000_000

def validate(data, spec, previous=None):
    if not data or len(data) > MAX_BYTES:
        raise ValueError('empty or oversized response')
    text = data.decode('utf-8-sig')
    rules = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith(('#', ';', '//')):
            continue
        # Intentionally fail closed: unfamiliar syntax requires human review.
        if not re.fullmatch(r'DOMAIN(?:-SUFFIX)?,[a-zA-Z0-9](?:[a-zA-Z0-9.-]*[a-zA-Z0-9])?', line):
            raise ValueError('unsupported or invalid rule: ' + line[:100])
        if any(not part or len(part) > 63 or part.startswith('-') or part.endswith('-') for part in line.split(',')[1].split('.')):
            raise ValueError('invalid domain')
        rules.append(line)
    if len(set(rules)) < spec['min_rules']:
        raise ValueError('too few distinct rules')
    if not set(spec['required_rules']).issubset(rules):
        raise ValueError('required Apple Intelligence rules missing')
    if previous:
        old_count = sum(bool(x.strip()) and not x.strip().startswith(('#', ';', '//')) for x in previous.decode('utf-8-sig').splitlines())
        if len(rules) < old_count * 0.8:
            raise ValueError('rule count dropped by more than 20%')
    return len(rules)

def download(url):
    if not url.startswith('https://raw.githubusercontent.com/'):
        raise ValueError('only explicit GitHub Raw HTTPS sources allowed')
    with urlopen(Request(url, headers={'User-Agent': 'loon-rules-backup', 'Cache-Control': 'no-cache'}), timeout=30) as response:
        if response.status != 200 or not response.url.startswith('https://raw.githubusercontent.com/'):
            raise ValueError('unexpected response or redirect')
        data = response.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES:
            raise ValueError('oversized response')
        return data

def sync_one(root, spec, fetch=download):
    path = root / spec['path']
    if Path(spec['path']).is_absolute() or '..' in Path(spec['path']).parts:
        raise ValueError('unsafe destination')
    previous = path.read_bytes() if path.exists() else None
    try:
        data = fetch(spec['url'])
        count = validate(data, spec, previous)
        if previous != data:
            tmp = path.with_name(path.name + '.tmp')
            tmp.write_bytes(data)
            os.replace(tmp, path)
        return {'state': 'updated' if previous != data else 'unchanged', 'rules': count,
                'sha256': hashlib.sha256(data).hexdigest()}
    except Exception as exc:
        # The destination is never touched before download AND validation succeed.
        return {'state': 'retained' if previous is not None else 'unavailable',
                'error': str(exc), 'sha256': hashlib.sha256(previous).hexdigest() if previous is not None else None}

def main():
    manifest = json.loads((ROOT / 'sources.json').read_text())
    report = {'checked_at': datetime.now(timezone.utc).isoformat(), 'files': {}}
    for spec in manifest['files']:
        report['files'][spec['path']] = {'source': spec['url'], **sync_one(ROOT, spec)}
    (ROOT / 'sync-status.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(report, ensure_ascii=False, indent=2))
    failed = any(x['state'] in ('retained', 'unavailable') for x in report['files'].values())
    if os.environ.get('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'], 'a') as f:
            f.write('## Loon daily sync\n\n```json\n' + json.dumps(report, ensure_ascii=False, indent=2) + '\n```\n')
    return 1 if failed else 0

if __name__ == '__main__':
    sys.exit(main())

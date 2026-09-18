#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

cd "$ROOT_DIR"

docker compose exec -T backend python - <<'PY'
from pathlib import Path
import json

papers_dir = Path('/workspace/Paper')
notes_dir = Path('/workspace/Memo')

KEYS = ['title', 'authors', 'affiliations', 'year', 'conference', 'journal', 'doi', 'abstract', 'publisher_url', 'keywords']

def score(meta: dict) -> int:
    s = 0
    if meta.get('title'):
        s += 4
    if meta.get('authors'):
        s += 3
    if meta.get('affiliations'):
        s += 2
    if meta.get('doi'):
        s += 3
    if meta.get('journal') or meta.get('conference'):
        s += 2
    if meta.get('year'):
        s += 1
    if meta.get('keywords'):
        s += 1
    return s

def is_missing(value):
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() == ''
    if isinstance(value, list):
        return len(value) == 0
    return False

updated = []
for pdf in sorted(papers_dir.glob('*.pdf')):
    stem = pdf.stem
    target_meta_path = notes_dir / f'{stem}.meta.json'

    candidates = list(notes_dir.glob(f'{stem}*.meta.json'))
    if not candidates:
        continue

    best_meta = None
    best_score = -1
    for cand in candidates:
        try:
            data = json.loads(cand.read_text(encoding='utf-8'))
        except Exception:
            continue
        sc = score(data)
        if sc > best_score:
            best_score = sc
            best_meta = data

    if best_meta is None:
        continue

    if target_meta_path.exists():
        try:
            current = json.loads(target_meta_path.read_text(encoding='utf-8'))
        except Exception:
            current = {}
    else:
        current = {}

    changed = False
    for key in KEYS:
        if is_missing(current.get(key)) and not is_missing(best_meta.get(key)):
            current[key] = best_meta.get(key)
            changed = True

    if changed:
        target_meta_path.write_text(json.dumps(current, ensure_ascii=False, indent=2), encoding='utf-8')
        updated.append(target_meta_path.name)

print(f'Updated metadata files: {len(updated)}')
for name in updated:
    print(name)
PY
